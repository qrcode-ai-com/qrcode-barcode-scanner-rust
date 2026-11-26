// node.js · @qrcode-ai-com/qrcode-barcode-scanner-wasm/node (0.12.1)
// The same scanner in Node (18 or later): the loader reads the package's own WASM from disk,
// beside this module, where ./auto fetches it. Nothing is read, compiled or requested when this
// module is imported; the file is read when a loader is first called. The scanner it resolves to
// has the shape ./auto's has: the module's exports, scan and scanFrame, and variant.
import { readFile } from 'node:fs/promises';
import { ScannerInitError, scannerCapabilities } from './auto.js';
import { bindScanner, isFinal } from './scan.js';

export { ScannerInitError, isFinal };

/** A loader with its own state, under ./auto's rule: concurrent callers share one Promise, a
 * loaded scanner is kept, and so is a failure a second attempt cannot change. A failed read
 * of the file (`asset_read_failed`, `error.retryable`) is not kept: the next call reads again.
 * `wasmPath` replaces the package's own file: a path, as node:fs reads one, or a file: URL, of
 * the same package version. */
export function createScannerLoader({ wasmPath } = {}) {
  const attempt = async () => {
    const selected = 'portable';
    if (wasmPath !== undefined && typeof wasmPath !== 'string'
      && !(wasmPath instanceof URL && wasmPath.protocol === 'file:')) {
      throw new ScannerInitError('invalid_options', null);
    }
    const capabilities = scannerCapabilities();
    if (!capabilities.wasm) throw new ScannerInitError('wasm_unavailable', selected);
    if (!capabilities.baseline) throw new ScannerInitError('wasm_features_unsupported', selected);
    let mod;
    try { mod = await import('./qrcode-barcode-scanner.js'); }
    catch (cause) { throw new ScannerInitError('loader_import_failed', selected, cause); }
    let bytes;
    try { bytes = await readFile(wasmPath ?? new URL('./qrcode-barcode-scanner_bg.wasm', import.meta.url)); }
    catch (cause) { throw new ScannerInitError('asset_read_failed', selected, cause); }
    let module;
    try { module = await WebAssembly.compile(bytes); }
    catch (cause) {
      // The codes ./auto gives the same bytes; the native exception stays the cause.
      const validHeader = bytes.length >= 8 && [0, 97, 115, 109, 1, 0, 0, 0].every((byte, index) => bytes[index] === byte);
      const code = !validHeader ? 'binary_invalid'
        : WebAssembly.validate(bytes) ? 'wasm_compile_failed' : 'wasm_validation_failed';
      throw new ScannerInitError(code, selected, cause);
    }
    // The generated module's own initialization, given the compiled module: no fetch.
    try { await mod.default({ module_or_path: module }); }
    catch (cause) { throw new ScannerInitError('wasm_instantiate_failed', selected, cause); }
    return Object.freeze({ ...mod, ...bindScanner(mod), variant: selected });
  };
  let pending;
  return () => {
    if (pending === undefined) {
      pending = (async () => {
        try { return await attempt(); }
        catch (error) {
          // attempt() is async, so this runs after `pending` holds this very Promise.
          if (error instanceof ScannerInitError && error.retryable) pending = undefined;
          throw error;
        }
      })();
    }
    return pending;
  };
}

/** The package's shared Node loader: one Promise, one read of the file, one instance. */
export const loadScanner = createScannerLoader();
