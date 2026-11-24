# Licence notes · Replicate model

This folder holds two kinds of material with different terms.

## The source in this folder: MIT

`run.py`, `cog.yaml`, `requirements.txt`, `.dockerignore`, the tests and the texts of this folder
are project-authored source under the [MIT License](LICENSE).

## The built image: MIT, with the notices of its parts

`cog build` and `cog push` make a container image that installs the published engine wheel
`qrcode-barcode-scanner` 0.12.0 from PyPI. That wheel is published under the **MIT License**, like
this folder. Its licence text ships inside the wheel, at
`qrcode_barcode_scanner-0.12.0.dist-info/licenses/LICENSE` in the image's Python `site-packages`.

Two reader parts of the engine derive from rxing 0.9.3 and keep their **Apache-2.0** notices. The
wheel does not carry those notices, so this folder does: `licenses/engine-0.12.0/THIRD-PARTY.md`
and `licenses/engine-0.12.0/LICENSE-APACHE-2.0` are copies of
`crates/qrcode-ai-scanner/THIRD-PARTY.md` and `crates/qrcode-ai-scanner/LICENSE-APACHE-2.0` at tag
`v0.12.0`, byte for byte (sha256 `542c2d99262bf4215de4de3d7e1a6e8b065b934b61ccb650dd82d2c4f96a71ab`
and `865b180617725f20be71aa305e82efaa8e56b3c6936d68089bc63cf91cb23087`). `cog build` copies them
into the image with `run.py`.

The image also holds Cog's own runtime (`cog` and `coglet` 0.23.1 from PyPI, Apache-2.0), the
Python 3.13 interpreter and the system packages of Cog's base image, each under its own licence.

Earlier preparations of this model pinned the engine wheel 0.11.0, which keeps the licence it
shipped with, AGPL-3.0-or-later. No version of them was pushed to Replicate.

## The source of the hosted model

On Replicate the model is a network service: people send it images and get reports back. The MIT
and Apache-2.0 licences do not require a source offer for that use, but the model page still links
the source of what runs:

- the engine 0.12.0: the tag
  [v0.12.0 of the engine repository](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/v0.12.0),
  commit `897dd50cdf27cbde54d408bf65e1ca4622035d42`, and the source distribution on
  [PyPI](https://pypi.org/project/qrcode-barcode-scanner/0.12.0/);
- the model: this folder, at the commit the version was pushed from,
  `https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/<commit>/integrations/replicate`.

[LISTING.md](LISTING.md) gives the exact text for the model page. When a new version is pushed,
its commit replaces `<commit>` in that text.

## More

The [licensing guide](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/blob/main/LICENSING.md)
explains the boundaries between the MIT source, the published archives and third-party
components, and the
[licence history](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/blob/main/docs/guides/license-history.mdx)
records earlier grants.
