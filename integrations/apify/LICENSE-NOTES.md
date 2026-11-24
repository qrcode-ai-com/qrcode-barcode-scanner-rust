# License notes for the Actor image

The files of this folder (the `qrscan_actor` package, `Dockerfile`, `requirements.txt`, the
`.actor` definition, the tests and these notes) are project source of the QR Code & Barcode
Scanner, under the MIT License in `LICENSE`.

The image Apify builds from them is not only that source. It also holds:

| Part | Version | License | Where its text is in the image |
| --- | --- | --- | --- |
| `qrcode-barcode-scanner`, the scanner engine wheel from PyPI | 0.12.0 | MIT | `qrcode_barcode_scanner-0.12.0.dist-info/licenses/LICENSE` in the image's `site-packages` |
| the reader parts the engine derives from rxing 0.9.3 | as in engine 0.12.0 | Apache-2.0 | `/usr/src/app/licenses/engine-0.12.0/` |
| the Apify SDK, HTTPX and their dependencies | as pinned in `requirements.txt` and resolved by `pip` | their own licenses | each package's `dist-info` folder in `site-packages` |
| Python and the base of the `apify/actor-python:3.12` image | as that tag resolves at build time | their own licenses | as that base image ships them |

The engine 0.12.0 is published under the MIT License, like the Actor's own files, so the
`Dockerfile` labels the image `MIT`. Two reader parts of the engine keep their Apache-2.0 notices,
which the image carries, and the other parts keep their own licenses. Earlier preparations of this
Actor installed the engine 0.11.0, which keeps the license it shipped with, AGPL-3.0-or-later; no
image of them was published.

## Corresponding source

- The engine 0.12.0: tag `v0.12.0` of
  [qrcode-ai-com/qrcode-barcode-scanner-rust](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/v0.12.0),
  commit `897dd50cdf27cbde54d408bf65e1ca4622035d42`. The wheel was built from it.
- The Actor: the folder `integrations/apify` of the same repository, at the commit the Actor's
  Git source names when it is built.

`licenses/engine-0.12.0/THIRD-PARTY.md` and `LICENSE-APACHE-2.0` are copies of
`crates/qrcode-ai-scanner/THIRD-PARTY.md` and `crates/qrcode-ai-scanner/LICENSE-APACHE-2.0` at tag
`v0.12.0`, byte for byte (sha256 `542c2d99262bf4215de4de3d7e1a6e8b065b934b61ccb650dd82d2c4f96a71ab`
and `865b180617725f20be71aa305e82efaa8e56b3c6936d68089bc63cf91cb23087`).
