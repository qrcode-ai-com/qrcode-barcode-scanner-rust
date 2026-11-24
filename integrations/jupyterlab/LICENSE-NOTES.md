# License notes

This folder builds one Python wheel, `jupyterlab-qrcode-barcode-scanner`, that holds the extension's
own code and the scanner engine it bundles. Both are under the MIT License, so its metadata declares
`MIT`. Two reader parts of the engine keep their Apache-2.0 notices.

## The extension's own code: MIT

The source in `src/`, `style/`, `scripts/`, `tests/` and `jupyterlab_qrcode_barcode_scanner/`, and
the JavaScript the build compiles from it into the labextension's `static/` folder, is available
under the MIT License in [LICENSE](LICENSE). The bundle also holds the small runtime helpers of
`css-loader` and `style-loader`, both MIT; `static/third-party-licenses.json` lists them with their
texts.

## The bundled scanner engine: MIT

The labextension's `static/*.wasm` file and the JavaScript glue bundled with it are the published
npm package `@qrcode-ai-com/qrcode-barcode-scanner-wasm@0.12.0`, unchanged. The module's SHA-256 is
`298fd9df8bc23639d00cb8effd5f1d1a742db2f53866868aec21723468f08868`; the build refuses any other.
That package is distributed under the MIT License. Two isolated parts of its reader derive from
rxing 0.9.3 and keep their original Apache-2.0 copyright and license notices. Its source is the
[`v0.12.0` tag](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/v0.12.0) of the
scanner repository, revision `897dd50cdf27cbde54d408bf65e1ca4622035d42`.

The build copies the package's own license files, unchanged, into `licenses/`:
`ENGINE-0.12.0-LICENSE`, `ENGINE-0.12.0-LICENSE-APACHE-2.0` and `ENGINE-0.12.0-THIRD-PARTY.md`,
with `ENGINE.json`, the record of the bundled module. The wheel carries them in its
`.dist-info/licenses/` folder, and the installed labextension carries them, with this file and
[LICENSE](LICENSE), in its own `licenses/` folder.

Whoever distributes the wheel keeps those notices with it. Engine 0.11.0 keeps its
AGPL-3.0-or-later license in its own published archives; no release of this extension bundles it.
