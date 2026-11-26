//! The correction margin of a QR Code symbol, measured where the symbol
//! lies in the image (spec/04-score.md § The correction margin).
//!
//! An engine's stream is ONE sampling of the symbol, taken in the attempt
//! image that read it: a downscale, a binarization, that reader's grid. Its
//! error count mixes the modules the design really damages with the ones
//! that sampling misread, and it moves with the attempt: the same picture
//! exported at another size was read at another alignment and published
//! another margin, and a symbol only rxing's port read published none.
//!
//! The scanner samples the symbol itself, in the image it was given, at the
//! outer corners a reader measured ([`measure`]): every module read three
//! ways — at its centre, as the mean of its core, as the mean of the whole
//! cell — each binarized two ways over the symbol's own modules (the
//! midpoint of their extremes, Otsu's threshold). A sampling counts only
//! when its stream, under the format information read on the same grid,
//! error-corrects errors-only to the detection's payload, byte for byte.
//! The margin of the symbol is the widest one a sampling that counts
//! reads: what the design leaves a reader that samples it well, never more
//! than one of the scanner's own samplers verified.
//!
//! A reader's corners are themselves a measurement, a fraction of a module
//! off on designs whose finders are not plain squares, and a design drawn
//! in thin strokes reads differently a fraction of a module away. So a
//! symbol whose first sampling still shows errors is registered
//! ([`register`]): each corner moves by fractions of a module while the
//! sampled modules agree better with the codewords the symbol encodes (the
//! verified sampling, corrected), and the registered grid is sampled again.
//!
//! Bounded and deterministic: no clock, no RNG, no engine. At most
//! [`MAX_GRIDS`] grids are sampled in full per call and a registration
//! reads at most [`MAX_REGISTER_SAMPLES`] pixels; a symbol no sampling
//! verifies keeps what its reader measured.

use crate::engine::MaskedStream;
use crate::engine::locate;
use crate::engine::occurrence::Kind;
use crate::input::LumaImage;
use crate::ladder::MergedDetection;
use crate::matrix::sampler::{Homography, sample_bilinear};
use crate::report::{EcLevel, EngineKind, Point, Symbology};
use crate::rescue::{Acceptance, Rederived};
use crate::score::uec;

/// Grids sampled in full per call: the likeliest ones ([`MAX_RANKED`]
/// versions and polarities, each as read and transposed).
const MAX_GRIDS: usize = 6;

/// Versions and polarities whose format information is read, the ones whose
/// function patterns fit best ([`fit`]).
const MAX_RANKED: usize = 3;

/// The smallest share of a grid's finder and timing modules that must read
/// as drawn for its format information to be read: under one half the grid
/// fits the reversed reflectance better.
const MIN_FIT: f32 = 0.5;

/// The smallest module pitch a grid is sampled at, in pixels.
const MIN_PITCH: f32 = 1.0;

/// Pixels a registration may read ([`register`]): its corner moves stop at
/// this bound whatever the version.
const MAX_REGISTER_SAMPLES: usize = 3_000_000;

/// The corner moves of a registration, in modules, coarse to fine.
const REGISTER_STEPS: [f32; 3] = [0.25, 0.125, 0.0625];

/// The directions a registration moves a corner in: along each axis, then
/// along each diagonal (a corner off on both axes sits on a plateau of the
/// axis moves alone).
const MOVES: [(f32, f32); 8] = [
    (1.0, 0.0),
    (-1.0, 0.0),
    (0.0, 1.0),
    (0.0, -1.0),
    (1.0, 1.0),
    (-1.0, -1.0),
    (1.0, -1.0),
    (-1.0, 1.0),
];

/// How one module is read.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Sampler {
    /// The pixel under the module's centre.
    Centre,
    /// The mean of a 3 × 3 lattice over the module's central half.
    Core,
    /// The mean of a 5 × 5 lattice over four fifths of the module.
    Cell,
}

impl Sampler {
    const ALL: [Self; 3] = [Self::Centre, Self::Core, Self::Cell];

    /// The lattice offsets from the module's centre, in modules.
    fn offsets(self) -> &'static [f32] {
        match self {
            Self::Centre => &[0.0],
            Self::Core => &[-0.25, 0.0, 0.25],
            Self::Cell => &[-0.4, -0.2, 0.0, 0.2, 0.4],
        }
    }
}

/// What a grid of the symbol is sampled under.
#[derive(Debug, Clone, Copy)]
struct Reading {
    /// The grid is the transposed symbol (a mirrored one).
    mirrored: bool,
    /// A dark module is a low value (else a high one: an inverted symbol).
    dark_is_low: bool,
}

