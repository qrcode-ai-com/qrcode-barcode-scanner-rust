// scan.test.mjs: S1-S24, the named-options surface of the BUILT pkg/ (run scripts/build-wasm.sh
// first; Node >= 22). scan.js (bindScanner, isFinal) on fake modules that record their arguments,
// the ./auto loader's retry rule under a fake fetch, and the ./node entry on the real module.
// Node only, never shipped. QRSCAN_SCAN_PACKAGE selects another package folder (default: ./pkg).
// Expected values are written out by hand, never computed by the implementation. No assertion
// reads a clock: a scan whose result is asserted runs unbudgeted (budgetMs 0), or its rerun does.
// No request leaves this machine: the loader cases replace the global fetch with a fake.
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { runInNewContext } from 'node:vm';
import { inflateSync } from 'node:zlib';

const PACKAGE = process.env.QRSCAN_SCAN_PACKAGE
  ? pathToFileURL(resolve(process.env.QRSCAN_SCAN_PACKAGE) + '/') : new URL('./pkg/', import.meta.url);
const packaged = (file) => new URL(file, PACKAGE);
const { bindScanner, isFinal } = await import(packaged('scan.js').href);
const auto = await import(packaged('auto.js').href);
const node = await import(packaged('node.js').href);
const { createScannerLoader, ScannerInitError } = auto;

const pkg = JSON.parse(readFileSync(packaged('package.json'), 'utf8'));
const WASM_URL = packaged('qrcode-barcode-scanner_bg.wasm');
const wasmBytes = readFileSync(WASM_URL);
const fixture = (rel) => new Uint8Array(readFileSync(new URL(`../../fixtures/${rel}`, import.meta.url)));
const texts = (report) => report.detections.map((d) => d.content.text);
const codes = (report) => report.detections.map((d) => [d.symbology, d.content.text]).sort();
const attempts = (report) => report.trace.stages.reduce((n, stage) => n + stage.transforms_tried, 0);
// A report without its wall-clock fields: everything else of an unbudgeted scan is deterministic.
const untimed = (value) => (Array.isArray(value) ? value.map(untimed)
  : value !== null && typeof value === 'object'
    ? Object.fromEntries(Object.entries(value).filter(([key]) => key !== 'ms' && key !== 'total_ms')
      .map(([key, child]) => [key, untimed(child)]))
    : value);
const scratch = [];
const scratchDir = (label) => {
  const dir = mkdtempSync(join(tmpdir(), `qrscan-${label}-`));
  scratch.push(dir);
  return dir;
};
test.after(() => { for (const dir of scratch) rmSync(dir, { recursive: true, force: true }); });

// ---- Fake modules -------------------------------------------------------------------------

const FINAL = () => ({ detections: [], score: null, hints: [], trace: { stages: [], budget_exhausted: false } });
const CUT = () => ({ detections: [], score: null, hints: [], trace: { stages: [], budget_exhausted: true } });
// A module whose two functions record every argument they receive and answer from `replies`, a
// list of reports (returned) and Errors (thrown); the last one answers every later call.
function recorder(...replies) {
  const calls = [];
  const answer = (name) => (...args) => {
    calls.push([name, args]);
    const reply = replies[Math.min(calls.length, replies.length) - 1] ?? FINAL();
    if (reply instanceof Error) throw reply;
    return reply;
  };
  return { calls, module: { scan_image: answer('scan_image'), scan_frame: answer('scan_frame') } };
}
const BYTES = new Uint8Array([137, 80, 78, 71]);
const FRAME = { data: new Uint8Array(16), width: 2, height: 2 };
// One distinct value per option, so a value in the wrong position cannot pass.
const EVERY = { profile: 'fast', formats: ['qr_code', 'ean13'], budgetMs: 250, maxDimension: 2048, maxPixels: 4000000,
  scoreSkipAxes: ['perspective'], scoreSkipChecks: ['uec'], scorePreset: 'capture', alphaBackground: '#f3f4f6',
  alphaPalette: ['white', '#000000'] };
// The index of each option among the arguments of the two functions, written from their
// signatures: scan_image(bytes, profile, max_dimension, max_pixels, budget_ms, score_skip_axes,
// score_skip_checks, alpha_background, alpha_palette, score_preset, formats) and
// scan_frame(data, width, height, profile, budget_ms, max_dimension, max_pixels,
// score_skip_axes, score_skip_checks, alpha_background, alpha_palette, score_preset, formats).
const IMAGE_INDEX = { profile: 1, maxDimension: 2, maxPixels: 3, budgetMs: 4, scoreSkipAxes: 5, scoreSkipChecks: 6,
  alphaBackground: 7, alphaPalette: 8, scorePreset: 9, formats: 10 };
const FRAME_INDEX = { profile: 3, budgetMs: 4, maxDimension: 5, maxPixels: 6, scoreSkipAxes: 7, scoreSkipChecks: 8,
  alphaBackground: 9, alphaPalette: 10, scorePreset: 11, formats: 12 };
const OPTION_LIST = 'profile, formats, budgetMs, retryBudgetMs, maxDimension, maxPixels, scoreSkipAxes, '
  + 'scoreSkipChecks, scorePreset, alphaBackground, alphaPalette';

test('S1 scan() passes every option to scan_image in its positional order', () => {
  const { calls, module } = recorder();
  bindScanner(module).scan(BYTES, EVERY);
  assert.deepEqual(calls, [['scan_image', [BYTES, 'fast', 2048, 4000000, 250, ['perspective'], ['uec'], '#f3f4f6',
    ['white', '#000000'], 'capture', ['qr_code', 'ean13']]]]);
  // The caller's own objects reach the module: the bytes and each array, not copies.
  const [, args] = calls[0];
  assert.equal(args[0], BYTES);
  assert.equal(args[5], EVERY.scoreSkipAxes);
  assert.equal(args[10], EVERY.formats);
});

