# Scanner source

This image contains the unchanged Linux CLI from the public `v0.12.2` release
of [QR Code & Barcode Scanner](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust).
It does not rebuild Rust. `build-info.json` records its compiler (Rust 1.99.1),
locked dependencies, binary digest and original build producer. The image's
`org.opencontainers.image.revision` names immutable engine source
`d0fcf8a27410f5ee182aab6477624e3fc52c4aa5`; the separate
`io.qrcode-ai.scanner.packaging-revision` names the reviewed image recipe revision.

`source/` contains the exact public CLI source archive and both published
crates, verified against `inputs.json`. The license, third-party notices, Rust
standard-library notice and original release source instructions are installed
alongside this file.

## The base

Everything else in the image comes from its base, pinned by digest in the recipe:
`cgr.dev/chainguard/glibc-dynamic@sha256:a96ba3c8d5ffc646e1092c03d72000b5e2ccd9f6cda695d6342a0e31ce4d52ee`.
It is Chainguard's `glibc-dynamic` image, built from the Wolfi distribution. It holds
the C library and the compiler runtime the binary links, a certificate bundle and
the base layout: seven packages, listed in `inputs.json`, with no shell and no
package manager. Each package has an SPDX file under `/var/lib/db/sbom/`. That file
names the package's version, its license and the commit of its build definition.
For the six packages built from an upstream source it also names that source's
commit and the address of the archive it was built from, on `tarballs.cgr.dev`;
the seventh, the base layout, is made by its definition alone. Image receipts
identify the platform of the base and every raw layer.

- [Immutable engine source](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/d0fcf8a27410f5ee182aab6477624e3fc52c4aa5)
- [Public release and source archive](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/releases/tag/v0.12.2)
- [QR Code AI](https://qrcode-ai.com/)
- [QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner)
- [Barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner)

Core and CLI: MIT. Two isolated parts of the rxing adapter keep their Apache-2.0
notices (`LICENSE-APACHE-2.0`, `THIRD-PARTY.md`); linked crates keep theirs in
`THIRD-PARTY-LICENSES.txt`. The packages of the base keep their own licenses, named
in their SPDX files. No hosted service or runtime network is required.
