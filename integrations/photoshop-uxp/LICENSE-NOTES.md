# License notes for the Photoshop plugin

The source in this folder and the plugin built from it are both under the MIT License. This note
lists each part.

## The source in this folder

The plugin's own code and documents here (`src/`, `scripts/`, `test/`, these notes, the README and
the listing kit) are under the MIT License, in [LICENSE](LICENSE). The two pictures in `media/` are
made from screenshots of the built plugin in its test page, under the same license.

This folder holds no Adobe code and no engine. `npm ci` installs the engine and the build tools
from the npm registry, at the exact versions of `package-lock.json`.

## The parts of the plugin

`scripts/build.mjs` writes the plugin folder, `dist/`, and the same files in
`build/qrcode-barcode-scanner-photoshop-<version>.zip`. Its `NOTICE.md` lists them again inside the
plugin.

| Files in the plugin | What they are | Version | License |
| --- | --- | --- | --- |
| `manifest.json`, `index.html`, `styles.css`, `icons/` | the plugin's panel, copied from `src/`, and its icons drawn by `scripts/icons.mjs` | 0.1.1 | MIT, in `LICENSE-MIT.txt` |
| `index.js` | the plugin's code from `src/`, with the scanner engine `@qrcode-ai-com/qrcode-barcode-scanner-wasm` inlined by [integrations/wasm-inline](../wasm-inline/) | 0.1.1, engine 0.12.0 | MIT for the plugin's code and for the engine, with Apache-2.0 notices for the code derived from rxing |
| `LICENSE`, `LICENSE-APACHE-2.0`, `THIRD-PARTY.md` | the engine package's own license files, copied byte for byte | 0.12.0 | |
| `LICENSE-MIT.txt`, `NOTICE.md` | the MIT License of the plugin's code, and the list of parts with the engine's source revision | 0.1.1 | |

The plugin as a whole is distributed under the MIT License: the plugin's code and the engine 0.12.0
are both MIT, and two parts of the engine keep the Apache-2.0 notices of rxing. Version 0.1.0,
prepared with the engine 0.11.0 under AGPL-3.0-or-later, was never submitted.

The engine module inside `index.js` is the one of the published npm package, byte for byte:
SHA-256 `298fd9df8bc23639d00cb8effd5f1d1a742db2f53866868aec21723468f08868`, built from revision
`897dd50cdf27cbde54d408bf65e1ca4622035d42` (tag `v0.12.0`) of this repository. Only its loader changes, so that it
takes the module from the file instead of fetching it. The engine's source is that
revision of <https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust>, named in `NOTICE.md`.

The `TextDecoder`, `TextEncoder` and `performance` stand-ins in `src/polyfills.js` are this
plugin's own MIT code, written for it; no polyfill package is bundled.

## Adobe's code is not in the plugin

The plugin reaches Photoshop through `require('photoshop')` and `require('uxp')`, which Photoshop
answers when the panel runs. The build keeps both outside `index.js` and refuses any other
`require`. No Adobe code, SDK or sample is copied into this folder or the plugin. The way the
engine is started (the module inlined, then started synchronously) follows the pattern Adobe shows
in its `wasm-rust-sample`; the code here is written for this plugin.

So the plugin combines no code under another vendor's license, and the MIT License applies to it
as it is. Adobe's Developer Terms of Use, which the owner accepts before using the UXP Developer
Tool and the Developer Distribution portal, govern packaging and the Marketplace listing; they are
not a license of the plugin. As read on 10 November 2026, those terms forbid putting Adobe's
developer tools under AGPL-type terms (clause 6.6), which is why none of them is in the plugin, and
ask for an end-user license agreement (clause 6.15), which is why the listing gives a terms URL.

## If the engine's license changes

`scripts/build.mjs` refuses an engine that is not MIT or does not ship the MIT text, so a future
engine under other terms needs `banner()` and `notice()`, the footer of `src/index.html` and this
file reviewed before it can be built.

This note describes the licenses as written. It is not legal advice.
