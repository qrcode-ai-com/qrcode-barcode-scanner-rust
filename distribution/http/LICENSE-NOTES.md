# License notes for the HTTP service image

The files of this folder (`server.mjs`, `Dockerfile`, `package.json`, the tests and these notes)
are project source of the QR Code & Barcode Scanner, under the MIT License in `LICENSE`.

The image built from them is not only that source. It also holds:

| Part | Version | License | Where its text is in the image |
| --- | --- | --- | --- |
| `@qrcode-ai-com/qrcode-barcode-scanner`, the scanner engine for Node.js | 0.12.2 | MIT | `/opt/qrscan-http/node_modules/@qrcode-ai-com/qrcode-barcode-scanner/LICENSE` |
| its native package for the image's platform (`linux-x64-gnu` or `linux-arm64-gnu`) | 0.12.2 | MIT | `LICENSE` in that package's folder under `node_modules/@qrcode-ai-com/` |
| the reader parts the engine derives from rxing 0.9.3 | as in engine 0.12.2 | Apache-2.0 | `/opt/qrscan-http/licenses/engine-0.12.2/` |
| Node.js 26 and the Wolfi packages of Chainguard's `cgr.dev/chainguard/node` image | as pinned in `Dockerfile` | their own licenses | as that base image records them: the SPDX document of each package, under `/var/lib/db/sbom`, names its license |

The engine 0.12.2 is published under the MIT License, like this folder's files, so the image's
`org.opencontainers.image.licenses` label is `MIT`. Two isolated reader parts of the engine derive
from rxing and keep their Apache-2.0 notice; the npm packages ship only the MIT `LICENSE`, so the
image carries those notices itself, in `licenses/engine-0.12.2/`. Node.js and the packages of the
Chainguard base keep their own licenses.

Version 0.1.3 of the service ran the engine 0.12.1, on Node.js 22 and the Debian base of the
`node:22.22.2-bookworm-slim` image. Versions 0.1.1 and 0.1.2 ran the engine 0.12.0. Both engines
are MIT too. Version 0.1.0 of the service ran the engine 0.11.0, which was published under
AGPL-3.0-or-later and keeps that license; an image built from version 0.1.0 is therefore
AGPL-3.0-or-later as a whole.

## Source

- The engine 0.12.2: tag `v0.12.2` of
  [qrcode-ai-com/qrcode-barcode-scanner-rust](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/v0.12.2),
  commit `d0fcf8a27410f5ee182aab6477624e3fc52c4aa5`. The npm packages were built from it.
- The service: the folder `distribution/http` of the same repository, at the commit that
  `SOURCE.json` names next to `server.mjs` in the image.

The service names its source on every answer: the `X-Source-Code` header and the `source` field of
`GET /` name the service's source at its commit and the engine's source at `v0.12.2`. If you
change the service and run it for others, point those links at your own source.

`licenses/engine-0.12.2/THIRD-PARTY.md` and `LICENSE-APACHE-2.0` are copies of
`crates/qrcode-ai-scanner/THIRD-PARTY.md` and `crates/qrcode-ai-scanner/LICENSE-APACHE-2.0` at tag
`v0.12.2`, byte for byte.