test('S2 scanFrame() passes every option to scan_frame in its positional order', () => {
  const { calls, module } = recorder();
  bindScanner(module).scanFrame(FRAME, EVERY);
  assert.deepEqual(calls, [['scan_frame', [FRAME.data, 2, 2, 'fast', 250, 2048, 4000000, ['perspective'], ['uec'],
    '#f3f4f6', ['white', '#000000'], 'capture', ['qr_code', 'ean13']]]]);
  assert.equal(calls[0][1][0], FRAME.data);
});

test('S3 an option left out arrives as undefined, and each option alone lands in its own position', () => {
  for (const options of [undefined, null, {}]) {
    const image = recorder(), frame = recorder();
    bindScanner(image.module).scan(BYTES, options);
    bindScanner(frame.module).scanFrame(FRAME, options);
    assert.deepEqual(image.calls, [['scan_image', [BYTES, undefined, undefined, undefined, undefined, undefined,
      undefined, undefined, undefined, undefined, undefined]]]);
    // scanFrame names no profile of its own: undefined keeps the engine's default, frame.
    assert.deepEqual(frame.calls, [['scan_frame', [FRAME.data, 2, 2, undefined, undefined, undefined, undefined,
      undefined, undefined, undefined, undefined, undefined, undefined]]]);
  }
  assert.deepEqual(Object.keys(IMAGE_INDEX).sort(), Object.keys(EVERY).sort());
  assert.deepEqual(Object.keys(FRAME_INDEX).sort(), Object.keys(EVERY).sort());
  for (const [key, value] of Object.entries(EVERY)) {
    const image = recorder(), frame = recorder();
    bindScanner(image.module).scan(BYTES, { [key]: value });
    bindScanner(frame.module).scanFrame(FRAME, { [key]: value });
    const wantImage = new Array(11).fill(undefined);
    wantImage[0] = BYTES;
    wantImage[IMAGE_INDEX[key]] = value;
    const wantFrame = new Array(13).fill(undefined);
    wantFrame.splice(0, 3, FRAME.data, 2, 2);
    wantFrame[FRAME_INDEX[key]] = value;
    assert.deepEqual(image.calls, [['scan_image', wantImage]], `scan: ${key}`);
    assert.deepEqual(frame.calls, [['scan_frame', wantFrame]], `scanFrame: ${key}`);
  }
  // An explicit null is passed as given: the engine reads it as unset.
  const nulled = recorder();
  bindScanner(nulled.module).scan(BYTES, { profile: null, budgetMs: null });
  assert.deepEqual(nulled.calls[0][1].slice(1, 5), [null, undefined, undefined, null]);
});

test('S4 an unknown option throws a TypeError that names it and the accepted options, before any scan', () => {
  const { calls, module } = recorder();
  const { scan, scanFrame } = bindScanner(module);
  assert.throws(() => scan(BYTES, { budget_ms: 5 }), { name: 'TypeError',
    message: `scan(bytes, options): unknown option "budget_ms" (did you mean budgetMs?); the options are ${OPTION_LIST}` });
  assert.throws(() => scanFrame(FRAME, { score_skip_axes: ['rotation'] }), { name: 'TypeError',
    message: 'scanFrame(frame, options): unknown option "score_skip_axes" (did you mean scoreSkipAxes?); '
      + `the options are ${OPTION_LIST}` });
  assert.throws(() => scan(BYTES, { profile: 'fast', timeout: 5 }), { name: 'TypeError',
    message: `scan(bytes, options): unknown option "timeout"; the options are ${OPTION_LIST}` });
  // A positional habit (a profile name where the options go) is refused too.
  for (const options of ['full', 5, true, ['full'], () => ({})]) {
    assert.throws(() => scan(BYTES, options), (error) => error instanceof TypeError
      && /^scan\(bytes, options\): the options must be an object/.test(error.message));
    assert.throws(() => scanFrame(FRAME, options), TypeError);
  }
  assert.deepEqual(calls, []);
});

test('S5 scan() takes a Uint8Array or an ArrayBuffer and refuses anything else', () => {
  const { calls, module } = recorder();
  const { scan } = bindScanner(module);
  const buffer = new Uint8Array([1, 2, 3, 4, 5]).buffer;
  scan(buffer);
  const [[, [view]]] = calls;
  assert.equal(Object.prototype.toString.call(view), '[object Uint8Array]');
  assert.equal(view.buffer, buffer, 'a view of the same bytes, not a copy');
  assert.deepEqual([view.byteOffset, view.length], [0, 5]);
  const nodeBuffer = Buffer.from([9, 8, 7]);
  scan(nodeBuffer);
  assert.equal(calls[1][1][0], nodeBuffer, 'a Node Buffer is a Uint8Array and passes as it is');
  // An array of another realm (a frame, a vm context) is still a Uint8Array.
  const foreign = runInNewContext('new Uint8Array([4, 5, 6])');
  assert.equal(foreign instanceof Uint8Array, false);
  scan(foreign);
  assert.equal(calls[2][1][0], foreign);
  assert.equal(calls.length, 3);
  for (const [bytes, named] of [['image.png', 'string'], [[137, 80], 'Array'], [new Uint8ClampedArray(4), 'Uint8ClampedArray'],
    [new DataView(buffer), 'DataView'], [new Uint16Array(2), 'Uint16Array'], [null, 'null'], [undefined, 'undefined'],
    [{ data: BYTES }, 'Object'], [42, 'number']]) {
    assert.throws(() => scan(bytes), { name: 'TypeError',
      message: `scan(bytes): the bytes must be a Uint8Array or an ArrayBuffer, not ${named}` });
  }
  assert.equal(calls.length, 3, 'a refused input never reaches the module');
});

