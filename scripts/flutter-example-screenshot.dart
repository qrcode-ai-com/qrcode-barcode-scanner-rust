// The pub.dev screenshot of the Flutter example, on a device or simulator.
//
// flutter-qualification.yml copies this file into the staged example as
// integration_test/screenshot.dart, and its driver,
// scripts/flutter-example-screenshot-driver.dart, as
// test_driver/screenshot_driver.dart, then runs, from the example:
//
//   flutter drive -d DEVICE --driver test_driver/screenshot_driver.dart \
//     --target integration_test/screenshot.dart
//
// The app scans the mixed QR/Code 128 fixture with its defaults (the full
// profile under its default budget); once the result list shows both codes,
// the screenshot goes to the driver, which writes it. Both files stay outside
// bindings/flutter, so the pub.dev archive does not ship them, and the
// example's own integration tests do not run this one.

import 'dart:io' show Platform;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:qr_barcode_scanner/qr_barcode_scanner.dart';
import 'package:qrcode_ai_scanner_example/main.dart';

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('the example lists both codes of the mixed fixture', (
    tester,
  ) async {
    await QrcodeAiScanner.init();
    await tester.pumpWidget(const DemoApp());
    await tester.tap(find.byKey(const Key('scan')));
    // The scan runs on the Rust worker pool: wait for its report in real
    // time, a frame every 200 ms.
    final deadline = DateTime.now().add(const Duration(minutes: 2));
    while (find.byKey(const Key('summary')).evaluate().isEmpty) {
      if (DateTime.now().isAfter(deadline)) {
        fail('no scan report on screen after 2 minutes');
      }
      await tester.pump(const Duration(milliseconds: 200));
    }
    expect(find.text('STOCK-4827'), findsOneWidget);
    expect(find.text('https://qrc-ai.com/76xMa'), findsOneWidget);
    // Android renders to a surface the plugin cannot read until it is
    // converted to an image; elsewhere this is a no-op.
    await binding.convertFlutterSurfaceToImage();
    await tester.pumpAndSettle();
    await binding.takeScreenshot('example-${Platform.operatingSystem}');
  });
}