/// One candidate grid over the symbol's outer corners.
struct Grid<'a> {
    img: &'a LumaImage,
    to_image: Homography,
    /// Modules per side.
    size: usize,
    reading: Reading,
}

impl Grid<'_> {
    /// The value of module `(row, column)` of the symbol under `sampler`:
    /// the mean of its lattice, white outside the image.
    #[expect(
        clippy::cast_precision_loss,
        clippy::cast_possible_truncation,
        clippy::cast_sign_loss,
        reason = "module indices ≤ 177 and lattices ≤ 25 points are exact in f32; the mean of u8 samples is in 0..=255"
    )]
    fn value(&self, row: usize, column: usize, sampler: Sampler) -> u8 {
        let (column, row) = if self.reading.mirrored {
            (row, column)
        } else {
            (column, row)
        };
        let cells = self.size as f32;
        let offsets = sampler.offsets();
        let mut sum = 0.0f32;
        for dy in offsets {
            for dx in offsets {
                let (u, v) = (
                    (column as f32 + 0.5 + dx) / cells,
                    (row as f32 + 0.5 + dy) / cells,
                );
                // a point that projects to infinity reads as background
                sum += self
                    .to_image
                    .apply(u, v)
                    .map_or(255.0, |(x, y)| f32::from(sample_bilinear(self.img, x, y)));
            }
        }
        (sum / (offsets.len() * offsets.len()) as f32)
            .round()
            .clamp(0.0, 255.0) as u8
    }

    /// Every module's value under `sampler`, row-major.
    fn values(&self, sampler: Sampler) -> Vec<u8> {
        (0..self.size * self.size)
            .map(|i| self.value(i / self.size, i % self.size, sampler))
            .collect()
    }
}

/// The midpoint between the 2nd and 98th percentile of `values`; `None` for
/// a flat grid (the re-read's own threshold, `locate`).
fn midpoint(values: &[u8]) -> Option<u8> {
    let mut sorted = values.to_vec();
    sorted.sort_unstable();
    let lo = *sorted.get(sorted.len() / 50)?;
    let hi = *sorted.get(sorted.len().checked_sub(1 + sorted.len() / 50)?)?;
    (hi - lo >= 16).then(|| lo + (hi - lo) / 2)
}

/// The dark modules of a `size`-module grid of `values`, binarized each way:
/// below the midpoint of their extremes, and on the dark side of Otsu's
/// threshold. A flat grid has neither.
fn binarized(values: &[u8], size: usize, dark_is_low: bool) -> Vec<Vec<bool>> {
    let mut grids = Vec::with_capacity(2);
    if let Some(threshold) = midpoint(values) {
        grids.push(
            values
                .iter()
                .map(|value| (*value < threshold) == dark_is_low)
                .collect(),
        );
        // Otsu's split of the same modules (the transform's own: above its
        // threshold is white)
        let width = u32::try_from(size).unwrap_or(u32::MAX);
        let split =
            crate::transform::otsu_threshold(&LumaImage::new(values.to_vec(), width, width));
        grids.push(
            split
                .data()
                .iter()
                .map(|value| (*value == 0) == dark_is_low)
                .collect(),
        );
    }
    grids
}

/// What the image measured of a symbol: the sampled stream with the widest
/// margin among those that verify, and the format it verifies under.
#[derive(Debug, Clone)]
pub(crate) struct Measured {
    /// The data modules in placement order, still masked.
    pub(crate) stream: MaskedStream,
    /// The version of the grid.
    pub(crate) version: u8,
    /// The EC level its format information states.
    pub(crate) ec: EcLevel,
    /// The mask its format information states.
    pub(crate) mask: u8,
    /// The worst block's margin of `stream` ([`uec::compute`]).
    pub(crate) margin: f32,
}

/// What the detection already states of the symbol's format: a sampling
/// counts only under it.
#[derive(Debug, Clone, Copy, Default)]
pub(crate) struct Stated {
    /// The version an engine measured.
    pub(crate) version: Option<u8>,
    /// The EC level an engine read.
    pub(crate) ec: Option<EcLevel>,
    /// The mask an engine read.
    pub(crate) mask: Option<u8>,
}