test('S6 scanFrame() takes { data, width, height } with Uint8Array or Uint8ClampedArray pixels', () => {
  const { calls, module } = recorder();
  const { scanFrame } = bindScanner(module);
  // ImageData.data is a Uint8ClampedArray: the module receives a Uint8Array over the same bytes,
  // offset and length included.
  const backing = new ArrayBuffer(64);
  const clamped = new Uint8ClampedArray(backing, 16, 36);
  scanFrame({ data: clamped, width: 3, height: 3, colorSpace: 'srgb' });
  const [[name, [view, width, height]]] = calls;
  assert.equal(name, 'scan_frame');
  assert.equal(Object.prototype.toString.call(view), '[object Uint8Array]');
  assert.equal(view.buffer, backing);
  assert.deepEqual([view.byteOffset, view.length, width, height], [16, 36, 3, 3]);
  for (const [frame, named] of [[null, 'null'], [undefined, 'undefined'], ['frame', 'string']]) {
    assert.throws(() => scanFrame(frame), { name: 'TypeError',
      message: `scanFrame(frame): the frame must be { data, width, height }, as an ImageData is, not ${named}` });
  }
  for (const [data, named] of [[undefined, 'undefined'], [[255, 255, 255, 255], 'Array'], [backing, 'ArrayBuffer'],
    [new Float32Array(4), 'Float32Array']]) {
    assert.throws(() => scanFrame({ data, width: 1, height: 1 }), { name: 'TypeError',
      message: `scanFrame(frame): frame.data must be a Uint8Array or a Uint8ClampedArray of RGBA bytes, not ${named}` });
  }
  assert.equal(calls.length, 1);
});

test('S7 isFinal() is false only for a report the budget cut', () => {
  assert.equal(isFinal({ trace: { budget_exhausted: true } }), false);
  assert.equal(isFinal({ trace: { budget_exhausted: false } }), true);
  // Older reports carry no flag, or a null one: nothing in them says they were cut.
  assert.equal(isFinal({ trace: {} }), true);
  assert.equal(isFinal({ trace: { budget_exhausted: null } }), true);
  assert.equal(isFinal({ trace: { stages: [], engine_panics: 0, total_ms: 3 } }), true);
  // Only the boolean true is a cut.
  assert.equal(isFinal({ trace: { budget_exhausted: 'true' } }), true);
  for (const [value, named] of [[undefined, 'undefined'], [null, 'null'], ['report', 'string'], [5, 'number'],
    [true, 'boolean']]) {
    assert.throws(() => isFinal(value), { name: 'TypeError',
      message: `isFinal(report): the report must be the object a scan returned, not ${named}` });
  }
  for (const value of [{}, { trace: null }, { trace: 'cut' }, []]) {
    assert.throws(() => isFinal(value), { name: 'TypeError',
      message: 'isFinal(report): the report has no trace; pass the whole report a scan returned' });
  }
  assert.equal(isFinal, auto.isFinal, './auto re-exports the same function');
  assert.equal(isFinal, node.isFinal, './node re-exports the same function');
});

test('S8 retryBudgetMs reruns a cut scan once, with that budget, and returns the second report', () => {
  for (const [call, name, input, index] of [['scan', 'scan_image', BYTES, IMAGE_INDEX], ['scanFrame', 'scan_frame', FRAME,
    FRAME_INDEX]]) {
    const budgets = (calls) => calls.map(([, args]) => args[index.budgetMs]);
    // not final, then final: two scans, and the second report is the result
    {
      const cut = CUT(), final = FINAL();
      const { calls, module } = recorder(cut, final);
      const report = bindScanner(module)[call](input, { profile: 'full', budgetMs: 50, retryBudgetMs: 4000,
        formats: ['qr_code'] });
      assert.equal(report, final, `${call}: the second report itself`);
      assert.deepEqual(calls.map(([fn]) => fn), [name, name]);
      assert.deepEqual(budgets(calls), [50, 4000]);
      // Only the budget differs between the two calls.
      const [first, second] = calls.map(([, args]) => args.filter((_value, at) => at !== index.budgetMs));
      assert.deepEqual(second, first);
      assert.equal(second[0], first[0]);
    }
    // final first: one scan
    {
      const final = FINAL();
      const { calls, module } = recorder(final, CUT());
      assert.equal(bindScanner(module)[call](input, { budgetMs: 50, retryBudgetMs: 4000 }), final);
      assert.deepEqual(budgets(calls), [50]);
    }
    // two reports that are not final: exactly two scans, and the second is returned as it is
    {
      const first = CUT(), second = CUT();
      const { calls, module } = recorder(first, second, FINAL());
      const report = bindScanner(module)[call](input, { budgetMs: 50, retryBudgetMs: 100 });
      assert.equal(report, second);
      assert.equal(isFinal(report), false);
      assert.deepEqual(budgets(calls), [50, 100]);
    }
    // 0 is a budget (the engine's "no limit"), not "no rerun"; the first scan keeps its default
    {
      const { calls, module } = recorder(CUT(), FINAL());
      bindScanner(module)[call](input, { retryBudgetMs: 0 });
      assert.deepEqual(budgets(calls), [undefined, 0]);
    }
    // without retryBudgetMs: one scan, whatever the report says
    for (const options of [undefined, { budgetMs: 50 }, { budgetMs: 50, retryBudgetMs: undefined }]) {
      const cut = CUT();
      const { calls, module } = recorder(cut, FINAL());
      assert.equal(bindScanner(module)[call](input, options), cut);
      assert.equal(calls.length, 1);
    }
    // a report without the flag is final: no rerun
    {
      const older = { detections: [], score: null, hints: [], trace: { stages: [] } };
      const { calls, module } = recorder(older, FINAL());
      assert.equal(bindScanner(module)[call](input, { retryBudgetMs: 0 }), older);
      assert.equal(calls.length, 1);
    }
    // retryBudgetMs is a number: anything else is refused before the first scan
    for (const [value, named] of [['4000', 'string'], [null, 'null'], [true, 'boolean'], [{}, 'Object']]) {
      const { calls, module } = recorder(CUT(), FINAL());
      assert.throws(() => bindScanner(module)[call](input, { retryBudgetMs: value }), (error) => error instanceof TypeError
        && error.message.endsWith(`retryBudgetMs must be a number of milliseconds (0 for no limit), not ${named}`));
      assert.equal(calls.length, 0);
    }
  }
});

