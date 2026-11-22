// Build the UNSIGNED precompiled binaries cargokit downloads for the Flutter
// package, from a staged package (scripts/stage-flutter-package.py).
//
// It holds no key: signing, the `precompiled_<crate hash>` release and its
// upload are the owner's step on their own machine
// (scripts/flutter-precompiled.py publish). This file reuses cargokit's own
// classes from the staged package, so the crate hash, the target list, the
// artifact names and the Android build environment are the ones a consuming
// app computes:
//
//   (cd <package>/cargokit/build_tool && dart pub get --enforce-lockfile)
//   dart --packages=<package>/cargokit/build_tool/.dart_tool/package_config.json \
//     scripts/flutter-precompiled-build.dart hash --manifest-dir <package>/rust
//   dart --packages=... scripts/flutter-precompiled-build.dart build \
//     --manifest-dir <package>/rust --out DIR --toolchain "$RUST_TOOLCHAIN" \
//     --target aarch64-linux-android [--target ...] \
//     [--android-sdk DIR --android-ndk VERSION --android-min-sdk 21]
//
// `build` writes `<rust target>_<artifact>` (PrecompileBinaries.fileName) for
// each target and manifest.json: the crate hash, the package, the toolchain,
// the targets and the sha256 of every file.

import 'dart:convert';
import 'dart:io';

import 'package:build_tool/src/android_environment.dart';
import 'package:build_tool/src/artifacts_provider.dart';
import 'package:build_tool/src/cargo.dart';
import 'package:build_tool/src/crate_hash.dart';
import 'package:build_tool/src/precompile_binaries.dart';
import 'package:build_tool/src/target.dart';
import 'package:crypto/crypto.dart';
import 'package:path/path.dart' as path;

Never fail(String message) {
  stderr.writeln('flutter-precompiled-build: $message');
  exit(1);
}

/// `--name value` options, repeatable ones collected in order.
Map<String, List<String>> parseOptions(List<String> args, Set<String> known) {
  final options = <String, List<String>>{};
  for (var i = 0; i < args.length; i += 2) {
    final name = args[i];
    if (!name.startsWith('--') || !known.contains(name.substring(2))) {
      fail('unknown option $name (known: ${known.join(', ')})');
    }
    if (i + 1 >= args.length) {
      fail('$name needs a value');
    }
    options.putIfAbsent(name.substring(2), () => []).add(args[i + 1]);
  }
  return options;
}

String one(Map<String, List<String>> options, String name) {
  final values = options[name];
  if (values == null || values.length != 1) {
    fail('--$name is required once');
  }
  return values.single;
}

String? optional(Map<String, List<String>> options, String name) {
  final values = options[name];
  if (values == null) {
    return null;
  }
  if (values.length != 1) {
    fail('--$name is given more than once');
  }
  return values.single;
}

/// The iOS deployment target the podspec declares: Xcode exports it to the
/// cargo build a consuming app runs, so the precompiled library carries it too.
String iosDeploymentTarget(String manifestDir) {
  final podspec =
      File(path.join(manifestDir, '..', 'ios', 'qr_barcode_scanner.podspec'));
  final found = RegExp(r"^\s*s\.platform\s*=\s*:ios,\s*'([0-9.]+)'",
          multiLine: true)
      .firstMatch(podspec.readAsStringSync());
  if (found == null) {
    fail('cannot read the iOS platform of ${podspec.path}');
  }
  return found.group(1)!;
}

