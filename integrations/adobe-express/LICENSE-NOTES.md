# License notes for the Adobe Express add-on

The source in this folder and the package built from it are both under the MIT License. This note
lists each part.

## The source in this folder

The add-on's own code and documents here (`src/`, `scripts/`, `test/`, these notes, the README and
the listing kit) are under the MIT License, in [LICENSE](LICENSE). The two pictures in `media/` are
screenshots of the built add-on in its test page, under the same license.

This folder holds no Adobe code and no engine. `npm ci` installs the engine and the build tools
from the npm registry, at the exact versions of `package-lock.json`.

## The parts of the package

`scripts/build.mjs` writes the package, `build/qrcode-barcode-scanner-adobe-express-<version>.zip`,
from these parts. Its `NOTICE.md` lists them again inside the package.

| Files in the package | What they are | Version | License |
| --- | --- | --- | --- |
| `manifest.json`, `index.html`, `index.js`, `image.js`, `results.js`, `styles.css` | the add-on's panel, copied from `src/` | 0.1.1 | MIT, in `LICENSE-MIT.txt` |
| `scanner-worker.js` | the add-on's worker code, from `src/worker.js`, with the scanner engine `@qrcode-ai-com/qrcode-barcode-scanner-wasm` inlined by [integrations/wasm-inline](../wasm-inline/) | 0.1.1, engine 0.12.0 | MIT for the worker code and for the engine, with Apache-2.0 notices for the code derived from rxing |
| `LICENSE`, `LICENSE-APACHE-2.0`, `THIRD-PARTY.md` | the engine package's own license files, copied byte for byte | 0.12.0 | |
| `LICENSE-MIT.txt`, `NOTICE.md` | the MIT License of the add-on's code, and the list of parts with the engine's source revision | 0.1.1 | |

The package as a whole is distributed under the MIT License: the add-on's code and the engine
0.12.0 are both MIT, and two parts of the engine keep the Apache-2.0 notices of rxing. Version 0.1.0,
prepared with the engine 0.11.0 under AGPL-3.0-or-later, was never submitted.

The engine module inside `scanner-worker.js` is the one of the published npm package, byte for byte:
SHA-256 `298fd9df8bc23639d00cb8effd5f1d1a742db2f53866868aec21723468f08868`, built from revision
`897dd50cdf27cbde54d408bf65e1ca4622035d42` (tag `v0.12.0`) of this repository. Only its loader changes, so that it
takes the module from the file instead of fetching it. The engine's source is that
revision of <https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust>, named in `NOTICE.md`.

## Adobe's code is not in the package

The panel imports the Adobe Express add-on SDK from `https://express.adobe.com/static/add-on-sdk/sdk.js`
when it runs, as Adobe's documentation shows. The SDK is Adobe's, served by Adobe, and no copy of
it is in this folder or in the package. The build checks that the panel names no other remote
address.

So the package combines no code under another vendor's license, and the MIT License applies to it
as it is. Adobe's developer terms, which the owner accepts in the Adobe Express distribution flow,
govern the listing and the use of the SDK; they are not a license of the package.

## If the engine's license changes

`scripts/build.mjs` refuses an engine that is not MIT or does not ship the MIT text, so a future
engine under other terms needs `notice()`, the footer of `src/index.html` and this file reviewed
before it can be built.

This note describes the licenses as written. It is not legal advice.
