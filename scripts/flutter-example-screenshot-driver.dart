// Host side of the Flutter example's pub.dev screenshot: flutter drive runs
// it beside scripts/flutter-example-screenshot.dart (read that file first).
// Each screenshot the device sends is written as NAME.png in the directory
// QRSCAN_SCREENSHOT_DIR names. The driver keeps no response data file.

import 'dart:io';

import 'package:integration_test/integration_test_driver_extended.dart';

Future<void> main() async {
  final directory = Directory(
    Platform.environment['QRSCAN_SCREENSHOT_DIR'] ?? 'screenshots',
  );
  await directory.create(recursive: true);
  await integrationDriver(
    responseDataCallback: null,
    onScreenshot: (name, image, [args]) async {
      final file = File('${directory.path}/$name.png');
      await file.writeAsBytes(image, flush: true);
      stdout.writeln('QRSCAN_SCREENSHOT ${file.path} ${image.length} bytes');
      return true;
    },
  );
}