test('S9 a report is returned as the module made it, and a module error is thrown as it is', () => {
  const made = Object.freeze({ detections: Object.freeze([]), score: null, hints: Object.freeze([]),
    trace: Object.freeze({ stages: Object.freeze([]), budget_exhausted: false }), versions: Object.freeze({}) });
  const { scan, scanFrame } = bindScanner(recorder(made).module);
  assert.equal(scan(BYTES), made);
  assert.equal(scanFrame(FRAME, { retryBudgetMs: 0 }), made);
  const refused = new Error('invalid option `max_dimension`: 0 is not a whole number from 1 to 4294967295 [QRS-006]');
  for (const call of ['scan', 'scanFrame']) {
    const input = call === 'scan' ? BYTES : FRAME;
    const first = recorder(refused);
    assert.throws(() => bindScanner(first.module)[call](input, { maxDimension: 0 }), (error) => error === refused);
    assert.equal(first.calls.length, 1);
    // also when the rerun is the call that throws
    const second = recorder(CUT(), refused);
    assert.throws(() => bindScanner(second.module)[call](input, { retryBudgetMs: 0 }), (error) => error === refused);
    assert.equal(second.calls.length, 2);
  }
});

test('S10 bindScanner() needs the loaded module and returns a frozen { scan, scanFrame }', () => {
  const { module } = recorder();
  const bound = bindScanner(module);
  assert.deepEqual(Object.keys(bound), ['scan', 'scanFrame']);
  assert.equal(Object.isFrozen(bound), true);
  for (const value of [undefined, null, {}, { scan_image() {} }, { scan_frame() {} }, 'module',
    { scan_image: 'a', scan_frame: 'b' }]) {
    assert.throws(() => bindScanner(value), { name: 'TypeError', message: 'bindScanner(module): the module must be '
      + 'the loaded scanner, with its scan_image and scan_frame functions' });
  }
});

test('S11 scan.js imports nothing, and ./scan and ./auto import without WebAssembly or a fetch call', () => {
  const child = spawnSync(process.execPath, ['--input-type=module', '-e', `
    globalThis.WebAssembly = undefined;
    let fetchCalls = 0;
    globalThis.fetch = () => { fetchCalls += 1; throw new Error('unexpected fetch'); };
    const scan = await import(${JSON.stringify(packaged('scan.js').href)});
    const auto = await import(${JSON.stringify(packaged('auto.js').href)});
    const lengths = [];
    const bound = scan.bindScanner({ scan_image: (...args) => { lengths.push(args.length); return { trace: {} }; },
      scan_frame: (...args) => { lengths.push(args.length); return { trace: {} }; } });
    bound.scan(new Uint8Array(1));
    bound.scanFrame({ data: new Uint8ClampedArray(4), width: 1, height: 1 });
    const loaded = await auto.loadScanner().then(() => 'loaded', (error) => error.code);
    console.log(JSON.stringify({ scan: Object.keys(scan).sort(), auto: Object.keys(auto).sort(), lengths, loaded,
      fetchCalls }));`], { encoding: 'utf8' });
  assert.equal(child.status, 0, child.stderr);
  assert.deepEqual(JSON.parse(child.stdout.trim().split('\n').pop()), {
    scan: ['bindScanner', 'isFinal'],
    auto: ['ScannerInitError', 'createScannerLoader', 'isFinal', 'loadScanner', 'scannerCapabilities'],
    lengths: [11, 13], loaded: 'wasm_unavailable', fetchCalls: 0 });
  // The forms a bundler rewrites stay literal in the loader.
  const source = readFileSync(packaged('auto.js'), 'utf8');
  assert.equal(source.split("import('./qrcode-barcode-scanner.js')").length, 2);
  assert.equal(source.split("new URL('./qrcode-barcode-scanner_bg.wasm', import.meta.url)").length, 2);
});

// ---- The ./auto loader under a fake fetch --------------------------------------------------

const RETRYABLE = { invalid_options: false, wasm_unavailable: false, wasm_features_unsupported: false,
  loader_import_failed: true, asset_network_failed: true, asset_http_failed: true, asset_read_failed: true,
  binary_invalid: false, wasm_validation_failed: false, wasm_compile_failed: false, wasm_instantiate_failed: false };
const WASM_ADDRESS = 'https://scanner.invalid/scanner.wasm';
const served = () => new Response(wasmBytes, { status: 200, headers: { 'content-type': 'application/wasm' } });
// Replaces the global fetch while `run` runs. Each call takes the next step (a function that
// returns a response or throws); a call past the last step is recorded and fails.
async function withFetch(steps, run) {
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    if (calls.length > steps.length) throw new Error(`unexpected fetch call ${calls.length}`);
    return steps[calls.length - 1]();
  };
  try { return await run(calls); } finally { globalThis.fetch = original; }
}
const settled = (promise) => promise.then((value) => ({ value }), (error) => ({ error }));
// A turn of the event loop: anything the loader had scheduled by itself would have run.
const turn = () => new Promise((done) => { setImmediate(done); });
const assertLoaded = (scanner, label) => {
  assert.equal(Object.isFrozen(scanner), true, `${label}: frozen`);
  assert.deepEqual(Object.keys(scanner).sort(), ['capabilities', 'default', 'initSync', 'scan', 'scanFrame',
    'scan_frame', 'scan_image', 'variant', 'version'], label);
  assert.equal(scanner.variant, 'portable');
  assert.equal(scanner.version(), pkg.version);
};

test('S12 ScannerInitError.retryable is true for the four transient codes only', () => {
  for (const [code, retryable] of Object.entries(RETRYABLE)) {
    const error = new ScannerInitError(code, 'portable');
    assert.equal(error.retryable, retryable, code);
    assert.deepEqual([error.name, error.message, error.code, error.variant, 'status' in error, 'cause' in error],
      ['ScannerInitError', `Scanner initialization failed: ${code}`, code, 'portable', false, false]);
  }
  const cause = new TypeError('fetch failed');
  const failed = new ScannerInitError('asset_http_failed', 'portable', cause, 503);
  assert.deepEqual([failed.status, failed.cause, failed.retryable], [503, cause, true]);
  assert.equal(ScannerInitError, node.ScannerInitError, './node re-exports the same class');
});

