# Devin · CognitionAI/devin-marketplace (agent-devin)

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
| 2026-11-21 07:22:12 | https://docs.devin.ai/cli/extensibility/plugins/overview | 200 | Plugins use `.devin-plugin/plugin.json`; Devin falls back to `.claude-plugin/plugin.json` |
| 2026-11-21 07:46 | https://github.com/CognitionAI/devin-marketplace (README, `.agents/skills/adding-a-plugin/SKILL.md`, PR template) | 200 | A third-party plugin is one pinned object in `optionalPlugins` of `.devin-plugin/plugin.json` |

Mechanism: a pull request to `CognitionAI/devin-marketplace`. Requirements stated there:

- the entry is pinned to a full 40-hex commit SHA, never a branch or a tag;
- no display metadata goes in the entry; the plugin's own manifest at that SHA supplies it;
- `python3 scripts/validate.py --fix` then `--fetch` must pass;
- before opening the PR, the plugin is installed with `devin plugins install --local` and a
  session calls one of its tools or skills;
- opening the PR means agreeing to the Cognition App Developer Terms
  (https://cognition.com/legal/app-terms), which the PR template asks to tick.

## What exists

- The plugin repository has `.claude-plugin/plugin.json` and `.mcp.json` at
  `f37ab720795a7a15f27d5a00c302afdb321b9b3d` (`main`), which Devin reads through its fallback.
- Dry run on a local clone of `devin-marketplace` at `43cc7751d16ae0aec855d3ef671e94f21f6239ee`:
  `validate.py --fix` printed `ok: 239 entries (230 authored, 9 upstream)` and `validate.py --fetch`
  exited 0 with the entry below.
- Not done here: `devin plugins install --local` and a session that calls a tool. Both need a
  signed-in Devin CLI.

## Submission

Branch from `main` of the owner's fork. The diff, after `validate.py --fix` sorted it:

```diff
--- a/.devin-plugin/plugin.json
+++ b/.devin-plugin/plugin.json
@@ -279,6 +279,11 @@
       "source": "url",
       "url": "https://github.com/mobbin/skills.git",
       "sha": "cac338357d596415773874f06a6c16e862c195e4"
+    },
+    {
+      "source": "url",
+      "url": "https://github.com/qrcode-ai-com/qrcode-barcode-scanner-plugin.git",
+      "sha": "f37ab720795a7a15f27d5a00c302afdb321b9b3d"
     }
   ]
 }
```

If `main` has moved, rerun `python3 scripts/validate.py --fix`; it places the entry.

PR title: `Add qrcode-barcode-scanner plugin`

PR body (their template):

```markdown
## Summary

Adds QR Code & Barcode Scanner as an optional third-party plugin, pinned to commit
f37ab720795a7a15f27d5a00c302afdb321b9b3d of qrcode-ai-com/qrcode-barcode-scanner-plugin. It reads
QR codes and barcodes in local images through a skill and a local MCP server pinned to
@qrcode-ai-com/qrcode-barcode-scanner-mcp@0.3.4. Scanning runs on the user's computer and needs no
credential.

`python3 scripts/validate.py --fix` and `python3 scripts/validate.py --fetch` pass. Installed with
`devin plugins install --local` and checked with a session that scanned an image.

## Checklist

- [x] I have read and agree to the [Cognition App Developer Terms](https://cognition.com/legal/app-terms).
```

## The owner's next action

1. Read and decide on the Cognition App Developer Terms.
2. Install the Devin CLI, sign in, install the plugin with `devin plugins install --local` from a
   clone of the plugin repository at `f37ab72`, and have a session scan an image. Remove the
   sentence "Installed with … scanned an image" from the body if that test is not done.
3. Fork `CognitionAI/devin-marketplace`, apply the diff, run both `validate.py` commands, open the
   PR with the title and body above.
