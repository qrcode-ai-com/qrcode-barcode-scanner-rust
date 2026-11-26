// scan.js · @qrcode-ai-com/qrcode-barcode-scanner-wasm/scan (0.12.1)
// Named options over the positional scan_image and scan_frame exports, and the test that tells a
// final report from one the time budget cut. Plain JavaScript: it imports nothing and, when
// imported, compiles no WebAssembly, fetches nothing and touches no DOM, so it loads in any
// runtime, server rendering included. It never changes a report: scan() and scanFrame() return
// the object the engine returned, and every engine error ([QRS-xxx] and the option errors)
// reaches the caller as thrown.

// Every accepted option, in the order an error message lists them.
const OPTION_KEYS = Object.freeze(['profile', 'formats', 'budgetMs', 'retryBudgetMs', 'maxDimension',
  'maxPixels', 'scoreSkipAxes', 'scoreSkipChecks', 'scorePreset', 'alphaBackground', 'alphaPalette']);

// The class of a value, read from its tag: an array made in another realm (a frame, a worker
// message) answers like a local one, where instanceof would say no. A Node Buffer is a Uint8Array.
const classOf = (value) => Object.prototype.toString.call(value).slice(8, -1);
const describe = (value) => (value === null ? 'null'
  : typeof value === 'object' || typeof value === 'function' ? classOf(value) : typeof value);

/**
 * true unless the time budget cut the scan (`report.trace.budget_exhausted === true`): a cut
 * report can miss codes, and a `score: null` beside a detection then means "not judged".
 * A report without the flag (written before the engine reported it) carries nothing that says
 * it was cut, and is read as final.
 */
export function isFinal(report) {
  if (report === null || typeof report !== 'object') {
    throw new TypeError(`isFinal(report): the report must be the object a scan returned, not ${describe(report)}`);
  }
  const { trace } = report;
  if (trace === null || typeof trace !== 'object') {
    throw new TypeError('isFinal(report): the report has no trace; pass the whole report a scan returned');
  }
  return trace.budget_exhausted !== true;
}

// The options of one call, each read once. A key this module does not know is refused: a typo
// such as budget_ms would otherwise run an unbounded or default scan without a word.
function readOptions(options, call) {
  if (options === undefined || options === null) return {};
  if (typeof options !== 'object' || Array.isArray(options)) {
    throw new TypeError(`${call}: the options must be an object such as { profile: 'fast' }, not ${describe(options)}`);
  }
  for (const key of Object.keys(options)) {
    if (OPTION_KEYS.includes(key)) continue;
    const camel = key.replace(/_([a-z])/g, (_match, letter) => letter.toUpperCase());
    const hint = camel !== key && OPTION_KEYS.includes(camel) ? ` (did you mean ${camel}?)` : '';
    throw new TypeError(`${call}: unknown option "${key}"${hint}; the options are ${OPTION_KEYS.join(', ')}`);
  }
  const { profile, formats, budgetMs, retryBudgetMs, maxDimension, maxPixels, scoreSkipAxes, scoreSkipChecks,
    scorePreset, alphaBackground, alphaPalette } = options;
  // The engine checks every value it receives. It never sees this one unless a rerun happens,
  // so a wrong type is refused here, before the first scan.
  if (retryBudgetMs !== undefined && typeof retryBudgetMs !== 'number') {
    throw new TypeError(`${call}: retryBudgetMs must be a number of milliseconds (0 for no limit), not ${describe(retryBudgetMs)}`);
  }
  return { profile, formats, budgetMs, retryBudgetMs, maxDimension, maxPixels, scoreSkipAxes, scoreSkipChecks,
    scorePreset, alphaBackground, alphaPalette };
}

// One scan, and at most one more: when the first report is not final and the caller gave a
// retry budget, the same scan runs once with that budget and its report is returned as it is,
// final or not. Never a loop.
function scanWithRetry(run, { budgetMs, retryBudgetMs }) {
  const report = run(budgetMs);
  return retryBudgetMs === undefined || isFinal(report) ? report : run(retryBudgetMs);
}

/**
 * `{ scan, scanFrame }` over a loaded scanner module, the object that has `scan_image` and
 * `scan_frame`. Both take named options and pass them to the module in its positional order;
 * an option left out arrives as `undefined`, which keeps the engine's own default.
 */
export function bindScanner(module) {
  if (module === null || (typeof module !== 'object' && typeof module !== 'function')
    || typeof module.scan_image !== 'function' || typeof module.scan_frame !== 'function') {
    throw new TypeError('bindScanner(module): the module must be the loaded scanner, with its scan_image and scan_frame functions');
  }

  /** Scan encoded image bytes (PNG, JPEG, WebP, GIF): a Uint8Array or an ArrayBuffer. */
  function scan(bytes, options) {
    const kind = classOf(bytes);
    if (kind !== 'Uint8Array' && kind !== 'ArrayBuffer') {
      throw new TypeError(`scan(bytes): the bytes must be a Uint8Array or an ArrayBuffer, not ${describe(bytes)}`);
    }
    const input = kind === 'ArrayBuffer' ? new Uint8Array(bytes) : bytes;
    const o = readOptions(options, 'scan(bytes, options)');
    return scanWithRetry((budgetMs) => module.scan_image(input, o.profile, o.maxDimension, o.maxPixels, budgetMs,
      o.scoreSkipAxes, o.scoreSkipChecks, o.alphaBackground, o.alphaPalette, o.scorePreset, o.formats), o);
  }

  /** Scan raw RGBA pixels: `{ data, width, height }`, which an ImageData is. */
  function scanFrame(frame, options) {
    if (frame === null || typeof frame !== 'object') {
      throw new TypeError(`scanFrame(frame): the frame must be { data, width, height }, as an ImageData is, not ${describe(frame)}`);
    }
    const { data, width, height } = frame;
    const kind = classOf(data);
    if (kind !== 'Uint8Array' && kind !== 'Uint8ClampedArray') {
      throw new TypeError(`scanFrame(frame): frame.data must be a Uint8Array or a Uint8ClampedArray of RGBA bytes, not ${describe(data)}`);
    }
    // The same bytes under the type the module declares: a view, never a copy.
    const rgba = kind === 'Uint8Array' ? data : new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
    const o = readOptions(options, 'scanFrame(frame, options)');
    return scanWithRetry((budgetMs) => module.scan_frame(rgba, width, height, o.profile, budgetMs, o.maxDimension,
      o.maxPixels, o.scoreSkipAxes, o.scoreSkipChecks, o.alphaBackground, o.alphaPalette, o.scorePreset, o.formats), o);
  }

  return Object.freeze({ scan, scanFrame });
}