test('S13 a transient failure is shared by the callers waiting on it, and the next call starts over', async () => {
  const refused = new TypeError('fetch failed');
  await withFetch([() => { throw refused; }, served], async (calls) => {
    const load = createScannerLoader({ wasmUrl: WASM_ADDRESS });
    const first = load(), second = load();
    assert.equal(first, second, 'concurrent callers hold one Promise');
    const [a, b] = await Promise.all([settled(first), settled(second)]);
    assert.equal(a.error, b.error, 'and receive one rejection');
    assert.ok(a.error instanceof ScannerInitError);
    assert.deepEqual([a.error.code, a.error.retryable, a.error.variant, a.error.cause],
      ['asset_network_failed', true, 'portable', refused]);
    assert.deepEqual(calls, [WASM_ADDRESS]);
    // nothing retries by itself
    await turn();
    assert.deepEqual(calls, [WASM_ADDRESS]);
    const third = load();
    assert.notEqual(third, first, 'the next call is a fresh attempt');
    const scanner = await third;
    assertLoaded(scanner, 'second attempt');
    assert.deepEqual(calls, [WASM_ADDRESS, WASM_ADDRESS]);
    // a loaded scanner is kept: no further request
    assert.equal(load(), third);
    assert.equal(await load(), scanner);
    assert.deepEqual(calls, [WASM_ADDRESS, WASM_ADDRESS]);
    assert.deepEqual(texts(scanner.scan(fixture('clean/gen_v2_l.png'), { profile: 'fast', budgetMs: 0 })), ['qrc.ai/v2l']);
  });
});

test('S14 an HTTP error and a failed body read are transient too, and a failure can repeat', async () => {
  await withFetch([() => new Response('busy', { status: 503 }), served], async (calls) => {
    const load = createScannerLoader({ wasmUrl: WASM_ADDRESS });
    const { error } = await settled(load());
    assert.deepEqual([error.code, error.retryable, error.status, 'cause' in error], ['asset_http_failed', true, 503, false]);
    assertLoaded(await load(), 'after a 503');
    assert.equal(calls.length, 2);
  });
  const broken = new TypeError('terminated');
  await withFetch([() => ({ ok: true, status: 200, arrayBuffer: () => Promise.reject(broken) }), served], async (calls) => {
    const load = createScannerLoader({ wasmUrl: WASM_ADDRESS });
    const { error } = await settled(load());
    assert.deepEqual([error.code, error.retryable, error.cause], ['asset_read_failed', true, broken]);
    assertLoaded(await load(), 'after a failed read');
    assert.equal(calls.length, 2);
  });
  // Two failures in a row: two attempts, two distinct rejections, and still no attempt unasked.
  await withFetch([() => { throw new TypeError('offline'); }, () => new Response('gone', { status: 404 })], async (calls) => {
    const load = createScannerLoader({ wasmUrl: WASM_ADDRESS });
    const first = await settled(load()), second = await settled(load());
    assert.deepEqual([first.error.code, second.error.code, second.error.status], ['asset_network_failed', 'asset_http_failed', 404]);
    assert.notEqual(first.error, second.error);
    await turn();
    assert.equal(calls.length, 2);
  });
  // With no wasmUrl the loader asks for the file beside it.
  await withFetch([served], async (calls) => {
    assertLoaded(await createScannerLoader()(), 'default URL');
    assert.deepEqual(calls, [WASM_URL.href]);
  });
});

test('S15 a permanent failure stays cached: one attempt, one rejection', async () => {
  // A valid header then a truncated type section; and bytes that are no WASM at all.
  const INVALID = new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0, 1, 4, 1, 96]);
  for (const [bytes, code] of [[new Uint8Array([0, 0, 0, 0]), 'binary_invalid'], [INVALID, 'wasm_validation_failed']]) {
    await withFetch([() => new Response(bytes), served], async (calls) => {
      const load = createScannerLoader({ wasmUrl: WASM_ADDRESS });
      const first = load();
      const { error } = await settled(first);
      assert.deepEqual([error.code, error.retryable, error.variant, error.cause?.name], [code, false, 'portable', 'CompileError']);
      assert.equal(load(), first, `${code}: the same Promise`);
      assert.equal((await settled(load())).error, error, `${code}: the same rejection`);
      assert.deepEqual(calls, [WASM_ADDRESS], `${code}: no second attempt`);
    });
  }
  await withFetch([served], async (calls) => {
    const load = createScannerLoader({ variant: 'simd', wasmUrl: WASM_ADDRESS });
    const first = load();
    const { error } = await settled(first);
    assert.deepEqual([error.code, error.retryable, error.variant], ['invalid_options', false, null]);
    assert.equal(load(), first);
    // A realm that refuses the baseline: the verdict is kept even once the realm would pass.
    const unsupported = createScannerLoader({ wasmUrl: WASM_ADDRESS });
    const validate = WebAssembly.validate;
    let refusedOnce;
    WebAssembly.validate = () => false;
    try { refusedOnce = unsupported(); } finally { WebAssembly.validate = validate; }
    const verdict = await settled(refusedOnce);
    assert.deepEqual([verdict.error.code, verdict.error.retryable], ['wasm_features_unsupported', false]);
    assert.equal(unsupported(), refusedOnce);
    assert.deepEqual(calls, [], 'neither failure requested the module');
  });
});