/// Measure the symbol whose outer corners are `corners` in `img` (clockwise
/// from its top-left finder, a pixel spanning one unit: the occurrence
/// convention) and whose payload is `payload`. `None`: no sampling of any
/// grid error-corrects to that payload under `stated`.
pub(crate) fn measure(
    img: &LumaImage,
    corners: [Point; 4],
    payload: &[u8],
    stated: Stated,
) -> Option<Measured> {
    // outer corners on pixel edges → the sampler's pixel-centre coordinates
    let quad = corners.map(|p| (p.x - 0.5, p.y - 0.5));
    let to_image = Homography::unit_square_to_quad(quad)?;
    let edge = (0..4)
        .map(|i| {
            let (a, b) = (quad[i], quad[(i + 1) % 4]);
            (b.0 - a.0).hypot(b.1 - a.1)
        })
        .sum::<f32>()
        / 4.0;
    let versions = match stated.version {
        Some(version) => version..=version,
        None => 1..=40,
    };
    // the grids worth reading, best fit first: the one of the symbol puts
    // its finders and timing patterns where they are drawn
    let mut ranked: Vec<(f32, u8, bool)> = Vec::new();
    for version in versions {
        let size = usize::from(version) * 4 + 17;
        #[expect(
            clippy::cast_precision_loss,
            reason = "module counts ≤ 177 are exact in f32"
        )]
        if !(1..=40).contains(&version) || edge / (size as f32) < MIN_PITCH {
            continue;
        }
        let grid = Grid {
            img,
            to_image,
            size,
            reading: Reading {
                mirrored: false,
                dark_is_low: true,
            },
        };
        let Some(fit) = fit(&grid) else {
            continue;
        };
        // an inverted symbol reads every function module the other way
        ranked.push((fit, version, true));
        ranked.push((1.0 - fit, version, false));
    }
    // stable: equal fits keep the lower version, dark-on-light first
    ranked.sort_by(|a, b| b.0.total_cmp(&a.0));
    let mut grids_read = 0usize;
    for (fit, version, dark_is_low) in ranked.into_iter().take(MAX_RANKED) {
        if fit < MIN_FIT {
            break;
        }
        for mirrored in [false, true] {
            let grid = Grid {
                img,
                to_image,
                size: usize::from(version) * 4 + 17,
                reading: Reading {
                    mirrored,
                    dark_is_low,
                },
            };
            let formats = formats(&grid, version, stated);
            if formats.is_empty() {
                continue;
            }
            if grids_read >= MAX_GRIDS {
                return None;
            }
            grids_read += 1;
            let Some((measured, sampler, otsu)) = widest(&grid, version, &formats, payload) else {
                continue;
            };
            if measured.margin >= 1.0 {
                return Some(measured);
            }
            // errors left: register the grid on the symbol and sample it
            // again; the wider of the two verified margins stands
            let registered = crate::rescue::corrected_codewords(
                &measured.stream,
                version,
                measured.ec,
                measured.mask,
            )
            .map(|truth| {
                register(
                    &grid,
                    quad,
                    (version, measured.mask),
                    (sampler, otsu),
                    &truth,
                )
            })
            .filter(|corners| *corners != quad)
            .and_then(Homography::unit_square_to_quad)
            .and_then(|to_image| {
                let grid = Grid {
                    img,
                    to_image,
                    size: grid.size,
                    reading: grid.reading,
                };
                widest(&grid, version, &[(measured.ec, measured.mask)], payload)
            })
            .map(|(registered, ..)| registered)
            .filter(|registered| registered.margin > measured.margin);
            return Some(registered.unwrap_or(measured));
        }
    }
    None
}

/// The share of a dark-on-light grid's finder and timing modules that read
/// as ISO/IEC 18004 draws them, each as the mean of its core (a centre
/// alone misses a module drawn as a dot or a ring a fraction of a module
/// away), against the midpoint of the finders' own extremes: near 1 on the symbol's grid, near one half on
/// a grid of another version (its finders and timing lines fall elsewhere),
/// near 0 on the grid of an inverted symbol. `None` for flat finders.
#[expect(
    clippy::cast_precision_loss,
    reason = "module counts ≤ 3 × 49 + 2 × 161 are exact in f32"
)]
fn fit(grid: &Grid<'_>) -> Option<f32> {
    let size = grid.size;
    let finder_dark = |row: usize, column: usize| {
        row == 0
            || row == 6
            || column == 0
            || column == 6
            || ((2..=4).contains(&row) && (2..=4).contains(&column))
    };
    let mut modules: Vec<(u8, bool)> = Vec::with_capacity(3 * 49 + 2 * size);
    for (top, left) in [(0, 0), (0, size - 7), (size - 7, 0)] {
        for i in 0..49 {
            let (row, column) = (i / 7, i % 7);
            modules.push((
                grid.value(top + row, left + column, Sampler::Core),
                finder_dark(row, column),
            ));
        }
    }
    let finders: Vec<u8> = modules.iter().map(|(value, _)| *value).collect();
    let threshold = midpoint(&finders)?;
    for i in 8..size - 8 {
        modules.push((grid.value(6, i, Sampler::Core), i % 2 == 0));
        modules.push((grid.value(i, 6, Sampler::Core), i % 2 == 0));
    }
    let fitting = modules
        .iter()
        .filter(|(value, dark)| (*value < threshold) == *dark)
        .count();
    Some(fitting as f32 / modules.len() as f32)
}

