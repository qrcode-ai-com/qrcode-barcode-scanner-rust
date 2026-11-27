# Changelog

## 0.1.2

- Bundles the published `@qrcode-ai-com/qrcode-barcode-scanner-wasm` 0.12.1 module instead of
  0.12.0. Its SHA-256 is the one the engine's v0.12.1 release records. It reads the same 19
  formats, and the output channel now names scanner 0.12.1.
- Engine 0.12.1 scores with contract 6 instead of 5: the report's `versions.score_contract` is 6.
  The engine is MIT, like 0.12.0, and ships the same license files.
- The commands, menus and settings are unchanged.

## 0.1.1

- Bundles the published `@qrcode-ai-com/qrcode-barcode-scanner-wasm` 0.12.0 module instead of
  0.11.0. Its SHA-256 is the one the engine's v0.12.0 release records. It reads the same 19
  formats, and the output channel now names scanner 0.12.0.
- The engine 0.12.0 is under the MIT License, like the extension's own code, so the manifest's
  license is now `MIT` instead of `MIT AND AGPL-3.0-or-later`. `LICENSE.md` holds the MIT text
  of the extension and of the engine; two reader parts of the engine keep their Apache-2.0
  notices in `dist/engine/`. Version 0.1.0 keeps engine 0.11.0 and its AGPL-3.0-or-later license.
- The commands, menus and settings are unchanged.

## 0.1.0

- First version of the extension. The command **Scan QR codes and barcodes** reads PNG, JPEG,
  WebP, GIF and uncompressed BMP files from the Explorer, the editor title or the Command
  Palette, writes each result and the engine report to an output channel, and offers each
  decoded text to copy.
- Settings `qrcodeBarcodeScanner.profile` (`full`, `fast` or `frame`) and
  `qrcodeBarcodeScanner.budgetMs`.
- Bundles the published `@qrcode-ai-com/qrcode-barcode-scanner-wasm` 0.11.0 module. Scans run
  locally in a worker thread, without network access.
