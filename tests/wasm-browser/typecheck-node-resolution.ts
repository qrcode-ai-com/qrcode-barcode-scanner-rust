// The root, loader, camera and overlay entries by package name under Node's own resolution
// (tsconfig.node-resolution.json: module and moduleResolution nodenext), the setting of a
// TypeScript server and of many libraries. The package is an ES module, so there a relative
// import inside one of its declarations resolves only with its file extension. An import that
// does not resolve is reported once inside the declaration, which `skipLibCheck` hides, and
// every type it brought then reads as `any`: a report whose fields are no longer checked.
//
// Each @ts-expect-error below sits on a line that is an error only while the type is known.
// When a declaration loses a type, the line stops being an error and tsc reports the unused
// directive, with or without `skipLibCheck`. typecheck.ts compiles the same entries under a
// bundler's resolution, which accepts both forms and so cannot see this.
import { capabilities, scan_frame, scan_image } from '@qrcode-ai-com/qrcode-barcode-scanner-wasm';
import { loadScanner } from '@qrcode-ai-com/qrcode-barcode-scanner-wasm/auto';
import { loadScanner as loadNodeScanner } from '@qrcode-ai-com/qrcode-barcode-scanner-wasm/node';
import { bindScanner } from '@qrcode-ai-com/qrcode-barcode-scanner-wasm/scan';
import type { ScanReport } from '@qrcode-ai-com/qrcode-barcode-scanner-wasm/report-types';
import {
  contentKey, createDetectionTracker, type CameraScannerOptions,
} from '@qrcode-ai-com/qrcode-barcode-scanner-wasm/camera';
import {
  describeDetection, projectOverlayGeometry, type CameraOverlay, type OverlayDestinations, type OverlayView,
} from '@qrcode-ai-com/qrcode-barcode-scanner-wasm/camera-overlay';

const bytes = new Uint8Array();

// The shared report types, and the named options over them.
declare const report: ScanReport;
// @ts-expect-error ./report-types: a report has no such field
report.nope;
// @ts-expect-error ./scan: the bound scan returns a report
bindScanner({ scan_image, scan_frame }).scan(bytes).nope;

// The root module: its declaration is written at pack time and imports ./report-types.
// @ts-expect-error root: scan_image returns a report
scan_image(bytes).nope;
// @ts-expect-error root: scan_frame returns a report
scan_frame(bytes, 1, 1).nope;
// @ts-expect-error root: capabilities() is typed
capabilities().nope;

// The loaders: the named functions, and the positional ones of the module they resolve to.
const browser = await loadScanner();
// @ts-expect-error ./auto: scan returns a report
browser.scan(bytes).nope;
// @ts-expect-error ./auto: the loaded module's scan_image returns a report
browser.scan_image(bytes).nope;
const server = await loadNodeScanner();
// @ts-expect-error ./node: scan returns a report
server.scan(bytes).nope;
// @ts-expect-error ./node: the loaded module's scan_image returns a report
server.scan_image(bytes).nope;

// The camera module imports ./report-types: a detection, and the report its scan callback returns.
// @ts-expect-error ./camera: contentKey takes a detection
contentKey(42);
// @ts-expect-error ./camera: the tracker takes a report or detections
createDetectionTracker().update(42, { width: 1, height: 1, observedAt: 0 });
declare const onResult: NonNullable<CameraScannerOptions['onResult']>;
// @ts-expect-error ./camera: onResult receives a report
onResult(42, undefined as never, null);

// The overlay module imports ./report-types, ./camera and ./destination.
// @ts-expect-error ./camera-overlay: describeDetection takes a detection (./report-types)
describeDetection(42);
declare const view: OverlayView;
// @ts-expect-error ./camera-overlay: a geometry kind is one of the tracker's (./camera)
projectOverlayGeometry({ kind: 'nope', points: [], precise: false }, view);
declare const overlay: CameraOverlay;
// @ts-expect-error ./camera-overlay: update takes a tracker snapshot (./camera)
overlay.update(42);
declare const destinations: OverlayDestinations;
// @ts-expect-error ./camera-overlay: the verifier reads a destination target (./destination)
destinations.get(42);