/// The formats `(EC level, mask)` a grid's format information reads under
/// any sampler, either copy, that `stated` allows — none when the version
/// information (from version 7) does not state the grid's version.
fn formats(grid: &Grid<'_>, version: u8, stated: Stated) -> Vec<(EcLevel, u8)> {
    let mut found: Vec<(EcLevel, u8)> = Vec::new();
    for sampler in [Sampler::Centre, Sampler::Core] {
        // the function modules alone: a threshold from the finders' own
        // dark and light (the three 7 × 7 corners)
        let size = grid.size;
        let finders: Vec<u8> = [(0, 0), (0, size - 7), (size - 7, 0)]
            .into_iter()
            .flat_map(|(top, left)| {
                (0..49).map(move |i| grid.value(top + i / 7, left + i % 7, sampler))
            })
            .collect();
        let Some(threshold) = midpoint(&finders) else {
            continue;
        };
        let dark = |row: usize, column: usize| {
            (grid.value(row, column, sampler) < threshold) == grid.reading.dark_is_low
        };
        if version >= 7 && locate::version_word(size, &dark) != Some(version) {
            continue;
        }
        for format in locate::format_words(size, &dark)
            .into_iter()
            .filter_map(locate::decode_format)
        {
            let allowed = stated.ec.is_none_or(|ec| ec == format.0)
                && stated.mask.is_none_or(|mask| mask == format.1);
            if allowed && !found.contains(&format) {
                found.push(format);
            }
        }
    }
    found
}

/// The stream a grid reads under one sampler and one binarization
/// (`otsu`: Otsu's threshold, else the midpoint of the extremes). `None`
/// for a flat grid.
fn stream_of(grid: &Grid<'_>, sampler: Sampler, otsu: bool) -> Option<MaskedStream> {
    let size = grid.size;
    let values = grid.values(sampler);
    let dark = binarized(&values, size, grid.reading.dark_is_low)
        .into_iter()
        .nth(usize::from(otsu))?;
    Some(locate::masked_stream(size, &|row, column| {
        dark.get(row * size + column).copied().unwrap_or(false)
    }))
}

/// The widest verified margin of a grid under `formats`, with the sampler
/// and the binarization that read it: every sampler, each binarization, each
/// format — the first of equal margins stands.
fn widest(
    grid: &Grid<'_>,
    version: u8,
    formats: &[(EcLevel, u8)],
    payload: &[u8],
) -> Option<(Measured, Sampler, bool)> {
    let mut best: Option<(Measured, Sampler, bool)> = None;
    for sampler in Sampler::ALL {
        for otsu in [false, true] {
            let Some(stream) = stream_of(grid, sampler, otsu) else {
                continue;
            };
            for &(ec, mask) in formats {
                let verifies = matches!(
                    crate::rescue::rederive(&stream, version, ec, mask, Acceptance::Engine),
                    Rederived::Parsed { parsed, .. } if parsed.bytes == payload
                );
                if !verifies {
                    continue;
                }
                let Some(report) = uec::compute(
                    &stream.bits,
                    stream.bit_len,
                    version,
                    ec,
                    mask,
                    uec::Stream::Decoded,
                ) else {
                    continue;
                };
                if best
                    .as_ref()
                    .is_none_or(|(held, ..)| report.margin > held.margin)
                {
                    best = Some((
                        Measured {
                            stream: stream.clone(),
                            version,
                            ec,
                            mask,
                            margin: report.margin,
                        },
                        sampler,
                        otsu,
                    ));
                }
            }
        }
    }
    best
}

