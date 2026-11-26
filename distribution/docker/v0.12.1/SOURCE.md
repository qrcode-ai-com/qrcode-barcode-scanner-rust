# Scanner source

This image contains the unchanged Linux CLI from the public `v0.12.1` release
of [QR Code & Barcode Scanner](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust).
It does not rebuild Rust. `build-info.json` records its compiler (Rust 1.99.1),
locked dependencies, binary digest and original build producer. The image's
`org.opencontainers.image.revision` names immutable engine source
`5b2c580c78b0693e58909f889b66f24fc1c548b1`; the separate
`io.qrcode-ai.scanner.packaging-revision` names the reviewed image recipe revision.

`source/` contains the exact public CLI source archive and both published
crates, verified against `inputs.json`. The license, third-party notices, Rust
standard-library notice and original release source instructions are installed
alongside this file. The runtime base index is pinned by digest in the recipe;
image receipts identify its platform and every raw layer.

- [Immutable engine source](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/5b2c580c78b0693e58909f889b66f24fc1c548b1)
- [Public release and source archive](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/releases/tag/v0.12.1)
- [QR Code AI](https://qrcode-ai.com/)
- [QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner)
- [Barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner)

Core and CLI: MIT. Two isolated parts of the rxing adapter keep their Apache-2.0
notices (`LICENSE-APACHE-2.0`, `THIRD-PARTY.md`); linked crates keep theirs in
`THIRD-PARTY-LICENSES.txt`. No hosted service or runtime network is required.
