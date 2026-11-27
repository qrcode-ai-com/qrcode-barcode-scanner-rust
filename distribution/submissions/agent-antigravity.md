# Google Antigravity · plugin marketplace (agent-antigravity)

Prepared on 2026-11-21 for the owner to review and send. Nothing has been submitted.

Updated on 2026-11-24: the plugin's next release, `v0.3.1`, starts the MCP server 0.3.2 on the
MIT engine 0.12.0 and carries skill 0.2.1. The values to send below name it. Send them once
`v0.3.1` is on the plugin repository, and replace any commit named below with the one that tag
and `main` then carry (`git ls-remote https://github.com/qrcode-ai-com/qrcode-barcode-scanner-plugin`).
The checks under "What exists" are dated and ran on `v0.3.0`.

Updated on 2026-11-25: `v0.3.1` has been on the plugin repository since 24 November 2026. The
next release, `v0.3.2`, starts the MCP server 0.3.3, whose `scan_image` and `scan_file` default to
the `fast` profile, and keeps skill 0.2.1 and engine 0.12.0. The values to send below now name
`v0.3.2` and MCP 0.3.3: send them once `v0.3.2` is on the plugin repository, with the commit that
tag then carries.

Updated on 2026-11-27: `v0.3.2` has been on the plugin repository since 25 November 2026. The
next release, `v0.3.3`, starts the MCP server 0.3.4 and carries skill 0.2.2, both on the MIT
engine 0.12.1, whose reports carry score contract 6. The values to send below now name `v0.3.3`
and MCP 0.3.4: send them once `v0.3.3` is on the plugin repository, with the commit that tag then
carries.

## Live route

| Read (UTC) | URL | HTTP | Finding |
| --- | --- | --- | --- |
| 2026-11-21 07:21:56 | https://antigravity.google/docs/marketplace | 200 | Curated plugins; "Get your plugin in the marketplace: fill out this interest form" |
| 2026-11-21 07:34 | https://forms.gle/2EX5RFYPoJe1UgxR9 (Google Form "Antigravity Plugin Interest Form") | 200 | Fields listed below |

Mechanism: a Google Form. Google reviews the plugin and follows up. The docs ask for a plugin
validated with `agy plugin validate`.

## What exists

- The plugin repository has `.antigravity-plugin/plugin.json` and `mcp_config.json`, at tag
  `v0.3.0` and on `main` (`f37ab720795a7a15f27d5a00c302afdb321b9b3d`). The engine CI checks that
  manifest against `https://antigravity.google/schemas/v1/plugin.json`.
- On 2026-11-21, Antigravity CLI 1.1.8 validated a clone of tag `v0.3.0`
  (`dbfb75f0c7c45b2018edd613afcf24c629ac0a69`) with `agy plugin validate`: one skill and one MCP
  server processed. In a scratch home without sign-in, `agy plugin install` of that folder installed
  `qrcode-barcode-scanner` with the `qrscan` server pinned to the npm adapter 0.3.1, and
  `agy plugin uninstall qrcode-barcode-scanner` removed it. No scan ran: a scan needs a signed-in
  Antigravity session.

## Submission: the form, field by field

| Field | Value |
| --- | --- |
| Email | the owner's address |
| Company Name | the owner's company |
| Company Primary Website (Domain) | the owner's choice; the manifests use https://qrcode-ai.com/ |
| Primary Contact Name | the owner |
| Primary Contact Email | the owner's address |
| Public-facing support email or helpdesk URL | https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/issues |
| Plugin Description | Read QR codes and barcodes in local images. The plugin adds the QR Code & Barcode Scanner skill and a local MCP server pinned to version 0.3.4. Both return the engine's JSON report: the exact payload, the format of each code and, for QR codes, a scannability judgment. Scanning runs on the user's computer. Source: https://github.com/qrcode-ai-com/qrcode-barcode-scanner-plugin |
| Documentation URL | https://github.com/qrcode-ai-com/qrcode-barcode-scanner-plugin |

## The owner's next action

1. Optionally sign in to Antigravity and ask it to read a QR code image, to see a scan end to end.
2. Open https://forms.gle/2EX5RFYPoJe1UgxR9, fill in the company and contact fields (Google uses
   them to verify the organization), paste the plugin values above, and submit.