/// Register a grid on its symbol: starting from the corners a reader
/// measured, move one corner at a time by a fraction of a module
/// ([`REGISTER_STEPS`], coarse to fine) and keep a move when fewer sampled
/// modules then disagree with `truth`, the codewords the symbol encodes
/// ([`crate::rescue::corrected_codewords`] of the verified sampling). The
/// modules are read as that sampling read them (`sampler`, `otsu`). Returns
/// the registered corners, the given ones when no move helps. At most
/// [`MAX_REGISTER_SAMPLES`] pixels are read.
#[expect(
    clippy::cast_precision_loss,
    reason = "module counts ≤ 177 are exact in f32"
)]
fn register(
    grid: &Grid<'_>,
    quad: [(f32, f32); 4],
    (version, mask): (u8, u8),
    (sampler, otsu): (Sampler, bool),
    truth: &[u8],
) -> [(f32, f32); 4] {
    let size = grid.size;
    let per_grid = size * size * sampler.offsets().len() * sampler.offsets().len();
    let mut budget = MAX_REGISTER_SAMPLES / per_grid.max(1);
    // the misread modules of the grid over `corners`; `None`: no such grid
    let misread = |corners: [(f32, f32); 4]| -> Option<u32> {
        let moved = Grid {
            img: grid.img,
            to_image: Homography::unit_square_to_quad(corners)?,
            size,
            reading: grid.reading,
        };
        let stream = stream_of(&moved, sampler, otsu)?;
        let codewords = crate::matrix::zigzag::unmask_to_codewords(
            &stream.bits,
            stream.bit_len,
            usize::from(version),
            mask,
        )?;
        Some(
            codewords
                .iter()
                .zip(truth)
                .map(|(read, encoded)| (read ^ encoded).count_ones())
                .sum(),
        )
    };
    let mut corners = quad;
    let Some(mut errors) = misread(corners) else {
        return quad;
    };
    let edge = (0..4)
        .map(|i| {
            let (a, b) = (quad[i], quad[(i + 1) % 4]);
            (b.0 - a.0).hypot(b.1 - a.1)
        })
        .sum::<f32>()
        / 4.0;
    let pitch = edge / size as f32;
    for step in REGISTER_STEPS {
        let step = step * pitch;
        // a sweep that moves a corner earns one more, twice at most
        for _sweep in 0..3 {
            let mut moved = false;
            for corner in 0..4 {
                for (dx, dy) in MOVES.map(|(dx, dy)| (dx * step, dy * step)) {
                    if errors == 0 || budget == 0 {
                        return corners;
                    }
                    budget -= 1;
                    let mut candidate = corners;
                    candidate[corner].0 += dx;
                    candidate[corner].1 += dy;
                    if let Some(count) = misread(candidate)
                        && count < errors
                    {
                        corners = candidate;
                        errors = count;
                        moved = true;
                    }
                }
            }
            if !moved {
                break;
            }
        }
    }
    corners
}

/// The margin the image measures of a judged QR Code detection ([`measure`],
/// at the outer corners of its first occurrence a reader measured as a
/// quad), when it is wider than its engine stream's or when no engine stream
/// measures one — a symbol only the port read then states its version and
/// mask ([`MergedDetection::adopt`]). `None`: the detection keeps what its
/// reader measured. A detection the S5 rescue recovered always does (the
/// distrust signal of `uec::Stream::Rescued`); Micro QR and rMQR have no
/// margin path.
pub(crate) fn remeasure(img: &LumaImage, detection: &MergedDetection) -> Option<Measured> {
    if detection.symbology != Symbology::QrCode || detection.engines.contains(&EngineKind::Rescue) {
        return None;
    }
    let corners = detection.occurrences.iter().find_map(|footprint| {
        (footprint.kind == Kind::Quad)
            .then(|| <[Point; 4]>::try_from(footprint.points.as_slice()).ok())
            .flatten()
    })?;
    // the engine stream's own margin, under the format published beside it
    let held = match (
        &detection.masked_stream,
        detection.version,
        detection.ec,
        detection.mask,
    ) {
        (Some(stream), Some(version), Some(ec), Some(mask)) => uec::compute(
            &stream.bits,
            stream.bit_len,
            version,
            ec,
            mask,
            uec::Stream::Decoded,
        )
        .map(|report| report.margin),
        _ => None,
    };
    let stated = Stated {
        // a version and a mask are stated together with a stream
        version: detection.masked_stream.as_ref().and(detection.version),
        ec: detection.ec,
        mask: detection.masked_stream.as_ref().and(detection.mask),
    };
    measure(img, corners, &detection.raw, stated)
        .filter(|measured| held.is_none_or(|margin| measured.margin > margin))
}

impl MergedDetection {
    /// Take the stream the image measured and the format it verifies under.
    /// Nothing else of the detection changes.
    pub(crate) fn adopt(&mut self, measured: Measured) {
        self.masked_stream = Some(measured.stream);
        self.version = Some(measured.version);
        self.ec = Some(measured.ec);
        self.mask = Some(measured.mask);
    }
}

