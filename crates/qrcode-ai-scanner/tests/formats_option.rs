//! The `formats` option: a scan restricted to the symbologies its host
//! handles (spec/02-profiles). No reader of another symbology runs, the
//! stages that exist for the others are not planned, and what is listed is
//! read as in an unrestricted scan.

#![allow(clippy::unwrap_used, clippy::expect_used)]

use std::collections::BTreeSet;

use qrcode_barcode_scanner::{ImageInput, ScanConfig, ScanProfile, ScanReport, Scanner, Symbology};

fn fixture_dir(folder: &str) -> std::path::PathBuf {
    std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures")
        .join(folder)
}

fn fixture(rel: &str) -> Vec<u8> {
    let path = fixture_dir("").join(rel);
    std::fs::read(&path).unwrap_or_else(|e| panic!("missing fixture {}: {e}", path.display()))
}

/// An unbudgeted scan of `profile` restricted to `formats` (empty: every
/// symbology).
fn scan(profile: ScanProfile, formats: &[Symbology], bytes: &[u8]) -> ScanReport {
    let mut config = profile.config();
    config.budget_ms = None;
    config.formats = formats.to_vec();
    Scanner::builder()
        .profile(ScanProfile::Custom(config))
        .build()
        .scan(ImageInput::encoded(bytes))
        .unwrap()
}

/// What a report read: each detection's symbology and exact bytes.
fn contents(report: &ScanReport) -> BTreeSet<(String, Vec<u8>)> {
    report
        .detections
        .iter()
        .map(|d| (d.symbology.name().to_owned(), d.content.raw.clone()))
        .collect()
}

fn stages(report: &ScanReport) -> Vec<&str> {
    report
        .trace
        .stages
        .iter()
        .map(|s| s.stage.as_str())
        .collect()
}

/// A QR Code large enough for the pyramid stage to read it downscaled.
fn qr_png(content: &str) -> Vec<u8> {
    let code = qrcode::QrCode::with_error_correction_level(content.as_bytes(), qrcode::EcLevel::Q)
        .unwrap();
    let img = code
        .render::<image::Luma<u8>>()
        .module_dimensions(28, 28)
        .build();
    let mut out = Vec::new();
    image::DynamicImage::ImageLuma8(img)
        .write_to(&mut std::io::Cursor::new(&mut out), image::ImageFormat::Png)
        .unwrap();
    out
}

#[test]
fn a_mixed_image_reads_only_the_listed_symbologies() {
    let bytes = fixture("symbology/mixed-code128-qr.png");
    let every = scan(ScanProfile::Full, &[], &bytes);
    let found: BTreeSet<&str> = every
        .detections
        .iter()
        .map(|d| d.symbology.name())
        .collect();
    assert_eq!(found, BTreeSet::from(["code128", "qr_code"]));
    assert_eq!(
        every.trace.formats, None,
        "an unrestricted scan says nothing"
    );

    for listed in [Symbology::QrCode, Symbology::Code128] {
        let report = scan(ScanProfile::Full, &[listed], &bytes);
        let expected: BTreeSet<_> = contents(&every)
            .into_iter()
            .filter(|(symbology, _)| symbology == listed.name())
            .collect();
        assert_eq!(contents(&report), expected, "{listed:?}");
        assert_eq!(report.trace.formats, Some(vec![listed]), "{listed:?}");
    }
    // the list is a set: its order and its repeats do not matter, and the
    // report states it in the order of `Symbology::ALL`
    let both = scan(
        ScanProfile::Full,
        &[Symbology::Code128, Symbology::QrCode, Symbology::Code128],
        &bytes,
    );
    assert_eq!(contents(&both), contents(&every));
    assert_eq!(
        both.trace.formats,
        Some(vec![Symbology::QrCode, Symbology::Code128])
    );
}

/// The one fixture where a restricted scan reads less: its Code 128 shares
/// its rows with an EAN-13
/// ([`a_code_beside_another_symbol_can_need_its_neighbor_listed`]).
const NEIGHBOR: (&str, &[Symbology]) = ("ean13-addon5-code128.png", &[Symbology::Code128]);