test('S16 a failed import of the module is transient: the next call imports again', async () => {
  // The loader and scan.js alone in a folder: the generated module is missing.
  const folder = scratchDir('loader');
  for (const file of ['auto.js', 'scan.js']) copyFileSync(packaged(file), join(folder, file));
  const lone = await import(pathToFileURL(join(folder, 'auto.js')).href);
  await withFetch([served], async (calls) => {
    const load = lone.createScannerLoader({ wasmUrl: WASM_ADDRESS });
    const first = await settled(load()), second = await settled(load());
    for (const { error } of [first, second]) {
      assert.ok(error instanceof lone.ScannerInitError);
      assert.deepEqual([error.code, error.retryable, error.cause?.code], ['loader_import_failed', true, 'ERR_MODULE_NOT_FOUND']);
    }
    assert.notEqual(first.error, second.error, 'two attempts');
    assert.deepEqual(calls, [], 'the WASM is not requested before the module imports');
    copyFileSync(packaged('qrcode-barcode-scanner.js'), join(folder, 'qrcode-barcode-scanner.js'));
    const scanner = await load();
    assert.equal(scanner.version(), pkg.version);
    assert.deepEqual(calls, [WASM_ADDRESS]);
  });
});

// ---- The ./node entry on the real module ---------------------------------------------------