#[cfg(test)]
mod tests {
    #![allow(
        clippy::unwrap_used,
        clippy::expect_used,
        clippy::cast_precision_loss,
        clippy::float_cmp
    )]

    use super::*;
    use crate::engine::occurrence::Footprint;
    use crate::rescue::test_symbols::{codeword_colors, mirror};

    const QUIET: usize = 4;
    const PAYLOAD: &[u8] = b"https://example.com/margin";

    /// The data codewords of `PAYLOAD` as one byte segment of a `version`
    /// symbol at `ec`.
    fn data_codewords(version: i16, ec: qrcode::EcLevel) -> Vec<u8> {
        let mut bits = qrcode::bits::Bits::new(qrcode::Version::Normal(version));
        bits.push_byte_data(PAYLOAD).unwrap();
        bits.push_terminator(ec).unwrap();
        bits.into_bytes()
    }

    /// `colors` drawn at `scale` pixels per module inside a `QUIET`-module
    /// quiet zone, each dark module filling the central `ink` share of its
    /// cell (1.0: the whole cell), and the symbol's outer corners in the
    /// occurrence convention (pixel edges, clockwise from the top-left).
    fn draw(
        colors: &[qrcode::Color],
        width: usize,
        scale: usize,
        ink: f32,
    ) -> (LumaImage, [Point; 4]) {
        let side = (width + 2 * QUIET) * scale;
        let mut data = vec![255u8; side * side];
        #[expect(
            clippy::cast_possible_truncation,
            clippy::cast_sign_loss,
            reason = "a share of one cell: between 0 and half the scale"
        )]
        let inset = ((1.0 - ink) / 2.0 * scale as f32).round() as usize;
        for (i, color) in colors.iter().enumerate() {
            if *color != qrcode::Color::Dark {
                continue;
            }
            let (mx, my) = (i % width + QUIET, i / width + QUIET);
            for dy in inset..scale - inset {
                for dx in inset..scale - inset {
                    data[(my * scale + dy) * side + mx * scale + dx] = 0;
                }
            }
        }
        let (near, far) = ((QUIET * scale) as f32, ((QUIET + width) * scale) as f32);
        let corners =
            [(near, near), (far, near), (far, far), (near, far)].map(|(x, y)| Point { x, y });
        let side = u32::try_from(side).unwrap();
        (LumaImage::new(data, side, side), corners)
    }

    /// A version 3-M symbol of `PAYLOAD` (one RS block of 26 parity
    /// codewords) with the codewords at `corrupt` inverted after encoding.
    fn symbol(corrupt: &[usize]) -> (Vec<qrcode::Color>, usize) {
        codeword_colors(
            qrcode::Version::Normal(3),
            qrcode::EcLevel::M,
            &data_codewords(3, qrcode::EcLevel::M),
            corrupt,
        )
    }

    /// The errors `uec` counts in the worst block of a measured stream.
    fn errors(measured: &Measured) -> u8 {
        uec::compute(
            &measured.stream.bits,
            measured.stream.bit_len,
            measured.version,
            measured.ec,
            measured.mask,
            uec::Stream::Decoded,
        )
        .unwrap()
        .worst_block_errors
    }

    #[test]
    fn a_clean_symbol_measures_a_full_margin_at_every_raster_size() {
        let (colors, width) = symbol(&[]);
        for scale in [2, 3, 4, 5, 7, 10, 16] {
            let (img, corners) = draw(&colors, width, scale, 1.0);
            let measured = measure(&img, corners, PAYLOAD, Stated::default())
                .unwrap_or_else(|| panic!("{scale} px per module measures"));
            assert_eq!(measured.margin, 1.0, "{scale} px per module");
            assert_eq!(
                (measured.version, measured.ec),
                (3, EcLevel::M),
                "{scale} px per module"
            );
        }
    }

    #[test]
    fn corrupted_codewords_are_counted_exactly_at_every_raster_size() {
        // real damage is never read away: the sampling with the widest
        // margin still counts every codeword the symbol itself has wrong
        for corrupt in [
            vec![0],
            vec![1, 9, 20, 33],
            vec![2, 5, 8, 13, 21, 34, 44, 50, 61],
        ] {
            let (colors, width) = symbol(&corrupt);
            for scale in [3, 5, 8] {
                let (img, corners) = draw(&colors, width, scale, 1.0);
                let measured = measure(&img, corners, PAYLOAD, Stated::default()).unwrap();
                assert_eq!(
                    usize::from(errors(&measured)),
                    corrupt.len(),
                    "{} corrupted codewords at {scale} px per module",
                    corrupt.len()
                );
                let expected = 1.0 - 2.0 * corrupt.len() as f32 / 26.0;
                assert!((measured.margin - expected).abs() < 1e-6);
            }
        }
    }

    /// The margin of the grid over `corners` alone, unregistered.
    fn unregistered(img: &LumaImage, corners: [Point; 4], width: usize) -> Option<f32> {
        let quad = corners.map(|p| (p.x - 0.5, p.y - 0.5));
        let grid = Grid {
            img,
            to_image: Homography::unit_square_to_quad(quad).unwrap(),
            size: width,
            reading: Reading {
                mirrored: false,
                dark_is_low: true,
            },
        };
        let found = formats(&grid, 3, Stated::default());
        widest(&grid, 3, &found, PAYLOAD).map(|(measured, ..)| measured.margin)
    }

    #[test]
    fn a_corner_a_fraction_of_a_module_off_is_registered_on_the_symbol() {
        let (colors, width) = symbol(&[]);
        // (pixels per module, ink share, pixels the far corner is off by)
        for (scale, ink, off) in [
            (10, 0.3, 2.0),
            (10, 0.5, 7.0),
            (10, 0.5, 9.0),
            (10, 1.0, 8.0),
        ] {
            let (img, corners) = draw(&colors, width, scale, ink);
            let mut moved = corners;
            moved[2].x += off;
            moved[2].y += off;
            let alone = unregistered(&img, moved, width)
                .unwrap_or_else(|| panic!("ink {ink} off {off}: the grid alone still verifies"));
            assert!(
                alone < 1.0,
                "ink {ink} off {off}: the witness needs a grid that misreads"
            );
            let measured = measure(&img, moved, PAYLOAD, Stated::default()).unwrap();
            assert_eq!(measured.margin, 1.0, "ink {ink} off {off}: registered");
        }
    }

    #[test]
    fn a_registration_never_narrows_a_margin_or_hides_real_damage() {
        // three codewords the symbol itself has wrong, under corners off by
        // up to a third of a module: every measure counts at least three
        // errors, and never more than its unregistered grid did
        let (colors, width) = symbol(&[6, 22, 51]);
        for ink in [0.4, 0.7, 1.0] {
            let (img, corners) = draw(&colors, width, 9, ink);
            for (corner, dx, dy) in [
                (0, 2.0, -1.0),
                (1, -3.0, 2.0),
                (2, 3.0, 3.0),
                (3, -1.0, -3.0),
            ] {
                let mut moved = corners;
                moved[corner].x += dx;
                moved[corner].y += dy;
                let Some(alone) = unregistered(&img, moved, width) else {
                    continue;
                };
                let measured = measure(&img, moved, PAYLOAD, Stated::default()).unwrap();
                assert!(measured.margin >= alone, "ink {ink} corner {corner}");
                assert!(
                    errors(&measured) >= 3,
                    "ink {ink} corner {corner}: real damage read away"
                );
            }
        }
    }

    #[test]
    fn a_mirrored_symbol_measures_under_its_transposed_grid() {
        let (colors, width) = symbol(&[3, 17]);
        // left-right mirrored: its top-left finder is the image's top-right
        let (img, corners) = draw(&mirror(&colors, width), width, 5, 1.0);
        let measured = measure(
            &img,
            [corners[1], corners[0], corners[3], corners[2]],
            PAYLOAD,
            Stated::default(),
        );
        // the corners above run counter-clockwise from the symbol's own
        // top-left; a reader publishes them clockwise, and the transposed
        // grid reads either
        let clockwise = measure(&img, corners, PAYLOAD, Stated::default());
        let measured = measured.or(clockwise).expect("a mirrored symbol measures");
        assert_eq!(errors(&measured), 2);
    }

    #[test]
    fn a_light_on_dark_symbol_measures_under_reversed_reflectance() {
        let (colors, width) = symbol(&[7]);
        let (img, corners) = draw(&colors, width, 6, 1.0);
        let inverted = LumaImage::new(
            img.data().iter().map(|value| 255 - value).collect(),
            img.width(),
            img.height(),
        );
        let measured = measure(&inverted, corners, PAYLOAD, Stated::default()).unwrap();
        assert_eq!(errors(&measured), 1);
    }

    #[test]
    fn a_sampling_counts_only_under_the_stated_format_and_the_payload() {
        let (colors, width) = symbol(&[]);
        let (img, corners) = draw(&colors, width, 6, 1.0);
        let measured = measure(&img, corners, PAYLOAD, Stated::default()).unwrap();
        let stated = |version, ec, mask| Stated {
            version: Some(version),
            ec: Some(ec),
            mask: Some(mask),
        };
        assert!(
            measure(
                &img,
                corners,
                PAYLOAD,
                stated(3, measured.ec, measured.mask)
            )
            .is_some(),
            "its own format"
        );
        assert!(
            measure(
                &img,
                corners,
                PAYLOAD,
                stated(3, measured.ec, (measured.mask + 1) % 8)
            )
            .is_none(),
            "another mask"
        );
        assert!(
            measure(&img, corners, PAYLOAD, stated(3, EcLevel::H, measured.mask)).is_none(),
            "another EC level"
        );
        assert!(
            measure(
                &img,
                corners,
                PAYLOAD,
                stated(4, measured.ec, measured.mask)
            )
            .is_none(),
            "another version"
        );
        assert!(
            measure(
                &img,
                corners,
                b"https://example.com/other",
                Stated::default()
            )
            .is_none(),
            "another payload"
        );
    }

    #[test]
    fn a_flat_image_and_a_degenerate_quad_measure_nothing() {
        let flat = LumaImage::new(vec![128; 64 * 64], 64, 64);
        let square =
            [(8.0, 8.0), (56.0, 8.0), (56.0, 56.0), (8.0, 56.0)].map(|(x, y)| Point { x, y });
        assert!(measure(&flat, square, PAYLOAD, Stated::default()).is_none());
        let (colors, width) = symbol(&[]);
        let (img, corners) = draw(&colors, width, 4, 1.0);
        let line = [corners[0], corners[1], corners[1], corners[0]];
        assert!(measure(&img, line, PAYLOAD, Stated::default()).is_none());
    }

    /// A QR Code detection of `PAYLOAD` whose one occurrence is `corners`.
    fn detection(corners: [Point; 4], engines: &[EngineKind]) -> MergedDetection {
        MergedDetection {
            symbology: Symbology::QrCode,
            raw: PAYLOAD.to_vec(),
            text: String::from_utf8(PAYLOAD.to_vec()).unwrap(),
            charset: crate::report::Charset::Utf8,
            masked_stream: None,
            corners: None,
            version: None,
            ec: Some(EcLevel::M),
            mask: None,
            fnc1: false,
            photometric_inverted: false,
            engines: engines.to_vec(),
            occurrences: vec![Footprint::candidate(
                Kind::Quad,
                corners.to_vec(),
                EngineKind::Rxing,
            )],
        }
    }

    #[test]
    fn a_read_without_a_stream_gains_the_measured_one() {
        let (colors, width) = symbol(&[4, 40]);
        let (img, corners) = draw(&colors, width, 6, 1.0);
        let mut port_only = detection(corners, &[EngineKind::Rxing]);
        let measured = remeasure(&img, &port_only).expect("the port's read measures");
        port_only.adopt(measured);
        assert_eq!(port_only.version, Some(3));
        assert!(port_only.mask.is_some());
        assert!(port_only.corners.is_none(), "no geometry is invented");
        let stream = port_only.masked_stream.as_ref().unwrap();
        let report = uec::compute(
            &stream.bits,
            stream.bit_len,
            3,
            EcLevel::M,
            port_only.mask.unwrap(),
            uec::Stream::Decoded,
        )
        .unwrap();
        assert_eq!(report.worst_block_errors, 2);
    }

    #[test]
    fn an_engine_stream_stands_unless_the_image_measures_a_wider_margin() {
        let (colors, width) = symbol(&[4, 40]);
        let (img, corners) = draw(&colors, width, 6, 1.0);
        let measured = measure(&img, corners, PAYLOAD, Stated::default()).unwrap();
        // the engine's stream already reads the symbol as well as the image
        // allows: nothing to adopt
        let mut read = detection(corners, &[EngineKind::Rqrr]);
        read.masked_stream = Some(measured.stream.clone());
        read.version = Some(measured.version);
        read.mask = Some(measured.mask);
        assert!(remeasure(&img, &read).is_none());
        // an engine stream that misread three more codewords gives way
        let mut worse = measured.stream.clone();
        for byte in [10usize, 30, 50] {
            worse.bits[byte] ^= 0xFF;
        }
        let held = uec::compute(
            &worse.bits,
            worse.bit_len,
            3,
            EcLevel::M,
            measured.mask,
            uec::Stream::Decoded,
        )
        .unwrap();
        assert!(
            held.worst_block_errors > 2,
            "the witness needs a worse stream"
        );
        read.masked_stream = Some(worse);
        let adopted = remeasure(&img, &read).expect("the wider margin is adopted");
        assert_eq!(errors(&adopted), 2);
    }

    #[test]
    fn a_rescued_or_non_qr_detection_keeps_what_its_reader_measured() {
        let (colors, width) = symbol(&[]);
        let (img, corners) = draw(&colors, width, 6, 1.0);
        let rescued = detection(corners, &[EngineKind::Rescue]);
        assert!(
            remeasure(&img, &rescued).is_none(),
            "the rescue's own count stands"
        );
        let mut micro = detection(corners, &[EngineKind::Rxing]);
        micro.symbology = Symbology::MicroQrCode;
        assert!(
            remeasure(&img, &micro).is_none(),
            "Micro QR has no margin path"
        );
        let mut unmeasured = detection(corners, &[EngineKind::Rxing]);
        unmeasured.occurrences = vec![Footprint::unavailable()];
        assert!(
            remeasure(&img, &unmeasured).is_none(),
            "no quad, no measure"
        );
    }
}
