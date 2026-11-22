// The qr_barcode_scanner example: scan a bundled image with a chosen profile
// and budget, then list every detection of the report, where the scanner
// measured it, and the scan's time.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_barcode_scanner/qr_barcode_scanner.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await QrcodeAiScanner.init(); // once, before any scan
  runApp(const DemoApp());
}

/// The bundled images, by asset path.
const samples = {
  'assets/mixed-code128-qr.png': 'QR + Code 128',
  'assets/sample_qr.png': 'QR code',
};

/// Each profile's default budget in milliseconds, which an empty budget keeps.
const defaultBudgets = {'fast': 800, 'frame': 80, 'full': 4000};

/// The two-dimensional symbologies, listed with a QR icon.
const matrixCodes = {
  Symbology.qrCode,
  Symbology.microQrCode,
  Symbology.rectangularMicroQrCode,
  Symbology.dataMatrix,
  Symbology.aztec,
  Symbology.maxiCode,
};

String formatName(Symbology symbology) => switch (symbology) {
  Symbology.qrCode => 'QR code',
  Symbology.microQrCode => 'Micro QR code',
  Symbology.rectangularMicroQrCode => 'rMQR code',
  Symbology.dataMatrix => 'Data Matrix',
  Symbology.aztec => 'Aztec',
  Symbology.pdf417 => 'PDF417',
  Symbology.maxiCode => 'MaxiCode',
  Symbology.ean13 => 'EAN-13',
  Symbology.ean8 => 'EAN-8',
  Symbology.upcA => 'UPC-A',
  Symbology.upcE => 'UPC-E',
  Symbology.code128 => 'Code 128',
  Symbology.code39 => 'Code 39',
  Symbology.code93 => 'Code 93',
  Symbology.codabar => 'Codabar',
  Symbology.itf => 'ITF',
  Symbology.dataBar => 'DataBar',
  Symbology.dataBarExpanded => 'DataBar Expanded',
  Symbology.telepen => 'Telepen',
  Symbology.unknown => 'Unknown format',
};

class DemoApp extends StatelessWidget {
  const DemoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'qr_barcode_scanner',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: Colors.indigo),
      home: const ScanPage(),
    );
  }
}

/// One finished scan: the report and what produced it.
class ScanResult {
  const ScanResult(this.report, this.profile, this.budgetMs, this.imageSize);

  final ScanReport report;
  final String profile;
  final int? budgetMs;

  /// The image's size in pixels, the space of the report's coordinates.
  final Size imageSize;
}

class ScanPage extends StatefulWidget {
  const ScanPage({super.key});

  @override
  State<ScanPage> createState() => _ScanPageState();
}

class _ScanPageState extends State<ScanPage> {
  final _budget = TextEditingController();
  String _asset = samples.keys.first;
  String _profile = 'full';
  bool _busy = false;
  ScanResult? _result;
  Object? _error;

  @override
  void dispose() {
    _budget.dispose();
    super.dispose();
  }

  Future<void> _scan() async {
    setState(() => _busy = true);
    final profile = _profile;
    // Empty keeps the profile's default budget; 0 is unbounded.
    final budgetMs = int.tryParse(_budget.text);
    ScanResult? result;
    Object? error;
    try {
      final bytes = (await rootBundle.load(_asset)).buffer.asUint8List();
      final image = await decodeImageFromList(bytes);
      final imageSize = Size(image.width.toDouble(), image.height.toDouble());
      image.dispose();
      final report = await QrcodeAiScanner.scan(
        bytes,
        profile: profile,
        budgetMs: budgetMs,
      );
      result = ScanResult(report, profile, budgetMs, imageSize);
    } catch (e) {
      // A scan fault is a String ending with its [QRS-xxx] code.
      error = e;
    }
    if (!mounted) return;
    setState(() {
      _busy = false;
      _result = result;
      _error = error;
    });
  }

