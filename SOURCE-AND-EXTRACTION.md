# Scanner source and package identity

**QR Code & Barcode Scanner** is one Rust engine for QR codes, barcodes and
other supported 2D formats. Its runtime bindings share the versioned scan-report
contract. QR and barcode use cases do not require separate engine repositories.

The source repository is
[`qrcode-ai-com/qrcode-barcode-scanner-rust`](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust).
The repository retains its identity, commits and tags across renames.

## Package names

Releases through 0.10.x keep their `qrcode-ai-scanner` names and stay available
under them. From 0.11.0 the packages carry the `qrcode-barcode-scanner` family
names: `qrcode-barcode-scanner` and `qrcode-barcode-scanner-cli` on crates.io,
`qrcode-barcode-scanner` on PyPI, and `@qrcode-ai-com/qrcode-barcode-scanner`,
its six platform packages and `@qrcode-ai-com/qrcode-barcode-scanner-wasm` on
npm. These five runtime entry points are public in 0.12.0, as are the prebuilt
CLI archives in the [v0.12.0 release](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/releases/tag/v0.12.0).
The six native npm platform packages are automatic optional dependencies of the
Node parent, not six additional SDKs. The browser package ships one portable
WASM module. No 0.12.0 package uses a former name or an alias/wrapper package;
`qrscan` remains the CLI command.

Public Flutter package [`qr_barcode_scanner` 0.12.0](https://pub.dev/packages/qr_barcode_scanner/versions/0.12.0)
is published under verified publisher `qrcode-ai.com`; an app build links its
signed precompiled native library when cargokit may use one and otherwise
compiles its Rust core. The [Flutter guide](docs/api/flutter.mdx) records the
Android and iOS builds of its tag, with and without Rust, and the earlier
emulator and simulator consumer run of the previous archive.
Publication does not establish general device qualification. Kotlin/JitPack is
unqualified. The Swift package `QRCodeBarcodeScanner` 0.12.0 is public from its
own repository, [`qrcode-ai-com/qrcode-barcode-scanner-swift`](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-swift),
whose tag `0.12.0` pins the xcframework of the release `swift-v0.12.0` by its
checksum: SwiftPM adds it by repository URL. A macOS SwiftPM consumer of that tag
scanned a QR code; a scan on an iOS simulator or device is not qualified. It is
listed on the [Swift Package Index](https://swiftpackageindex.com/qrcode-ai-com/qrcode-barcode-scanner-swift). JSR has no qualified
publication here. The public ClawHub
skill 0.2.1 and OpenClaw bundle 0.2.2 run the MIT engine 0.12.0. The MCP adapter is 0.3.3
on npm, on the MIT engine 0.12.0, and the Official MCP Registry lists 0.3.3. The
skill 0.2.1 is also published as files on the release `agents-v0.3.3`, and the MCP Bundle 0.3.3
on the release `mcpb-v0.3.3`. Homebrew and GHCR distribute the CLI
0.12.0. See the [distribution guide](distribution/README.md) for coordinates
and platform evidence. The initial engine npm uploads were manual. The adapter
0.3.1, 0.3.2 and 0.3.3 and PyPI uploads have their own trusted publishing evidence.

These spellings stay as they were in 0.11; none of them is an install name:

- the repository directories: `crates/qrcode-ai-scanner*`,
  `bindings/kotlin/qrcodeaiscanner` and `bindings/swift/Sources/QrcodeAiScanner`;
- the Cargo packages that are never published: `qrcode-ai-scanner-node`,
  `qrcode-ai-scanner-wasm`, `qrcode-ai-scanner-uniffi` and `qrcode-ai-scanner-fuzz`;
- the UniFFI, Kotlin, Swift and Android module names: the UniFFI library
  `qrcode_ai_scanner_uniffi`, the Kotlin package `uniffi.qrcode_ai_scanner_uniffi`,
  the Gradle module `:qrcodeaiscanner`, the Swift package `QrcodeAiScanner` with
  its `QrcodeAiScannerFFI` binary target, and the Android namespaces of the
  Kotlin and Flutter bindings;
- the platform identifiers of the Flutter example app.

Install from the coordinates in [README.md](README.md), the documentation and
the [distribution guide](distribution/README.md), not from the repository name.
The [migration guide](docs/guides/migrate-to-qrcode-barcode-scanner.mdx) maps
each former name to its new one.

## Development and delivery

1. Implement and test scanner changes in this repository.
2. Select an exact source revision and build the affected runtime artifacts.
3. Qualify the actual packages in clean consumers, including platform-specific
   requirements. A source tag or workspace test alone does not qualify a binding.
4. Publish through [RELEASING.md](RELEASING.md), then verify each artifact's
   version, source revision, installation and supported-platform evidence.

Preserve exact content, report/schema compatibility, advanced QR recovery,
scoring semantics and resource contracts. A repository rename does not release
or retire a package, rename its registry entry, or change its license. Published
artifact hashes, source snapshots, schema identifiers and dated verification
receipts retain their original identities.

QR Code AI is the application consuming this scanner; its creation engine has
its own source and release process. A mobile scanner binding is a developer
artifact, not an application-store release. See [LICENSING.md](LICENSING.md) for
this scanner's licensing terms.

The filename is retained for existing links. Earlier two-engine extraction
proposals are superseded; no extraction or alias/wrapper package is required.
Private operating plans and account data do not belong in this repository or
its distributable archives.

## QR Code AI

| | QR codes | Barcodes |
| --- | --- | --- |
| **Try the scanner live** | [QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner) | [Barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner) |
| **SDK guides** | [QR code scanner SDKs](https://qrcode-ai.com/en-US/qr-code-scanner/sdk) | [Barcode scanner SDKs](https://qrcode-ai.com/en-US/barcode-scanner/sdk) |
| **Create a code** | [QR code generator](https://qrcode-ai.com/en-US/qr-code-generator) | [Barcode generator](https://qrcode-ai.com/en-US/barcode-generator) |

## Source license amendment · 14 November 2026

The owner explicitly chose MIT for current project-authored scanner source and
future qualified releases. [LICENSING.md](LICENSING.md) defines the scope and
third-party boundaries. Existing published archives, their license metadata and
frozen release evidence remain version-specific. No tag, publication or service
license is changed by this source decision.