// The pixels of a non-interlaced 8-bit gray (0), RGB (2) or RGBA (6) PNG as an RGBA frame.
function pngFrame(bytes) {
  const view = Buffer.from(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const width = view.readUInt32BE(16), height = view.readUInt32BE(20);
  const [depth, color, , , interlace] = view.subarray(24, 29);
  const channels = { 0: 1, 2: 3, 6: 4 }[color];
  assert.ok(depth === 8 && channels && interlace === 0, 'test helper: 8-bit gray, RGB or RGBA, not interlaced');
  const idat = [];
  for (let at = 8; at < view.length;) {
    const length = view.readUInt32BE(at), type = view.toString('latin1', at + 4, at + 8);
    if (type === 'IDAT') idat.push(view.subarray(at + 8, at + 8 + length));
    at += 12 + length;
  }
  const packed = inflateSync(Buffer.concat(idat)), stride = width * channels;
  const rows = new Uint8Array(height * stride);
  for (let y = 0; y < height; y++) {
    const filter = packed[y * (stride + 1)];
    for (let x = 0; x < stride; x++) {
      const raw = packed[y * (stride + 1) + 1 + x];
      const a = x >= channels ? rows[y * stride + x - channels] : 0;
      const b = y > 0 ? rows[(y - 1) * stride + x] : 0;
      const c = x >= channels && y > 0 ? rows[(y - 1) * stride + x - channels] : 0;
      let predictor = 0;
      if (filter === 1) predictor = a;
      else if (filter === 2) predictor = b;
      else if (filter === 3) predictor = (a + b) >> 1;
      else if (filter === 4) {
        const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        predictor = pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
      }
      rows[y * stride + x] = (raw + predictor) & 255;
    }
  }
  const data = new Uint8ClampedArray(width * height * 4);
  for (let pixel = 0; pixel < width * height; pixel++) {
    const at = pixel * channels;
    const [r, g, b, alpha] = channels === 1 ? [rows[at], rows[at], rows[at], 255]
      : channels === 3 ? [rows[at], rows[at + 1], rows[at + 2], 255] : rows.subarray(at, at + 4);
    data.set([r, g, b, alpha], pixel * 4);
  }
  return { data, width, height };
}

test('S17 ./node loads the package\'s own WASM from disk into the shape ./auto resolves to', async () => {
  assert.deepEqual(Object.entries(node).map(([name, value]) => [name, typeof value]).sort(),
    [['ScannerInitError', 'function'], ['createScannerLoader', 'function'], ['isFinal', 'function'],
      ['loadScanner', 'function']]);
  await withFetch([], async (calls) => {
    const first = node.loadScanner(), second = node.loadScanner();
    assert.equal(first, second, 'one shared Promise');
    const scanner = await first;
    assertLoaded(scanner, './node');
    assert.equal(await node.loadScanner(), scanner);
    // a path and a file: URL both name the file to read
    for (const wasmPath of [fileURLToPath(WASM_URL), WASM_URL]) {
      assertLoaded(await node.createScannerLoader({ wasmPath })(), 'wasmPath');
    }
    assert.deepEqual(calls, [], 'the Node entry never fetches');
  });
});

test('S18 ./node gives the loader\'s codes: a failed read is transient, bad bytes and options are kept', async () => {
  const folder = scratchDir('node');
  const wasmPath = join(folder, 'scanner.wasm');
  const load = node.createScannerLoader({ wasmPath });
  const first = load();
  assert.equal(load(), first, 'concurrent callers hold one Promise');
  const missing = await settled(first), again = await settled(load());
  for (const { error } of [missing, again]) {
    assert.ok(error instanceof ScannerInitError);
    assert.deepEqual([error.code, error.retryable, error.variant, error.cause?.code], ['asset_read_failed', true, 'portable', 'ENOENT']);
  }
  assert.notEqual(missing.error, again.error, 'the second call read again');
  copyFileSync(WASM_URL, wasmPath);
  assertLoaded(await load(), 'once the file is there');

  const garbage = join(folder, 'garbage.wasm');
  writeFileSync(garbage, 'not a module');
  for (const [options, code, variant] of [[{ wasmPath: garbage }, 'binary_invalid', 'portable'],
    [{ wasmPath: 42 }, 'invalid_options', null],
    [{ wasmPath: new URL('https://scanner.invalid/scanner.wasm') }, 'invalid_options', null]]) {
    const kept = node.createScannerLoader(options);
    const attempt = kept();
    const { error } = await settled(attempt);
    assert.deepEqual([error.code, error.retryable, error.variant], [code, false, variant]);
    assert.equal(kept(), attempt, `${code}: the same Promise`);
    assert.equal((await settled(kept())).error, error);
  }
});

test('S19 ./node scans real images through scan() and scanFrame(), report unchanged', async () => {
  const scanner = await node.loadScanner();
  const clean = fixture('clean/OK_68ms_100_4e875a2c.png');
  const report = scanner.scan(clean, { profile: 'full', budgetMs: 0 });
  assert.deepEqual(codes(report), [['qr_code', 'https://qrc-ai.com/76xMa']]);
  assert.equal(report.detections[0].payload.url, 'https://qrc-ai.com/76xMa');
  assert.equal(isFinal(report), true);
  assert.equal(report.score.weights_run, 100);
  assert.equal(report.versions.scanner, pkg.version);
  // The positional call of the same module makes the same report, wall-clock fields aside.
  const positional = scanner.scan_image(clean, 'full', undefined, undefined, 0);
  assert.deepEqual(untimed(report), untimed(positional));
  // An ArrayBuffer of the same file reads the same; the positional function does not take one.
  const copy = clean.buffer.slice(clean.byteOffset, clean.byteOffset + clean.byteLength);
  assert.deepEqual(untimed(scanner.scan(copy, { profile: 'full', budgetMs: 0 })), untimed(positional));
  assert.throws(() => scanner.scan_image(copy, 'full'), /\[QRS-001\]/);

  // profile: the blob template class decodes in full and not in fast
  const monkey = fixture('artistic/blob-style-monkey-logo.webp');
  assert.deepEqual(texts(scanner.scan(monkey, { profile: 'full', budgetMs: 0 })), ['https://qrc-ai.com/Uo54C']);
  assert.deepEqual(texts(scanner.scan(monkey, { profile: 'fast', budgetMs: 0 })), []);
  // scoreSkipAxes, scorePreset and scoreSkipChecks
  const v2l = fixture('clean/gen_v2_l.png');
  const whole = scanner.scan(v2l, { profile: 'full', budgetMs: 0 });
  const skipped = scanner.scan(v2l, { profile: 'full', budgetMs: 0, scoreSkipAxes: ['perspective', 'rotation'] });
  assert.deepEqual(skipped.score.axes.map((a) => a.axis), ['resolution', 'blur', 'contrast', 'lighting']);
  assert.equal(skipped.score.weights_run, 70);
  assert.deepEqual(scanner.scan(v2l, { profile: 'full', budgetMs: 0, scorePreset: 'design' }).score, skipped.score);
  const withheld = scanner.scan(v2l, { profile: 'full', budgetMs: 0, scoreSkipChecks: ['uec', 'iso15415'] });
  assert.deepEqual([withheld.score.uec, withheld.score.iso15415, withheld.score.value], [null, null, whole.score.value]);
  // alphaBackground and alphaPalette
  const transparent = new Uint8Array(readFileSync(new URL('../../playground/public/samples/transparent.png', import.meta.url)));
  assert.deepEqual(texts(scanner.scan(transparent, { profile: 'full', budgetMs: 0 })), ['https://qrc-ai.com/76xMa']);
  assert.deepEqual(texts(scanner.scan(transparent, { profile: 'full', budgetMs: 0, alphaBackground: 'none' })), []);
  const themed = scanner.scan(transparent, { profile: 'full', budgetMs: 0, alphaPalette: ['#f3f4f6', 'black'] });
  assert.deepEqual(themed.alpha.envelope.palette.map(({ background, decoded }) => ({ background, decoded })),
    [{ background: '#f3f4f6', decoded: true }, { background: 'black', decoded: false }]);
  // maxDimension, maxPixels and the engine's own errors, thrown as they are (the image is 264 x 264)
  assert.throws(() => scanner.scan(v2l, { maxDimension: 100 }), /^Error: image 264x264 exceeds limit 100 \[QRS-002\]$/);
  assert.throws(() => scanner.scan(v2l, { maxPixels: 1000 }), /\[QRS-003\]$/);
  assert.throws(() => scanner.scan(v2l, { maxDimension: 0 }), /invalid option `max_dimension`: .* \[QRS-006\]$/);
  assert.throws(() => scanner.scan(v2l, { profile: 'fastest' }), /unknown profile `fastest`/);
  assert.throws(() => scanner.scan(new Uint8Array([1, 2, 3])), /\[QRS-001\]$/);

  // scanFrame: the same pixels as an ImageData holds them, at an offset inside a larger buffer
  const pixels = pngFrame(v2l);
  const backing = new ArrayBuffer(pixels.data.length + 32);
  const data = new Uint8ClampedArray(backing, 32);
  data.set(pixels.data);
  const frame = { data, width: pixels.width, height: pixels.height };
  // no profile: the engine's frame profile, which decodes and does not score
  const framed = scanner.scanFrame(frame, { budgetMs: 0 });
  assert.deepEqual([texts(framed), framed.score, isFinal(framed)], [['qrc.ai/v2l'], null, true]);
  const judged = scanner.scanFrame(frame, { profile: 'full', budgetMs: 0, scoreSkipAxes: ['perspective', 'rotation'] });
  assert.deepEqual(judged.score, skipped.score, 'the RGBA copy scores like the encoded image');
  assert.throws(() => scanner.scanFrame(frame, { maxDimension: 100 }), /\[QRS-002\]$/);
  assert.throws(() => scanner.scanFrame({ data: new Uint8ClampedArray(10), width: 2, height: 2 }), /\[QRS-004\]$/);

  // retryBudgetMs on the real module. The negative sample never decodes and its full ladder
  // outlasts a 1 ms budget (test.mjs asserts the same cut); the rerun is unbudgeted, so the
  // result is final whatever the first scan did.
  const degraded = fixture('degraded/FAIL_1491ms_0_584c998c.png');
  const budgets = [];
  const counted = bindScanner({ scan_image: (...args) => { budgets.push(args[4]); return scanner.scan_image(...args); },
    scan_frame: scanner.scan_frame });
  const rerun = counted.scan(degraded, { profile: 'full', budgetMs: 1, retryBudgetMs: 0 });
  assert.deepEqual(budgets, [1, 0]);
  assert.deepEqual([texts(rerun), isFinal(rerun)], [[], true]);
  assert.equal(attempts(rerun), attempts(scanner.scan(degraded, { profile: 'full', budgetMs: 0 })));
  assert.equal(isFinal(scanner.scan(degraded, { profile: 'full', budgetMs: 1 })), false);
  // A detection the budget left unjudged (score null) is judged by the rerun.
  const rejudged = scanner.scan(clean, { profile: 'full', budgetMs: 1, retryBudgetMs: 0 });
  assert.deepEqual([texts(rejudged), isFinal(rejudged), rejudged.score.weights_run], [['https://qrc-ai.com/76xMa'], true, 100]);
});

test('S20 the package name resolves ./scan and ./node, and refuses the Node loader by its file path', () => {
  const consumer = scratchDir('consumer');
  mkdirSync(join(consumer, 'node_modules', '@qrcode-ai-com'), { recursive: true });
  symlinkSync(fileURLToPath(PACKAGE), join(consumer, 'node_modules', pkg.name), 'dir');
  writeFileSync(join(consumer, 'package.json'), '{"name":"scan-consumer","private":true,"type":"module"}\n');
  const child = spawnSync(process.execPath, ['--input-type=module', '-e', `
    import { readFileSync } from 'node:fs';
    import { basename } from 'node:path';
    import { fileURLToPath } from 'node:url';
    const name = ${JSON.stringify(pkg.name)};
    const observed = {};
    for (const subpath of ['/scan', '/node', '/node.js']) {
      try {
        const namespace = await import(name + subpath);
        observed[subpath] = { file: basename(fileURLToPath(import.meta.resolve(name + subpath))),
          exports: Object.keys(namespace).sort() };
      } catch (error) { observed[subpath] = { code: error.code }; }
    }
    const { loadScanner, isFinal } = await import(name + '/node');
    const scanner = await loadScanner();
    const report = scanner.scan(readFileSync(${JSON.stringify(fileURLToPath(new URL('../../fixtures/clean/gen_v2_l.png', import.meta.url)))}),
      { profile: 'fast', budgetMs: 0 });
    observed.scanned = { texts: report.detections.map((d) => d.content.text), final: isFinal(report),
      version: scanner.version() };
    console.log(JSON.stringify(observed));`], { cwd: consumer, encoding: 'utf8' });
  assert.equal(child.status, 0, child.stderr);
  assert.deepEqual(JSON.parse(child.stdout.trim().split('\n').pop()), {
    '/scan': { file: 'scan.js', exports: ['bindScanner', 'isFinal'] },
    '/node': { file: 'node.js', exports: ['ScannerInitError', 'createScannerLoader', 'isFinal', 'loadScanner'] },
    '/node.js': { code: 'ERR_PACKAGE_PATH_NOT_EXPORTED' },
    scanned: { texts: ['qrc.ai/v2l'], final: true, version: pkg.version } });
});

// ---- formats on the real module ----------------------------------------------------------
// S22 to S24 need the module that reads the trailing `formats` argument (0.12.1): a 0.12.0
// module ignores an argument past its last one, returns every symbology and refuses no name.

// One image holds a QR code and a Code 128.
const MIXED = 'symbology/mixed-code128-qr.png';
const QR_ONLY = [['qr_code', 'https://qrc-ai.com/76xMa']];
const CODE128_ONLY = [['code128', 'STOCK-4827']];
const BOTH = [...CODE128_ONLY, ...QR_ONLY];
const UNBUDGETED = { profile: 'fast', budgetMs: 0 };

test('S21 without formats, and with an empty list, every symbology is read', async () => {
  const scanner = await node.loadScanner();
  const mixed = fixture(MIXED), frame = pngFrame(mixed);
  assert.deepEqual(codes(scanner.scan(mixed, UNBUDGETED)), BOTH);
  assert.deepEqual(codes(scanner.scan(mixed, { ...UNBUDGETED, formats: [] })), BOTH);
  assert.deepEqual(codes(scanner.scan(mixed, { ...UNBUDGETED, formats: ['code128', 'qr_code'] })), BOTH);
  assert.deepEqual(codes(scanner.scanFrame(frame, UNBUDGETED)), BOTH);
  assert.deepEqual(codes(scanner.scanFrame(frame, { ...UNBUDGETED, formats: [] })), BOTH);
});

test('S22 scan() with formats returns the listed symbologies and no other', async () => {
  const scanner = await node.loadScanner();
  const mixed = fixture(MIXED);
  assert.deepEqual(codes(scanner.scan(mixed, { ...UNBUDGETED, formats: ['qr_code'] })), QR_ONLY,
    'formats qr_code: the QR code and no Code 128');
  assert.deepEqual(codes(scanner.scan(mixed, { ...UNBUDGETED, formats: ['code128'] })), CODE128_ONLY,
    'formats code128: the Code 128 and no QR code');
  // a symbology the image does not hold: nothing, and the scan still ran to its end
  const none = scanner.scan(mixed, { ...UNBUDGETED, formats: ['aztec'] });
  assert.deepEqual([codes(none), isFinal(none)], [[], true]);
  // the full profile filters the same way
  assert.deepEqual(codes(scanner.scan(mixed, { profile: 'full', budgetMs: 0, formats: ['qr_code'] })), QR_ONLY);
});

test('S23 scanFrame() with formats returns the listed symbologies and no other', async () => {
  const scanner = await node.loadScanner();
  const frame = pngFrame(fixture(MIXED));
  assert.deepEqual(codes(scanner.scanFrame(frame, { ...UNBUDGETED, formats: ['qr_code'] })), QR_ONLY);
  assert.deepEqual(codes(scanner.scanFrame(frame, { ...UNBUDGETED, formats: ['code128'] })), CODE128_ONLY);
});

test('S24 a formats name the engine does not know throws, on scan() and scanFrame()', async () => {
  const scanner = await node.loadScanner();
  const mixed = fixture(MIXED);
  // The wire name is ean13: the spelling with an underscore is not one.
  for (const formats of [['qr_kode'], ['qr_code', 'ean_13']]) {
    assert.throws(() => scanner.scan(mixed, { ...UNBUDGETED, formats }), Error, `scan: ${formats}`);
    assert.throws(() => scanner.scanFrame(pngFrame(mixed), { ...UNBUDGETED, formats }), Error, `scanFrame: ${formats}`);
  }
});