#[test]
fn a_code_beside_another_symbol_can_need_its_neighbor_listed() {
    // an unrestricted scan reads the EAN-13, sets it aside and reads again
    // around it: the Code 128 on the same rows is then alone on them. With
    // the EAN-13 reader off nothing isolates the Code 128 — the difference
    // spec/02-profiles states.
    let bytes = fixture(&format!("symbology/{}", NEIGHBOR.0));
    let every = scan(ScanProfile::Full, &[], &bytes);
    let found: BTreeSet<&str> = every
        .detections
        .iter()
        .map(|d| d.symbology.name())
        .collect();
    assert_eq!(found, BTreeSet::from(["code128", "ean13"]));
    let alone = scan(ScanProfile::Full, NEIGHBOR.1, &bytes);
    assert!(alone.detections.is_empty(), "{:?}", contents(&alone));
    let both = scan(
        ScanProfile::Full,
        &[Symbology::Ean13, Symbology::Code128],
        &bytes,
    );
    assert_eq!(contents(&both), contents(&every));
}

#[test]
fn listing_what_an_image_holds_reads_what_an_unrestricted_scan_reads() {
    let mut checked: Vec<Symbology> = Vec::new();
    let mut files: Vec<_> = std::fs::read_dir(fixture_dir("symbology"))
        .unwrap()
        .map(|entry| entry.unwrap().path())
        .filter(|path| {
            path.extension()
                .is_some_and(|ext| ext == "png" || ext == "jpg")
        })
        .collect();
    files.sort();
    for path in files {
        let name = path.file_name().unwrap().to_string_lossy().into_owned();
        // rxing breaks PDF417 codeword ties in hash order: not a fixed read
        if name.starts_with("pdf417") {
            continue;
        }
        let bytes = std::fs::read(&path).unwrap();
        let every = scan(ScanProfile::Full, &[], &bytes);
        let mut held: Vec<Symbology> = Vec::new();
        for detection in &every.detections {
            if !held.contains(&detection.symbology) {
                held.push(detection.symbology);
            }
        }
        assert!(!held.is_empty(), "{name}: the fixture reads");
        // each symbology alone, then all it holds together
        let mut lists: Vec<Vec<Symbology>> = held.iter().map(|s| vec![*s]).collect();
        lists.push(held.clone());
        for listed in lists {
            let report = scan(ScanProfile::Full, &listed, &bytes);
            let expected: BTreeSet<_> = contents(&every)
                .into_iter()
                .filter(|(symbology, _)| listed.iter().any(|s| s.name() == symbology))
                .collect();
            if (name.as_str(), listed.as_slice()) == NEIGHBOR {
                continue;
            }
            assert_eq!(
                contents(&report),
                expected,
                "{name} restricted to {listed:?}"
            );
        }
        // a symbology it does not hold: nothing of another one is read
        let absent = [Symbology::Aztec, Symbology::MaxiCode]
            .into_iter()
            .find(|s| !held.contains(s))
            .unwrap();
        let report = scan(ScanProfile::Full, &[absent], &bytes);
        assert!(
            report.detections.iter().all(|d| d.symbology == absent),
            "{name} restricted to {absent:?}: {:?}",
            contents(&report)
        );
        checked.extend(held);
    }
    // the fixtures cover the family: a symbology this build reads and no
    // fixture holds would go unwitnessed
    for symbology in [
        Symbology::QrCode,
        Symbology::MicroQrCode,
        Symbology::RectangularMicroQrCode,
        Symbology::DataMatrix,
        Symbology::Aztec,
        Symbology::MaxiCode,
        Symbology::Ean13,
        Symbology::Ean8,
        Symbology::UpcA,
        Symbology::UpcE,
        Symbology::Code128,
        Symbology::Code39,
        Symbology::Code93,
        Symbology::Codabar,
        Symbology::Itf,
        Symbology::DataBar,
        Symbology::DataBarExpanded,
        Symbology::Telepen,
    ] {
        assert!(checked.contains(&symbology), "{symbology:?} is witnessed");
    }
}