Future<void> build(Map<String, List<String>> options) async {
  final manifestDir = path.canonicalize(one(options, 'manifest-dir'));
  final out = Directory(one(options, 'out'));
  final toolchain = one(options, 'toolchain');
  final triples = options['target'] ?? [];
  if (triples.isEmpty) {
    fail('give at least one --target');
  }
  if (out.existsSync() && out.listSync().isNotEmpty) {
    fail('${out.path} is not empty');
  }
  out.createSync(recursive: true);
  final crate = CrateInfo.load(manifestDir);
  final hash = CrateHash.compute(manifestDir);
  final temp = Directory.systemTemp.createTempSync('precompiled_');
  final files = <String, String>{};
  final targets = <String>[];
  for (final triple in triples) {
    final target = Target.forRustTriple(triple);
    if (target == null || (target.android == null && target.darwinPlatform == null)) {
      fail('$triple is not an Android or Apple target cargokit knows');
    }
    if (targets.contains(triple)) {
      fail('$triple is given twice');
    }
    targets.add(triple);
    final environment = <String, String>{};
    if (target.android != null) {
      environment.addAll(await AndroidEnvironment(
        sdkPath: one(options, 'android-sdk'),
        ndkVersion: one(options, 'android-ndk'),
        minSdkVersion: int.parse(one(options, 'android-min-sdk')),
        targetTempDir: temp.path,
        target: target,
      ).buildEnvironment());
    } else {
      environment['IPHONEOS_DEPLOYMENT_TARGET'] =
          optional(options, 'ios-deployment-target') ?? iosDeploymentTarget(manifestDir);
    }
    // cargokit's RustBuilder runs `rustup run stable cargo build` with these
    // arguments. The release binaries are built with the repository's pinned
    // toolchain instead, and --locked: the staged Cargo.lock is the
    // candidate's.
    final arguments = [
      'run',
      toolchain,
      'cargo',
      'build',
      '--locked',
      '--manifest-path',
      path.join(manifestDir, 'Cargo.toml'),
      '-p',
      crate.packageName,
      '--release',
      '--target',
      triple,
      '--target-dir',
      temp.path,
    ];
    stdout.writeln('rustup ${arguments.join(' ')}');
    final process = await Process.start('rustup', arguments,
        environment: environment, mode: ProcessStartMode.inheritStdio);
    final code = await process.exitCode;
    if (code != 0) {
      fail('cargo build for $triple exited $code');
    }
    for (final name in getArtifactNames(
        target: target, libraryName: crate.packageName, remote: true)) {
      final built = File(path.join(temp.path, triple, 'release', name));
      if (!built.existsSync()) {
        fail('missing artifact ${built.path}');
      }
      final fileName = PrecompileBinaries.fileName(target, name);
      final bytes = built.readAsBytesSync();
      File(path.join(out.path, fileName)).writeAsBytesSync(bytes);
      files[fileName] = sha256.convert(bytes).toString();
      stdout.writeln('$fileName ${files[fileName]} ${bytes.length} bytes');
    }
  }
  final manifest = {
    'crate_hash': hash,
    'package': crate.packageName,
    'toolchain': toolchain,
    'targets': targets,
    'files': Map.fromEntries(
        files.entries.toList()..sort((a, b) => a.key.compareTo(b.key))),
  };
  File(path.join(out.path, 'manifest.json')).writeAsStringSync(
      '${const JsonEncoder.withIndent('  ').convert(manifest)}\n');
  stdout.writeln('crate hash $hash');
}

Future<void> main(List<String> args) async {
  if (args.isEmpty) {
    fail('usage: hash --manifest-dir DIR | build --manifest-dir DIR --out DIR '
        '--toolchain X --target T [--target T] [--android-sdk DIR '
        '--android-ndk VERSION --android-min-sdk N] [--ios-deployment-target X]');
  }
  final rest = args.sublist(1);
  if (args.first == 'hash') {
    final options = parseOptions(rest, {'manifest-dir'});
    stdout.writeln(
        CrateHash.compute(path.canonicalize(one(options, 'manifest-dir'))));
  } else if (args.first == 'build') {
    await build(parseOptions(rest, {
      'manifest-dir',
      'out',
      'toolchain',
      'target',
      'android-sdk',
      'android-ndk',
      'android-min-sdk',
      'ios-deployment-target',
    }));
  } else {
    fail('unknown command ${args.first}');
  }
}
