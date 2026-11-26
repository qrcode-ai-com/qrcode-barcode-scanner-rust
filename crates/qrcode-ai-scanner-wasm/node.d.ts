// node.d.ts · @qrcode-ai-com/qrcode-barcode-scanner-wasm/node (0.12.1)
// Node only (18 or later). Run-time imports: node:fs/promises, ./auto.js, ./scan.js and, when a
// loader is first called, the package's module. Importing reads no file and compiles nothing.
import type { LoadedScanner } from './auto.js';

export { ScannerInitError } from './auto.js';
export { isFinal } from './scan.js';
export type { LoadedScanner, ScannerInitCode, ScannerVariant } from './auto.js';
export type {
  AlphaBackgroundOption, AlphaPaletteColor, BoundScanner, ScanFrameInput, ScanOptions, ScanProfile, ScannerModule,
  ScoreCheck, ScorePreset,
} from './scan.js';

export interface NodeScannerLoaderOptions {
  /**
   * The WASM file to read in place of the package's own: a path or a `file:` URL. Keep it on the
   * same exact package version. Any other value rejects with `invalid_options`.
   */
  wasmPath?: string | URL;
}

/**
 * A loader with its own state. It reads the WASM file from disk, compiles it and initializes the
 * package's module, under the rule and with the codes of `/auto`: concurrent calls share one
 * Promise, and a loaded scanner is kept. A failed read is `asset_read_failed`, whose `retryable`
 * is `true`: that failure is not kept and the next call reads again. A rejection whose
 * `retryable` is `false` is kept.
 */
export declare function createScannerLoader(options?: NodeScannerLoaderOptions): () => Promise<LoadedScanner>;
/** The package's shared Node loader: `createScannerLoader()` with no option. */
export declare const loadScanner: () => Promise<LoadedScanner>;