#[test]
fn the_stages_that_exist_for_unlisted_symbologies_are_not_planned() {
    let qr = qr_png("https://example.com/formats");
    // unrestricted: a pyramid read of a QR Code is completed at native
    // resolution for the symbologies the pyramid cannot hold
    let every = scan(ScanProfile::Full, &[], &qr);
    assert_eq!(stages(&every), ["pyramid", "direct"]);
    let only_qr = scan(ScanProfile::Full, &[Symbology::QrCode], &qr);
    assert_eq!(stages(&only_qr), ["pyramid"], "nothing to complete");
    assert_eq!(contents(&only_qr), contents(&every));
    assert_eq!(
        only_qr.score.as_ref().map(|s| s.value),
        every.score.as_ref().map(|s| s.value),
        "a listed symbology is judged as in an unrestricted scan"
    );

    // nothing to read: the deep stage exists for the QR family alone
    let blank = {
        let img = image::GrayImage::from_pixel(240, 240, image::Luma([255u8]));
        let mut out = Vec::new();
        image::DynamicImage::ImageLuma8(img)
            .write_to(&mut std::io::Cursor::new(&mut out), image::ImageFormat::Png)
            .unwrap();
        out
    };
    let every = scan(ScanProfile::Full, &[], &blank);
    assert!(stages(&every).contains(&"deep"), "{:?}", stages(&every));
    let qr_family = scan(ScanProfile::Full, &[Symbology::MicroQrCode], &blank);
    assert!(
        stages(&qr_family).contains(&"deep"),
        "{:?}",
        stages(&qr_family)
    );
    let linear = scan(
        ScanProfile::Full,
        &[Symbology::Ean13, Symbology::Code128],
        &blank,
    );
    assert!(!stages(&linear).contains(&"deep"), "{:?}", stages(&linear));
    assert_eq!(contents(&linear), BTreeSet::new());
    assert_eq!(
        linear.trace.formats,
        Some(vec![Symbology::Ean13, Symbology::Code128])
    );
}

#[test]
fn the_frame_and_fast_profiles_take_the_same_list() {
    let bytes = fixture("symbology/mixed-code128-qr.png");
    for profile in [ScanProfile::Frame, ScanProfile::Fast] {
        let report = scan(profile, &[Symbology::QrCode], &bytes);
        assert!(
            report
                .detections
                .iter()
                .all(|d| d.symbology == Symbology::QrCode),
            "{:?}",
            contents(&report)
        );
        assert_eq!(report.detections.len(), 1);
        assert_eq!(report.trace.formats, Some(vec![Symbology::QrCode]));
    }
}

#[test]
fn symbologies_are_listed_by_their_wire_names() {
    for symbology in Symbology::ALL {
        assert_eq!(Symbology::from_name(symbology.name()), Some(symbology));
        assert_eq!(
            serde_json::to_value(symbology).unwrap(),
            serde_json::Value::from(symbology.name()),
            "the name is the wire value"
        );
    }
    let distinct: BTreeSet<&str> = Symbology::ALL.iter().map(|s| s.name()).collect();
    assert_eq!(distinct.len(), Symbology::ALL.len());

    assert_eq!(
        ScanConfig::formats_from_names(&["qr_code", "ean13"]).unwrap(),
        vec![Symbology::QrCode, Symbology::Ean13]
    );
    assert_eq!(
        ScanConfig::formats_from_names::<&str>(&[]).unwrap(),
        Vec::<Symbology>::new()
    );
    for unknown in ["qr_kode", "ean_13", "QR_CODE", ""] {
        let err = ScanConfig::formats_from_names(&["qr_code", unknown]).unwrap_err();
        assert_eq!(err.code(), "QRS-006", "{unknown:?}");
        assert!(err.to_string().contains("formats"), "{err}");
    }
}
