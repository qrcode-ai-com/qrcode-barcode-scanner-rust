# WordPress Plugin Directory listing kit · QR Code & Barcode Scanner 0.1.1

Everything the owner needs to submit the plugin in this folder to the [WordPress Plugin Directory](https://wordpress.org/plugins/) and to publish it through its SVN repository. Nothing has been submitted or uploaded: the account, the submission, the review answers and the SVN commits are the owner's.

The directory reads the page of a plugin from its `readme.txt` and its SVN `assets/` folder. The submission form itself only takes the zip, so most values below are already in the files; they are listed here so they can be checked before the upload.

## The artifact

| | Value |
| --- | --- |
| File | `qrcode-barcode-scanner-0.1.1.zip` |
| Where | the `wordpress-plugin` artifact of the [integration-wordpress](../../.github/workflows/integration-wordpress.yml) run on the merged commit, or `build/` after `npm ci --ignore-scripts && npm run build` in this folder |
| SHA-256 | `05b0a84f65f4d5b93afdb3f6d6165ab6f19bee87c795a149a10194eb763f0f2c`, committed in [SHA256SUMS](SHA256SUMS) |
| Size | 1,019,655 bytes, 27 files, all under `qrcode-barcode-scanner/` (the directory's limit is 10 MB) |
| Engine | `@qrcode-ai-com/qrcode-barcode-scanner-wasm` 0.12.0, module SHA-256 `298fd9df8bc23639d00cb8effd5f1d1a742db2f53866868aec21723468f08868` |

To check a downloaded zip, in the folder that holds it: `shasum -a 256 qrcode-barcode-scanner-0.1.1.zip` on macOS or `sha256sum qrcode-barcode-scanner-0.1.1.zip` on Linux, and compare with the value above. A different value means a different file: do not upload it.

## The values

| Field | Value | Where it lives |
| --- | --- | --- |
| Plugin name | `QR Code & Barcode Scanner` | `Plugin Name` header, `readme.txt` title |
| Slug and address | `qrcode-barcode-scanner`, `https://wordpress.org/plugins/qrcode-barcode-scanner/` (expected, see below) | derived by the directory from the name |
| Short description | `Read QR codes and barcodes from an image or a photo, in the visitor's browser. The image is never uploaded. Open source.` (120 characters; the limit is 150) | `readme.txt` |
| Tags | `qr code`, `barcode`, `scanner`, `qr code reader`, `barcode reader` (the limit is 5) | `readme.txt` |
| Requires at least | `6.6` | header and `readme.txt` |
| Tested up to | `7.1` | `readme.txt` |
| Requires PHP | `7.4` | header and `readme.txt` |
| Stable tag | `0.1.1` | `readme.txt` |
| Version | `0.1.1` | header, `readme.txt`, `block.json` |
| License | `MIT`, `https://opensource.org/licenses/MIT` | header and `readme.txt` |
| Plugin URI | `https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust` | header |
| Author and Author URI | `QR Code AI`, `https://qrcode-ai.com/` | header |
| Text domain | `qrcode-barcode-scanner` | header, `block.json` |
| Contributors | none yet | `readme.txt` |

The slug `qrcode-barcode-scanner` was free on 21 November 2026: `https://api.wordpress.org/plugins/info/1.2/?action=plugin_information&request[slug]=qrcode-barcode-scanner` answered `Plugin not found`. It was checked, not reserved. The directory takes the slug from the plugin name at submission and gives `qrcode-barcode-scanner-2` if the name is taken by then. The slug can be changed once before the review starts, and never after approval.

`readme.txt` has no `Contributors` line because it needs the owner's WordPress.org username, which this repository does not know. It is optional. To show the owner as a contributor, add `Contributors: <username>` under the title in [plugin/readme.txt](plugin/readme.txt) in a pull request before the submission: the zip and its SHA-256 then change, and the workflow checks the new value.

The long description, the FAQ, the changelog and the screenshot captions are the sections of [plugin/readme.txt](plugin/readme.txt). The directory publishes them as they are.

## Images

The files of [directory-assets/](directory-assets/) go into the SVN `assets/` folder, not into the zip.

| File | Size | What it shows |
| --- | --- | --- |
| `icon-128x128.png` | 128 × 128 | three QR finder patterns and four barcode bars, the icon of the browser extension |
| `icon-256x256.png` | 256 × 256 | the same icon for high-density screens |
| `screenshot-1.png` | 1280 × 900 | caption 1: The scanner block on a page, after reading an image with a QR code and a Code 128 barcode. |
| `screenshot-2.png` | 1280 × 900 | caption 2: The block in the editor, with its three settings. |

The icons are drawn by `npm run assets`, and `npm test` checks that the committed files are the drawn ones. The screenshots come from `node test/playground.mjs --screenshots build/screenshots` on WordPress 7.1 with PHP 8.3, the run the workflow repeats; `npm run assets -- --screenshots build/screenshots` copies them here. There is no banner: `banner-772x250.png` and `banner-1544x500.png` are optional, and the page shows a plain header without them.

## Privacy answers

The directory has no privacy form; reviewers read the code and `readme.txt`. If a reviewer asks:

- Personal data collected: none. Data sent to the plugin's authors or any third party: none.
- Requests to other servers: none. The engine, the scripts and the stylesheet are files of the plugin, served by the site; the Playground test blocks outside requests and checks that the page makes none.
- Cookies, local storage, database writes, options, tables: none. The plugin keeps nothing when deleted.
- The image: read in the visitor's browser and discarded when the page closes; it is never uploaded to the site.
- The credit line with links to QR Code AI is off by default and shown only when the site owner turns it on (guideline 10).

The QR Code AI privacy, terms and support pages are planned at `https://qrcode-ai-com.github.io/privacy/`, `https://qrcode-ai-com.github.io/terms/` and `https://qrcode-ai-com.github.io/support/`. They are live after the owner's review; until then, do not cite them in a reviewer answer. Support for a directory plugin happens in its WordPress.org support forum, which the directory creates; the repository's issues at `https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/issues` take bug reports.

## Licence and compiled code: the verdict

Not blocked. The sources below were read live on 21 November 2026; the FSF licence list was read again on 24 November 2026 for the MIT and Apache-2.0 entries.

- [Detailed Plugin Guidelines](https://developer.wordpress.org/plugins/wordpress-org/detailed-plugin-guidelines/) (last updated 11 March 2026), guideline 1: "Although any GPL-compatible license is acceptable, using the same license as WordPress — 'GPLv2 or later' — is strongly recommended." The zip as a whole is MIT: the plugin's own files and the engine 0.12.0 alike, with Apache-2.0 notices for two parts of the engine derived from rxing.
- The FSF [license list](https://www.gnu.org/licenses/license-list.html) calls the Expat License, which "some people call" the MIT License, "a lax, permissive non-copyleft free software license, compatible with the GNU GPL", and the Apache License 2.0 "compatible with version 3 of the GNU GPL" but "not compatible with GPL version 2". A directory plugin is not required to be GPLv2-only, and this one contains no GPLv2-only code.
- The [Plugin Directory overview](https://developer.wordpress.org/plugins/wordpress-org/) says plugins "must be compatible with the GNU General Public License v2 or later"; the [2012 licensing update](https://make.wordpress.org/core/2012/04/30/the-plugin-directorys-licensing-guidelines-have-been-updated/) allows "code that is licensed under (or compatible with) version 3 of the GPL". [Common issues](https://developer.wordpress.org/plugins/wordpress-org/common-issues/) asks for "a sole license declared for your code": `MIT` in the header and in `readme.txt`.
- Plugin Check accepts the identifier: its licence pattern in `includes/Traits/License_Utils.php` (read on 24 November 2026) lists `MIT` among the GPL-compatible names. Plugin Check 2.2.0, run on version 0.1.0 of this zip in WordPress 7.1 on 21 November 2026, answered "No errors found." The workflow runs it again on every change, every category included, with warnings counted as failures.
- Guideline 4 forbids obfuscated code and asks for "public, maintained access to their source code and any build tools", for example "A link in the readme to the development location". The WebAssembly module is compiled, not obfuscated: `readme.txt` links its source at tag `v0.12.0` and the build script `scripts/build-wasm.sh`, and its `build-info.json` records the compiler, the settings and the module's SHA-256. The block's editor script ships with its source in `src/`. The words WebAssembly and wasm do not appear in the guidelines, and Plugin Check's file type check does not list `.wasm`. Directory plugins already ship `.wasm` files, for example [Squeeze](https://wordpress.org/plugins/squeeze/) and Code Block Pro.
- Guideline 7 (no contact with outside servers without consent) and guideline 8 (local JavaScript and CSS) hold: the test checks that no request leaves the site.

The residual risk is a reviewer who prefers GPLv2-or-later for the whole plugin. If one asks, the answer is the licences: the plugin and its engine are MIT, which the guidelines accept, and two parts of the engine keep the Apache-2.0 notices of rxing, which the 2012 update accepts as GPLv3-compatible. Version 0.1.0 of this kit, with the engine 0.11.0 under AGPL-3.0-or-later, was never submitted.

## The owner's steps

1. Sign in at `https://login.wordpress.org/` with the account that will own the plugin. Two-factor authentication is required for plugin owners and committers: turn it on in **Edit profile › Account & Security** first.
2. Open the merged pull request's **integration-wordpress** run in the repository's **Actions** tab. In **Artifacts**, download **wordpress-plugin** and unzip it. Take `qrcode-barcode-scanner-0.1.1.zip` and check its SHA-256 against the value above.
3. Open `https://wordpress.org/plugins/developers/add/`. Read the guidelines it links, choose the zip, tick the confirmations the form shows, and choose **Upload**. The form is shown only after sign-in, so its exact wording was not read for this kit. Check that the address it announces is `https://wordpress.org/plugins/qrcode-barcode-scanner/`.
4. Wait for the review email, between 1 and 10 days according to the page. Answer from the same account, by replying to the email. If the review asks how the plugin was made, say that it was developed with AI assistance. A requested change goes through a pull request in this repository; upload the new zip that its workflow builds.
5. After approval, the email gives the SVN address `https://plugins.svn.wordpress.org/qrcode-barcode-scanner/`. Set an SVN password in **Edit profile › Account & Security** if the email asks for one.
6. In an empty folder:

   ```sh
   svn checkout https://plugins.svn.wordpress.org/qrcode-barcode-scanner qrcode-barcode-scanner-svn
   cd qrcode-barcode-scanner-svn
   ```

   Unzip the verified zip elsewhere and copy the contents of its `qrcode-barcode-scanner/` folder into `trunk/`. Copy the four files of [directory-assets/](directory-assets/) into `assets/`. Then:

   ```sh
   svn add --force trunk assets
   svn propset svn:mime-type image/png assets/*.png
   svn cp trunk tags/0.1.1
   svn status
   svn commit -m "Release 0.1.1" --username <the owner's WordPress.org username>
   ```

   `svn status` must list only the plugin's 27 files, the four images and the tag. The SVN commit is a commit in WordPress.org's repository: it carries no studio trailer.
7. Once the directory has processed the commit, open `https://wordpress.org/plugins/qrcode-barcode-scanner/`. Check the name, the icon, the two screenshots and the version 0.1.1. On a test site, search **QR Code & Barcode Scanner** in **Plugins › Add New Plugin**, install it, add the block to a page and read an image.
8. Open a pull request here that changes the status paragraph of [README.md](README.md) to the directory address, with the date of the listing.

A new version follows the same path: bump the version in the plugin header, `readme.txt`, `block.json` and `package.json`, add a changelog entry, merge, then copy the new build into `trunk/` and `svn cp trunk tags/<version>`.

## Open points

- The QR Code AI pages `https://qrcode-ai.com/en-US/qr-code-scanner/integrations/wordpress` and `https://qrcode-ai.com/en-US/barcode-scanner/integrations/wordpress` that the README links are written by the website team; until they exist, the README is the reference.
- The plugin has been tested on WordPress Playground in Playwright's Chromium only. A manual check on a hosted site, and in Firefox and Safari, is worth doing before the submission.
