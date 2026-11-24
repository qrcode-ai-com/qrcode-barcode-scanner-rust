# License notes for the Canva app

The source in this folder is under the MIT License. The file built from it, `dist/app.js`, also
holds Canva's packages under Canva's own license. This note lists each part.

## The source in this folder

The app's own code and documents here (`src/`, `scripts/`, `test/`, `canva-app.json`, these notes,
the README and the listing kit) are under the MIT License, in [LICENSE](LICENSE). The two pictures
in `media/` are screenshots of the built app in its test page, under the same license.

This folder holds no Canva code, no engine and no other package. `npm ci` installs them from the
npm registry, at the exact versions of `package-lock.json`.

## The parts of `dist/app.js`

`scripts/build.mjs` bundles these parts into the one file Canva takes. The file ends with a comment
that holds the license text of every package in it, written from the files of each installed
package, and `build/build-receipt.json` lists them with their versions.

| Part | Version | License |
| --- | --- | --- |
| The app's own code, from `src/` | 0.1.1 | MIT |
| The scanner engine, `@qrcode-ai-com/qrcode-barcode-scanner-wasm`, inlined by [integrations/wasm-inline](../wasm-inline/) | 0.12.0 | MIT, with Apache-2.0 notices for the code derived from rxing |
| Canva's packages: `@canva/app-ui-kit`, `@canva/app-i18n-kit`, `@canva/design`, `@canva/asset`, `@canva/platform`, `@canva/intents` | as pinned | Canva's license, quoted below |
| React, React DOM, react-intl, FormatJS, MobX, Floating UI and their helpers | as pinned | MIT, BSD-3-Clause or 0BSD, each named in the file |

The engine module inside the file is the one of the published npm package, byte for byte: SHA-256
`298fd9df8bc23639d00cb8effd5f1d1a742db2f53866868aec21723468f08868`, built from revision
`897dd50cdf27cbde54d408bf65e1ca4622035d42` (tag `v0.12.0`) of this repository. Only its loader
changes, so that it takes the module from the file instead of fetching it. The engine's source is
that revision of <https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust>.

## Canva's license

Canva's packages carry the same license file. Its terms that matter here:

> 1. You must only use the Software Components and any Derivative on the Canva Platform.
> 2. You must only use the Software Components and any Derivative for the purpose of building or
>    updating Permitted Apps, and for no other purpose.
> 3. You must include a copy of this Licence in all copies of any Software Component and
>    Derivative.

A "Derivative" is any software that contains a Software Component, so `dist/app.js` is one. The
build keeps the license in the file, as term 3 asks. The tests run the built file in a test page
that stands in for Canva's panel, only to build and check this app, as Canva's own testing
documentation does with its packages.

## The engine and Canva's terms

Version 0.1.0 of the app was prepared with engine 0.11.0, under AGPL-3.0-or-later, and was never
submitted. AGPL-3.0 lets anyone who receives the combined work use, change and pass it on anywhere,
and Canva's terms 1 and 2 restrict the Canva parts of the same file to the Canva Platform, so that
file could not meet both sets of terms without an additional permission from the engine's copyright
holder.

Version 0.1.1 pins engine 0.12.0, built from the source that is under the MIT License since
14 November 2026, which is the second route this note described. The file combines the MIT code of
the app and the engine, the Apache-2.0 notices of rxing, Canva's license and the permissive licenses
above with no conflict, so no additional permission is needed.

`scripts/build.mjs` refuses an engine that is not MIT or does not ship the MIT text, so a future
engine under other terms needs the banner, the panel's license line in `src/messages.js` and this
file reviewed before it can be built.

This note describes the licenses as written. It is not legal advice.
