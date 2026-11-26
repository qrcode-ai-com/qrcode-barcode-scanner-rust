import type { BoundScanner } from './scan.js';

export { isFinal } from './scan.js';
export type {
  AlphaBackgroundOption, AlphaPaletteColor, BoundScanner, ScanFrameInput, ScanOptions, ScanProfile, ScannerModule,
  ScoreCheck, ScorePreset,
} from './scan.js';

/** The package ships one portable module (no SIMD) for every supported engine. */
export type ScannerVariant = 'portable';
export type ScannerInitCode = 'invalid_options' | 'wasm_unavailable' | 'wasm_features_unsupported'
  | 'loader_import_failed' | 'asset_network_failed' | 'asset_http_failed'
  | 'asset_read_failed' | 'binary_invalid' | 'wasm_validation_failed' | 'wasm_compile_failed'
  | 'wasm_instantiate_failed';
/**
 * The loaded scanner, frozen: the module's own exports (`scan_image`, `scan_frame`, `version`,
 * `capabilities`), `scan` and `scanFrame` with named options over them, and `variant`.
 */
export type LoadedScanner = typeof import('./qrcode-barcode-scanner.js') & Readonly<BoundScanner>
  & { readonly variant: ScannerVariant };
export interface ScannerLoaderOptions {
  /** 'compatible' is the pre-0.11 name of the same no-SIMD feature set; any other value is `invalid_options`. */
  variant?: 'auto' | 'portable' | 'compatible';
  wasmUrl?: string | URL;
}
export declare class ScannerInitError extends Error {
  readonly code: ScannerInitCode;
  readonly variant: ScannerVariant | null;
  /**
   * `true` for `loader_import_failed`, `asset_network_failed`, `asset_http_failed` and
   * `asset_read_failed`: the loader did not keep this failure, so calling it again starts a
   * fresh attempt. `false` for every other code, which the loader keeps.
   */
  readonly retryable: boolean;
  readonly status?: number;
  readonly cause?: unknown;
  constructor(code: ScannerInitCode, variant: ScannerVariant | null, cause?: unknown, status?: number);
}
/** `simd` is diagnostic only: the portable module does not need it. */
export declare function scannerCapabilities(): { wasm: boolean; simd: boolean; baseline: boolean };
/**
 * A loader with its own state. Concurrent calls share one Promise, and a loaded scanner is
 * kept. A rejection whose `retryable` is `false` is kept as well; a retryable one reaches
 * every caller already waiting, then the next call starts a fresh attempt. Nothing retries by
 * itself.
 */
export declare function createScannerLoader(options?: ScannerLoaderOptions): () => Promise<LoadedScanner>;
/** The package's shared loader: `createScannerLoader()` with no option. */
export declare const loadScanner: () => Promise<LoadedScanner>;
