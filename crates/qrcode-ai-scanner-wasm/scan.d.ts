// scan.d.ts · @qrcode-ai-com/qrcode-barcode-scanner-wasm/scan (0.12.1)
// Named options over the positional scan_image and scan_frame exports. Imports nothing at run
// time; the report types are the package's shared ones.
import type { ScanReport, StressAxis, Symbology } from './report-types.js';

/** Scan profiles: quality gate, upload tool, camera frame. */
export type ScanProfile = 'full' | 'fast' | 'frame';
/** A report section a host can withhold (`score.uec`, `score.iso15415`, `alpha.envelope`). */
export type ScoreCheck = 'uec' | 'iso15415' | 'alpha_envelope';
/** Named axis posture: `design` skips perspective and rotation, `capture` runs all six. */
export type ScorePreset = 'design' | 'capture';
/** The background flattened under transparent pixels; `auto` is the engine's default. */
export type AlphaBackgroundOption = 'auto' | 'white' | 'black' | 'none' | `#${string}`;
/** A color the placement envelope probes. */
export type AlphaPaletteColor = 'white' | 'black' | `#${string}`;

/**
 * The options of `scan` and `scanFrame`, all optional. An option left out reaches the engine as
 * `undefined` and keeps the engine's default. The engine validates every value and throws, with
 * its `[QRS-xxx]` code where it has one; an unknown key throws a TypeError naming it.
 */
export interface ScanOptions {
  /** `scan` defaults to `full`, `scanFrame` to `frame`. */
  profile?: ScanProfile;
  /**
   * The symbologies to read, by wire name (`['qr_code']`, `['ean13', 'code128']`). Left out or
   * empty: every symbology. An unknown name throws.
   */
  formats?: readonly Symbology[];
  /**
   * Wall-clock budget in milliseconds, replacing the profile's. `0` (a negative, `NaN` or
   * `Infinity` too) means no limit; a fraction floors to whole milliseconds; above 4294967295
   * throws `[QRS-006]`. A report the budget cut says so: `isFinal(report)` is then `false`.
   */
  budgetMs?: number;
  /**
   * When the first report is not final, scan once more with this budget and return that second
   * report as it is, final or not. `0` means no limit for the rerun. A final first report runs
   * no rerun, and so does leaving this out. Never more than two scans.
   */
  retryBudgetMs?: number;
  /** Largest accepted width or height in pixels: a whole number from 1, else `[QRS-006]`. */
  maxDimension?: number;
  /** Largest accepted pixel count: a whole number from 1, else `[QRS-006]`. */
  maxPixels?: number;
  /** Stress axes left out of the score: their cells never run and the composite renormalizes. */
  scoreSkipAxes?: readonly StressAxis[];
  /** Report sections withheld: the report carries `null` there; the score value does not move. */
  scoreSkipChecks?: readonly ScoreCheck[];
  /** Named axis posture; cannot be combined with `scoreSkipAxes`. */
  scorePreset?: ScorePreset;
  /** The background under transparent pixels (default `auto`); the result is in `report.alpha`. */
  alphaBackground?: AlphaBackgroundOption;
  /** Colors probed inside the same scan; their verdicts are in `report.alpha.envelope.palette`. */
  alphaPalette?: readonly AlphaPaletteColor[];
}

/** Raw RGBA pixels, four bytes per pixel, rows from the top. An `ImageData` fits. */
export interface ScanFrameInput {
  readonly data: Uint8Array | Uint8ClampedArray;
  readonly width: number;
  readonly height: number;
}

/**
 * The part of a loaded scanner module that `bindScanner` calls: its two positional functions.
 * The package's root module, and the object `loadScanner()` resolves to, both fit.
 */
export interface ScannerModule {
  scan_image(bytes: Uint8Array, profile?: string | null, max_dimension?: number | null, max_pixels?: number | null,
    budget_ms?: number | null, score_skip_axes?: string[] | null, score_skip_checks?: string[] | null,
    alpha_background?: string | null, alpha_palette?: string[] | null, score_preset?: string | null,
    formats?: string[] | null): ScanReport;
  scan_frame(data: Uint8Array, width: number, height: number, profile?: string | null, budget_ms?: number | null,
    max_dimension?: number | null, max_pixels?: number | null, score_skip_axes?: string[] | null,
    score_skip_checks?: string[] | null, alpha_background?: string | null, alpha_palette?: string[] | null,
    score_preset?: string | null, formats?: string[] | null): ScanReport;
}

export interface BoundScanner {
  /**
   * Scan encoded image bytes (PNG, JPEG, WebP, GIF). Returns the engine's report unchanged.
   * Anything but a `Uint8Array` or an `ArrayBuffer` throws a TypeError.
   */
  scan(bytes: Uint8Array | ArrayBuffer, options?: ScanOptions): ScanReport;
  /** Scan raw RGBA pixels, such as a canvas `ImageData`. Returns the engine's report unchanged. */
  scanFrame(frame: ScanFrameInput, options?: ScanOptions): ScanReport;
}

/**
 * `true` unless the time budget cut the scan (`report.trace.budget_exhausted === true`). A cut
 * report can miss codes, and a `null` score beside a detection then means "not judged".
 * Every report of this package's module carries the flag. A stored report written before the
 * engine reported it has none and is read as final: nothing in it says it was cut. Throws a
 * TypeError for a value that is not a report.
 */
export declare function isFinal(report: { readonly trace: { readonly budget_exhausted?: boolean | null } }): boolean;

/** `scan` and `scanFrame` over a loaded scanner module; frozen. */
export declare function bindScanner(module: ScannerModule): Readonly<BoundScanner>;