  void _selectImage(Set<String> selection) {
    setState(() {
      _asset = selection.single;
      _result = null;
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final result = _result;
    final error = _error;
    return Scaffold(
      appBar: AppBar(title: const Text('qr_barcode_scanner')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          SegmentedButton<String>(
            segments: [
              for (final MapEntry(:key, :value) in samples.entries)
                ButtonSegment(value: key, label: Text(value)),
            ],
            selected: {_asset},
            onSelectionChanged: _busy ? null : _selectImage,
          ),
          const SizedBox(height: 12),
          _Preview(asset: _asset, result: result),
          const SizedBox(height: 12),
          SegmentedButton<String>(
            segments: [
              for (final profile in defaultBudgets.keys)
                ButtonSegment(value: profile, label: Text(profile)),
            ],
            selected: {_profile},
            onSelectionChanged: _busy
                ? null
                : (selection) => setState(() => _profile = selection.single),
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: TextField(
                  controller: _budget,
                  enabled: !_busy,
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  maxLength: 10,
                  decoration: InputDecoration(
                    border: const OutlineInputBorder(),
                    labelText: 'budgetMs',
                    floatingLabelBehavior: FloatingLabelBehavior.always,
                    hintText: 'default, ${defaultBudgets[_profile]} ms',
                    helperText: 'Empty: the profile default. 0: unbounded.',
                    // Wraps instead of truncating on a narrow phone.
                    helperMaxLines: 2,
                    counterText: '',
                  ),
                ),
              ),
              const SizedBox(width: 12),
              FilledButton.icon(
                key: const Key('scan'),
                style: FilledButton.styleFrom(minimumSize: const Size(0, 56)),
                onPressed: _busy ? null : _scan,
                icon: _busy
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.qr_code_scanner),
                label: const Text('Scan'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (error != null)
            Card.filled(
              color: Theme.of(context).colorScheme.errorContainer,
              child: ListTile(
                leading: const Icon(Icons.error_outline),
                title: Text('$error'),
              ),
            )
          else if (result != null) ...[
            _Summary(result),
            for (final (index, detection) in result.report.detections.indexed)
              _DetectionTile(
                detection,
                // The report's score judges its first detection only.
                score: index == 0 ? result.report.score : null,
              ),
          ],
        ],
      ),
    );
  }
}

/// The image, with what the scanner measured of each detection drawn on it.
class _Preview extends StatelessWidget {
  const _Preview({required this.asset, required this.result});

  final String asset;
  final ScanResult? result;

  @override
  Widget build(BuildContext context) {
    final result = this.result;
    final Widget image = result == null
        ? Image.asset(asset, fit: BoxFit.contain)
        : FittedBox(
            child: SizedBox.fromSize(
              size: result.imageSize,
              child: CustomPaint(
                foregroundPainter: _Outlines(
                  result.report.detections,
                  Theme.of(context).colorScheme.primary,
                ),
                child: Image.asset(asset, fit: BoxFit.fill),
              ),
            ),
          );
    return Card.outlined(
      color: Colors.white,
      clipBehavior: Clip.antiAlias,
      child: SizedBox(
        height: 170,
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Center(child: image),
        ),
      ),
    );
  }
}

/// Draws each occurrence's geometry in image pixels: the outline of a QR
/// code, the row a linear barcode was read on, or single points.
class _Outlines extends CustomPainter {
  const _Outlines(this.detections, this.color);

  final List<Detection> detections;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final width = size.shortestSide / 80;
    Paint stroke(Color strokeColor, double strokeWidth) => Paint()
      ..color = strokeColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final halo = stroke(Colors.white, width * 2.5);
    final line = stroke(color, width);
    for (final detection in detections) {
      for (final occurrence in detection.occurrences ?? const <Occurrence>[]) {
        final geometry = occurrence.geometry;
        final points = [for (final p in geometry.points) Offset(p.x, p.y)];
        switch (geometry.kind) {
          case GeometryKind.quad || GeometryKind.segment:
            final closed = geometry.kind == GeometryKind.quad;
            final path = Path()..addPolygon(points, closed);
            canvas
              ..drawPath(path, halo)
              ..drawPath(path, line);
          default:
            for (final point in points) {
              canvas
                ..drawCircle(point, width * 1.5, halo)
                ..drawCircle(point, width * 1.5, line);
            }
        }
      }
    }
  }

  @override
  bool shouldRepaint(_Outlines oldDelegate) =>
      oldDelegate.detections != detections || oldDelegate.color != color;
}

/// How the scan ran, in the report's own terms.
class _Summary extends StatelessWidget {
  const _Summary(this.result);

  final ScanResult result;

  @override
  Widget build(BuildContext context) {
    final trace = result.report.trace;
    final title = switch (result.report.detections.length) {
      0 => 'No code found',
      1 => '1 detection',
      final count => '$count detections',
    };
    final budget = switch (result.budgetMs) {
      null => 'default, ${defaultBudgets[result.profile]} ms',
      0 => '0, unbounded',
      final ms => '$ms ms',
    };
    final cut = switch (trace.budgetExhausted) {
      true => 'true: the budget cut the scan',
      false => 'false: the result is final',
      null => 'not reported',
    };
    return Card.filled(
      key: const Key('summary'),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            _Fact('profile', result.profile),
            _Fact('budgetMs', budget),
            _Fact('trace.totalMs', '${trace.totalMs.toStringAsFixed(1)} ms'),
            _Fact('trace.budgetExhausted', cut),
          ],
        ),
      ),
    );
  }
}

class _Fact extends StatelessWidget {
  const _Fact(this.name, this.value);

  final String name;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 150,
            child: Text(
              name,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          Expanded(child: Text(value, style: theme.textTheme.bodyMedium)),
        ],
      ),
    );
  }
}

/// One detection: its format, its text and, for the first, the score.
class _DetectionTile extends StatelessWidget {
  const _DetectionTile(this.detection, {this.score});

  final Detection detection;
  final Score? score;

  @override
  Widget build(BuildContext context) {
    final score = this.score;
    final textTheme = Theme.of(context).textTheme;
    final matrix = matrixCodes.contains(detection.symbology);
    return Card(
      child: ListTile(
        leading: Icon(matrix ? Icons.qr_code_2 : Icons.view_week),
        title: Text(formatName(detection.symbology)),
        subtitle: Text(detection.content.text),
        trailing: score == null
            ? null
            : Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('${score.value}/100', style: textTheme.titleMedium),
                  Text(score.grade.name, style: textTheme.labelSmall),
                ],
              ),
      ),
    );
  }
}
