#!/usr/bin/env python3
"""Check the MIT source grant without relabelling published or third-party artifacts."""
import importlib.util
import json
from pathlib import Path
import re
import tomllib
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('readme_build', ROOT / 'scripts/build-readme-actions.py')
readmes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readmes)


def listed_readmes():
    """The committed list of maintained READMEs (scripts/maintained-readmes.txt)."""
    lines = (ROOT / 'scripts/maintained-readmes.txt').read_text().splitlines()
    return [line for line in lines if line and not line.startswith('#')]


class LicensingTests(unittest.TestCase):
    def test_owned_license_copies_are_standard_mit_with_requested_credits(self):
        license_text = (ROOT / 'LICENSE').read_text()
        self.assertTrue(license_text.startswith('MIT License\n'))
        for text in ('Thibaut Mélen & Nicolas Cella', 'QR Code AI', 'SuperNovae Studio',
                     'Permission is hereby granted, free of charge',
                     'The above copyright notice and this permission notice shall be included'):
            self.assertIn(text, license_text)
        paths = ['crates/qrcode-ai-scanner', 'crates/qrcode-ai-scanner-cli',
                 'crates/qrcode-ai-scanner-node', 'crates/qrcode-ai-scanner-wasm',
                 'crates/qrcode-ai-scanner-py', 'bindings/flutter', 'integrations/mcp',
                 'integrations/openclaw', 'skills/qrcode-barcode-scanner', 'distribution/aur',
                 'bindings/kotlin']
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual((ROOT / path / 'LICENSE').read_bytes(), license_text.encode())

    def test_authored_package_manifests_declare_mit(self):
        self.assertEqual(tomllib.loads((ROOT / 'Cargo.toml').read_text())['workspace']['package']['license'], 'MIT')
        for path in ('bindings/flutter/rust', 'crates/qrcode-ai-scanner-py', 'crates/qrcode-ai-scanner-uniffi', 'fuzz'):
            with self.subTest(path=path):
                self.assertEqual(tomllib.loads((ROOT / path / 'Cargo.toml').read_text())['package']['license'], 'MIT')
        for path in ('crates/qrcode-ai-scanner-node', 'integrations/mcp', 'integrations/openclaw', 'examples/web-vite', 'playground'):
            with self.subTest(path=path):
                self.assertEqual(json.loads((ROOT / path / 'package.json').read_text())['license'], 'MIT')
        self.assertEqual(tomllib.loads((ROOT / 'crates/qrcode-ai-scanner-py/pyproject.toml').read_text())['project']['license'], 'MIT')
        self.assertEqual(json.loads((ROOT / 'bindings/php/composer.json').read_text())['license'], 'MIT')
        project = ET.parse(ROOT / 'bindings/dotnet/src/QRCodeAI.QRCodeBarcodeScanner/QRCodeAI.QRCodeBarcodeScanner.csproj')
        self.assertEqual(project.find('.//PackageLicenseExpression').text, 'MIT')
        gemspec = (ROOT / 'bindings/ruby/qrcode-barcode-scanner.gemspec').read_text()
        self.assertIn("spec.license = 'MIT'", gemspec)
        gradle = (ROOT / 'bindings/kotlin/qrcodeaiscanner/build.gradle.kts').read_text()
        self.assertIn('name.set("MIT")', gradle)
        self.assertNotIn('name.set("AGPL-3.0-or-later")', gradle)
        self.assertIn('badge/MIT-', (ROOT / 'README.md').read_text())
        flutter_guide = (ROOT / 'docs/api/flutter.mdx').read_text()
        self.assertNotIn('almost always needs', flutter_guide)
        self.assertIn('Published `qr_barcode_scanner` 0.11.0 retains', flutter_guide)

    def test_all_maintained_readmes_distinguish_source_and_archive_licenses(self):
        paths = readmes.maintained_readmes()
        self.assertEqual(sorted(str(path) for path in paths), listed_readmes(),
                         'add or remove the README in scripts/maintained-readmes.txt (sorted)')
        for path in paths:
            with self.subTest(path=path):
                text = (ROOT / path).read_text()
                self.assertEqual(text.count('<!-- qrscan-source-license:v1 -->'), 1)
                self.assertIn('MIT License', text)
                self.assertIn('Published archives retain', text)
                self.assertIn('third-party', text)
                self.assertNotRegex(text, r'(?i)(needs|requires|need) (?:the |a )?commercial licen[cs]e')

    def test_licensing_guide_links_work_from_a_flat_cli_archive(self):
        guide = (ROOT / 'LICENSING.md').read_text()
        targets = re.findall(r'\]\(([^)]+)\)', guide)
        self.assertGreaterEqual(len(targets), 6)
        for target in targets:
            with self.subTest(target=target):
                if target.startswith('https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/blob/main/'):
                    self.assertTrue((ROOT / target.split('/blob/main/', 1)[1]).is_file())
                elif not target.startswith('https://'):
                    self.assertEqual(target, 'LICENSE', 'Only the adjacent LICENSE may be relative in the flat CLI archive')
        cli_readme = (ROOT / 'distribution/cli/README.md').read_text()
        self.assertNotIn('| `LICENSE` | the GNU Affero General Public License, version 3 |', cli_readme)
        self.assertIn('MIT in current source, AGPL-3.0-or-later in published 0.11.0 archives', cli_readme)

    def test_pinned_public_binaries_declare_the_license_of_the_version_they_pin(self):
        # Each Linux recipe wraps published CLI bytes, so it states the license of the release it
        # pins: AGPL-3.0-or-later up to 0.11.x, MIT from 0.12.0. The pin is read from the recipe.
        def pinned(relative, pattern):
            found = re.search(pattern, (ROOT / relative).read_text(), re.M)
            self.assertIsNotNone(found, f'{relative} does not pin a version')
            return found[1]

        def expected(version):
            major, minor, _ = (int(part) for part in version.split('.'))
            return 'MIT' if (major, minor) >= (0, 12) else 'AGPL-3.0-or-later'

        other = {'MIT': 'AGPL-3.0-or-later', 'AGPL-3.0-or-later': 'MIT'}
        license = expected(pinned('distribution/aur/PKGBUILD', r'^pkgver=(\S+)$'))
        self.assertIn(f"\nlicense=('{license}')\n", (ROOT / 'distribution/aur/PKGBUILD').read_text())
        license = expected(pinned('distribution/aur/.SRCINFO', r'^\tpkgver = (\S+)$'))
        self.assertIn(f'\tlicense = {license}\n', (ROOT / 'distribution/aur/.SRCINFO').read_text())
        appdata = ET.parse(ROOT / 'distribution/appimage/qrcode-barcode-scanner.appdata.xml')
        license = expected(appdata.find('.//releases/release').get('version'))
        self.assertEqual(appdata.find('.//project_license').text, license)
        self.assertEqual(expected(pinned('distribution/appimage/build.sh', r'^version=(\S+)$')), license)
        license = expected(pinned('distribution/rpm/qrcode-barcode-scanner.spec', r'^Version:\s+(\S+)$'))
        terms = pinned('distribution/rpm/qrcode-barcode-scanner.spec', r'^License:\s+(.+)$').split(' AND ')
        # The payload's third-party terms include MIT at every version; AGPL is only the scanner's.
        self.assertEqual(terms[0], license)
        self.assertEqual(terms.count('AGPL-3.0-or-later'), int(license == 'AGPL-3.0-or-later'))
        license = expected(pinned('distribution/debian/build.sh', r'^version=(\S+)$'))
        copyright = re.search(r"^cat >\"\$docdir/copyright\" <<'COPYRIGHT'\n(.*?)^COPYRIGHT$",
                              (ROOT / 'distribution/debian/build.sh').read_text(), re.M | re.S)[1]
        spelled = {'MIT': 'distributed under the MIT License', 'AGPL-3.0-or-later': 'distributed under AGPL-3.0-or-later'}
        self.assertIn(spelled[license], ' '.join(copyright.split()))
        self.assertNotIn(spelled[other[license]], ' '.join(copyright.split()))
        self.assertIn('retain upstream third-party notices and licenses', ' '.join(copyright.split()))
        self.assertIn('GNU AFFERO GENERAL PUBLIC LICENSE', (ROOT / 'distribution/releases/historical-agpl-3.0.txt').read_text())

    def test_upstream_notices_are_kept_separate(self):
        self.assertIn('Apache License', (ROOT / 'crates/qrcode-ai-scanner/LICENSE-APACHE-2.0').read_text())
        for path in ('crates/qrcode-ai-scanner/src/engine/multi_reader.rs',
                     'crates/qrcode-ai-scanner/src/engine/databar_expanded.rs'):
            text = (ROOT / path).read_text()
            self.assertIn('Licensed under the Apache License, Version 2.0', text)
            self.assertIn('Copyright', text)
        self.assertIn('MPL-2.0', (ROOT / 'deny.toml').read_text())
        self.assertNotIn('"AGPL-3.0-or-later"', (ROOT / 'deny.toml').read_text())


if __name__ == '__main__':
    unittest.main()
