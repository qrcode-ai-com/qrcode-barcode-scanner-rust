#!/usr/bin/env python3
"""Exercise URL payloads, README preservation and publication boundaries."""
import base64
import importlib.util
import json
from pathlib import Path
import re
import re
import unittest
from urllib.parse import parse_qs, urlsplit, unquote
from readme_prose import canonical_links, prose_links
from readme_actions import ASSETS, action_block, ai_links, html_tags, insert_actions, mcp_links, question, strip_actions

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build-readme-actions.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def listed_readmes():
    """The committed list of maintained READMEs (scripts/maintained-readmes.txt)."""
    lines = (ROOT / 'scripts/maintained-readmes.txt').read_text().splitlines()
    return [line for line in lines if line and not line.startswith('#')]


class ReadmeActions(unittest.TestCase):
    def test_prefill_routes_keep_exact_text_and_paste_routes_use_only_official_homepages(self):
        prompt = question('Flutter & café', 'https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/blob/main/bindings/flutter/README.md')
        expected = [('chatgpt.com', '/', 'q'), ('claude.ai', '/new', 'q'),
                    ('gemini.google.com', '/', None), ('grok.com', '/', 'q'), ('www.perplexity.ai', '/', 'q'),
                    ('copilot.com', '/', None), ('chat.deepseek.com', '/', None),
                    ('www.meta.ai', '/', None), ('qwen.ai', '/', None)]
        self.assertEqual(len(ai_links(prompt)), 9)
        for (_, _, link), (host, path, param) in zip(ai_links(prompt), expected, strict=True):
            parsed = urlsplit(link)
            self.assertEqual((parsed.scheme, parsed.netloc, parsed.path), ('https', host, path))
            self.assertEqual(parse_qs(parsed.query), {param: [prompt]} if param else {})
            self.assertEqual(parsed.fragment, '')
        self.assertIn('if a page is unavailable', prompt)
        self.assertIn('Do not invent', prompt)
        contextual = question('MCP', 'https://qrcode-ai.com/', context='Local stdio adapter for the scanner.')
        self.assertIn('Provided README context (verify against the sources): Local stdio adapter for the scanner.', contextual)

    def test_editor_configuration_is_exact_pinned_and_has_no_grants(self):
        config = json.loads((ROOT / 'distribution/readme-actions.json').read_text())['mcpLaunch']
        cursor, vscode = mcp_links(config)
        self.assertEqual(json.loads(base64.b64decode(parse_qs(urlsplit(cursor[2]).query)['config'][0])), config)
        native = parse_qs(urlsplit(vscode[2]).query)['url'][0]
        self.assertEqual(json.loads(unquote(native.split('?', 1)[1])), {'name': 'qrscan', **config})
        with self.assertRaises(ValueError):
            mcp_links({**config, 'env': {'ALLOWED_ROOTS': '/'}})
        with self.assertRaises(ValueError):
            mcp_links({'command': 'npx', 'args': ['--yes', '--ignore-scripts', '@qrcode-ai-com/qrcode-barcode-scanner-mcp@latest']})

    def test_generated_blocks_preserve_the_original_body_and_are_idempotent(self):
        original = '# Flutter\n\nNatural description.\n\n```dart\nscan(bytes);\n```\n'
        block = action_block('Explain this destination.')
        rendered = insert_actions(original, block)
        self.assertEqual(strip_actions(rendered), original)
        self.assertEqual(insert_actions(rendered, block), rendered)
        with self.assertRaises(ValueError):
            strip_actions(rendered + block)
        self.assertIn('Copy the plain-text prompt', block)
        self.assertIn('```text\nExplain this destination.\n```', block)
        self.assertNotIn('Google AI Studio', block)
        self.assertIn('](https://gemini.google.com/)', block)

    def test_a_page_shown_without_html_gets_its_prompt_unfolded(self):
        original = '# .NET\n\nNatural description.\n'
        block = action_block('Explain this destination.', markdown_only=True)
        self.assertEqual(html_tags(block), [])
        self.assertIn('**Copy the plain-text prompt**', block)
        self.assertIn('```text\nExplain this destination.\n```', block)
        rendered = insert_actions(original, block)
        self.assertEqual(strip_actions(rendered), original)
        self.assertEqual(insert_actions(insert_actions(original, action_block('Explain this destination.')), block), rendered)

    def test_a_page_that_drops_image_links_gets_text_links_and_plain_pictures(self):
        prompt = 'Explain this destination.'
        block = action_block(prompt, markdown_only=True, text_links=True)
        self.assertEqual(html_tags(block), [])
        self.assertNotIn('![', block)
        self.assertEqual([line.removesuffix(' ·') for line in block.split('### Ask AI\n\n')[1].split('\n\n')[0].splitlines()],
                         [f'[Ask {label}]({url})' for _, label, url in ai_links(prompt)])
        self.assertEqual(strip_actions(insert_actions('# Glama\n\nNatural description.\n', block)),
                         '# Glama\n\nNatural description.\n')
        outputs = builder.outputs()
        self.assertIn('distribution/glama/README.md', builder.TEXT_LINKS)
        for path in builder.TEXT_LINKS:
            with self.subTest(path=path):
                text = outputs[path]
                # Glama removes HTML and the link around an image: neither may carry content here.
                self.assertEqual(html_tags(text), [])
                self.assertNotRegex(text, r'\[!\[')
                self.assertEqual(text.count('### Ask AI'), 1)
                self.assertEqual(text.count('[Ask ChatGPT](https://chatgpt.com/?q='), 1)
                pictures = re.findall(r'!\[[^\]]+\]\(([^)\s]+)\)', text)
                self.assertEqual(len(pictures), 5)
                self.assertTrue(all(url.startswith('https://raw.githubusercontent.com/qrcode-ai-com/') for url in pictures))

    def test_a_page_that_makes_every_image_a_block_gets_badges_floated_into_a_row(self):
        # community.obsidian.md styles every image as a block and an image in a paragraph with
        # 2rem margins: Markdown badges stand one per line there. align="left" floats each image
        # whatever its display, hspace keeps a gap, <br clear="all"> ends the row; GitHub's
        # sanitizer keeps the three attributes.
        import html as markup
        prompt = 'Explain this destination & its limits.'
        block = action_block(prompt, floated=True)
        row = block.split('### Ask AI\n\n')[1].split('\n\n')[0]
        lines = row.splitlines()
        # One HTML block: no blank line inside, so Markdown passes it through whole.
        self.assertEqual((lines[0], lines[-3:]), ('<div>', ['<br clear="all">', '</div>', '<p></p>']))
        badges = [re.fullmatch(r'<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)" align="left" hspace="2"></a>', line)
                  for line in lines[1:-3]]
        self.assertTrue(all(badges), lines[1:-3])
        self.assertEqual([(markup.unescape(m[1]), m[2], m[3]) for m in badges],
                         [(url, f'{ASSETS}{key}-v2.svg', label) for key, label, url in ai_links(prompt)])
        self.assertNotIn('[![', block)
        self.assertIn('<details>', block)
        self.assertEqual(strip_actions(insert_actions('# Obsidian\n\nNatural description.\n', block)),
                         '# Obsidian\n\nNatural description.\n')
        installers = action_block(prompt, mcp_links(json.loads((ROOT / 'distribution/readme-actions.json').read_text())['mcpLaunch']),
                                  floated=True)
        self.assertEqual(installers.count('<br clear="all">'), 2)
        self.assertNotIn('&config', installers)
        for flags in ({'markdown_only': True}, {'text_links': True}):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                action_block(prompt, floated=True, **flags)
        outputs = builder.outputs()
        self.assertEqual(builder.BLOCK_IMAGES, {'integrations/obsidian/README.md'})
        for path in builder.BLOCK_IMAGES:
            with self.subTest(path=path):
                text = outputs[path]
                self.assertEqual(text, (ROOT / path).read_text())
                self.assertEqual(text.count('align="left" hspace="2"></a>'), 9)
                self.assertEqual(text.count('<br clear="all">'), 1)
                self.assertNotRegex(text, r'\[!\[(ChatGPT|Qwen)\]')
                prompt = markup.unescape(re.search(r'```text\n(.+)\n```', text)[1])
                for _, _, url in ai_links(prompt):
                    self.assertEqual(text.count(f'<a href="{markup.escape(url)}"><img '), 1)

    def test_a_page_that_shows_each_image_as_a_gallery_gets_one_line_of_text_links(self):
        # The Dify Marketplace shows each image as a block gallery and each line break as <br>:
        # its assistants are text links on one line, and its <details> stays.
        prompt = 'Explain this destination.'
        block = action_block(prompt, text_links=True, line_breaks=True)
        row = block.split('### Ask AI\n\n')[1].split('\n\n')[0]
        self.assertEqual(row, ' · '.join(f'[Ask {label}]({url})' for _, label, url in ai_links(prompt)))
        self.assertIn('<details>', block)
        with self.assertRaises(ValueError):
            action_block(prompt, line_breaks=True)
        outputs = builder.outputs()
        self.assertEqual(builder.GALLERY_IMAGES, {'integrations/dify/README.md'})
        for path in builder.GALLERY_IMAGES:
            with self.subTest(path=path):
                text = outputs[path]
                self.assertEqual(text, (ROOT / path).read_text())
                prompt = re.search(r'```text\n(.+)\n```', text)[1]
                row = text.split('### Ask AI\n\n')[1].split('\n\n')[0]
                self.assertEqual(row, ' · '.join(f'[Ask {label}]({url})' for _, label, url in ai_links(prompt)))
                self.assertNotIn('/docs/assets/actions/', text)
                self.assertEqual(text.count('<details>'), 1)

    def test_the_artifact_hub_listing_keeps_its_block_and_pictures_without_html(self):
        # Artifact Hub renders the page with react-markdown and skipHtml: any tag would vanish,
        # while a Markdown image, linked or not, is kept.
        path = 'distribution/artifacthub/LISTING.md'
        self.assertEqual(builder.LISTINGS, (path,))
        text = builder.outputs()[path]
        self.assertEqual(text, (ROOT / path).read_text())
        self.assertEqual(html_tags(text), [])
        self.assertEqual((text.count('<!-- qrcode-ai-readme-actions:v2 -->'), text.count('### Ask AI')), (1, 1))
        self.assertIn('**Copy the plain-text prompt**', text)
        prompt = re.search(r'```text\n(.+)\n```', text)[1]
        self.assertIn('/blob/main/' + path, prompt)
        badges = re.findall(r'\[!\[([^\]]+)\]\(https://[^)\s]+/docs/assets/actions/([a-z-]+)-v2\.svg\)\]\(([^)\s]+)\)', text)
        self.assertEqual(badges, [(label, key, link) for (key, *_), (_, label, link) in
                                  zip(builder.PROVIDERS, ai_links(prompt), strict=True)])
        pictures = re.findall(r'!\[[^\]]+\]\((https://[^)\s]+)\)', text)
        pictures = [url for url in pictures if '/docs/assets/actions/' not in url]
        readme = (ROOT / 'distribution/artifacthub/README.md').read_text()
        self.assertEqual([url.split('/')[-1].split('?')[0] for url in pictures],
                         ['banner-container-light.gif', 'journey-containers-light.gif', 'examples-mixed-light.png',
                          'formats-light.gif', 'runtimes-light.png'])
        for url in pictures:
            # The same address and hash as the light variant of the folder README.
            self.assertTrue(f'<img src="{url}"' in readme, url + ' is not the light picture of the folder README')
        self.assertEqual(set(canonical_links(path)) - prose_links(text), set())
        self.assertTrue(all(link.endswith('/docker') for link in canonical_links(path)[2:4]))
        # The page of an AGPL image gets no MIT source-license section, and names one version.
        self.assertNotIn('qrscan-source-license', text)
        runs = re.search(r'This image runs `qrscan` (\d+\.\d+\.\d+)', text)[1]
        licensed = re.search(r'The (\d+\.\d+\.\d+) program in this image is licensed AGPL-3\.0-or-later\.', text)[1]
        self.assertEqual(runs, licensed)

    def test_html_tags_are_found_outside_code_and_comments_only(self):
        self.assertEqual(html_tags('<details>\n<summary>Copy</summary>\n\n</details>'),
                         ['<details>', '<summary>', '</summary>', '</details>'])
        self.assertEqual(html_tags('A <sub>note</sub> and <img src="a.png" alt="">.'), ['<sub>', '</sub>', '<img src="a.png" alt="">'])
        self.assertEqual(html_tags('<!-- a marker -->\n\nText with `List<string>` and <https://example.com/>.'), [])
        self.assertEqual(html_tags('```xml\n<PackageReference Include="A" />\n```\n\n~~~~\n<b>\n~~~\n</b>\n~~~~\n'), [])
        self.assertEqual(html_tags('```xml\n<a>\n```\n\n<b>bold</b>'), ['<b>', '</b>'])

    def test_the_readme_packed_for_nuget_holds_no_html(self):
        outputs = builder.outputs()
        self.assertIn('bindings/dotnet/README.md', builder.MARKDOWN_ONLY)
        for path in builder.MARKDOWN_ONLY:
            self.assertEqual(html_tags(outputs[path]), [], path)
            self.assertEqual(outputs[path].count('### Ask AI'), 1)
        self.assertIn('<details>', outputs['README.md'])

    def test_previous_action_blocks_upgrade_without_duplicating_or_rewriting_the_body(self):
        body = '# Scanner\n\nA natural introduction.\n'
        old = '# Scanner\n\n<!-- qrcode-ai-readme-actions:v1 -->\n\nOld controls.\n\n<!-- /qrcode-ai-readme-actions:v1 -->\n\nA natural introduction.\n'
        self.assertEqual(strip_actions(old), body)
        upgraded = insert_actions(old, action_block('Explain the scanner.'))
        self.assertIn('qrcode-ai-readme-actions:v2', upgraded)
        self.assertNotIn('qrcode-ai-readme-actions:v1', upgraded)
        self.assertEqual(strip_actions(upgraded), body)
        with self.assertRaises(ValueError):
            strip_actions(old + action_block('Do not accept two formats.'))

    def test_frozen_and_vendored_readmes_are_not_targets(self):
        paths = builder.maintained_readmes()
        self.assertEqual(sorted(str(path) for path in paths), listed_readmes(),
                         'add or remove the README in scripts/maintained-readmes.txt (sorted)')
        self.assertNotIn('distribution/docker/v0.11/README.md', paths)
        self.assertNotIn('docs/assets/readme/README.md', paths)
        self.assertFalse(any('/cargokit/' in path for path in paths))
        outputs = builder.outputs()
        for path in paths:
            self.assertEqual(outputs[path].count('### Ask AI'), 1)
            ask = ('[Ask ChatGPT](https://chatgpt.com/?q=' if path in builder.TEXT_LINKS | builder.GALLERY_IMAGES
                   else '<img src="' + ASSETS + 'chatgpt-v2.svg" alt="ChatGPT" align="left"' if path in builder.BLOCK_IMAGES
                   else '[![ChatGPT]')
            self.assertEqual(outputs[path].count(ask), 1)
            self.assertEqual('Add to Cursor' in outputs[path], path in ('README.md', 'integrations/mcp/README.md'))

    def test_a_notebook_a_host_opens_carries_the_block_in_its_first_cell_only(self):
        outputs = builder.outputs()
        for path in builder.NOTEBOOKS:
            with self.subTest(path=path):
                committed = json.loads((ROOT / path).read_text())
                rendered = json.loads(outputs[path])
                cells = [''.join(cell['source']) for cell in rendered['cells']]
                self.assertEqual(rendered['cells'][0]['cell_type'], 'markdown')
                self.assertEqual(cells[0].count('### Ask AI'), 1)
                self.assertEqual(cells[0].count('[![ChatGPT]'), 1)
                self.assertFalse(any('qrcode-ai-readme-actions' in text for text in cells[1:]))
                self.assertIn('/blob/main/' + path, cells[0])
                self.assertEqual(set(canonical_links(path)) - prose_links(cells[0]), set())
                self.assertTrue(all(link.endswith('/sdk/python') for link in canonical_links(path)[2:4]))
                # The block is the only change: the cells around it and their outputs stay as committed.
                self.assertEqual(strip_actions(cells[0]), strip_actions(''.join(committed['cells'][0]['source'])))
                self.assertEqual(rendered['cells'][1:], committed['cells'][1:])

    def test_six_links_must_be_in_sentences_not_just_a_table_or_prompt(self):
        link = '[QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner)'
        self.assertEqual(prose_links('A sentence before the table.\n| Try it | ' + link + ' |'), set())
        self.assertEqual(prose_links('```text\nTry the scanner with this prompt: ' + link + '\n```'), set())
        self.assertEqual(prose_links(link + ' · [Other](https://example.com/)'), set())
        self.assertEqual(prose_links('To check an image before integrating the package, use the ' + link + '.'),
                         {'https://qrcode-ai.com/en-US/qr-code-scanner'})

    def test_fence_like_lines_cannot_turn_code_links_into_prose(self):
        url = 'https://qrcode-ai.com/en-US/qr-code-scanner'
        sentence = 'To check an image before integrating the package, use the [QR code scanner](' + url + ').'
        for newline in ('\n', '\r\n'):
            for marker in ('`', '~'):
                for false_close in (marker * 3 + 'not-a-close', marker * 5 + ' trailing',
                                    marker * 3 + ' ' + marker, marker * 2, '    ' + marker * 4):
                    with self.subTest(newline=newline, marker=marker, false_close=false_close):
                        code = newline.join((marker * 4 + 'md', false_close, sentence))
                        self.assertEqual(prose_links(code), set())
                        self.assertEqual(prose_links(code + newline + marker * 5 + ' \t'), set())
                        # Only a real closer allows a subsequent prose paragraph to qualify.
                        self.assertEqual(prose_links(code + newline + marker * 5 + ' \t' + newline * 2 + sentence), {url})
        self.assertEqual(prose_links('```invalid`info\n\n' + sentence), {url})
        for indent in ('    ', '\t'):
            self.assertEqual(prose_links(indent + sentence), set())
            self.assertEqual(prose_links(indent + '```md\n' + indent + sentence + '\n' + indent + '```'), set())

    def test_every_maintained_readme_has_its_six_canonical_links_in_prose(self):
        for path in builder.maintained_readmes():
            with self.subTest(path=path):
                body = (ROOT / path).read_text()
                self.assertEqual(set(canonical_links(path)) - prose_links(body), set())

    def test_the_chocolatey_description_keeps_to_what_its_gallery_renders_and_accepts(self):
        # community.chocolatey.org renders <description> with Markdig, shows raw HTML (comments
        # included) as text and turns each line break into <br>. Its validator refuses more than
        # 4000 characters (CPMR0026) and a heading without its space (CPMR0030).
        import xml.etree.ElementTree as ET
        nuspec = ET.parse(ROOT / 'distribution/chocolatey/qrcode-barcode-scanner.nuspec').getroot()
        text = nuspec.find('{*}metadata/{*}description').text
        self.assertLessEqual(len(text), 4000)
        self.assertEqual(html_tags(text), [])
        self.assertNotIn('<!--', text)
        self.assertEqual(re.findall(r'^#+[^#\s].*', text, re.M), [])
        paragraphs = [part for part in text.strip().split('\n\n') if not re.match(r'\d+\. ', part)]
        self.assertEqual([part for part in paragraphs if '\n' in part], [])
        self.assertEqual(set(canonical_links('distribution/chocolatey/README.md')) - prose_links(text), set())
        # The assistants that take a prompt in their URL carry the same request the page asks to paste.
        prompt = re.search(r'paste `([^`]+)`', text)[1]
        for _, label, link in ai_links(prompt):
            self.assertIn(f'[{label}]({link})', text)

    def test_every_assistant_badge_embeds_its_colored_retained_logo_and_license(self):
        import hashlib
        import xml.etree.ElementTree as ET
        manifest = json.loads((ROOT / 'docs/assets/actions/brands/provenance.json').read_text())
        outputs = builder.outputs()
        ns = {'s': 'http://www.w3.org/2000/svg'}
        self.assertEqual({row['id'] for row in manifest['icons']}, {row[0] for row in builder.PROVIDERS})
        for row in manifest['icons']:
            with self.subTest(provider=row['id']):
                original = (ROOT / 'docs/assets/actions/brands' / row['file']).read_bytes()
                self.assertEqual(hashlib.sha256(original).hexdigest(), row['sha256'])
                key = row['id']
                self.assertTrue(f'docs/assets/actions/{key}-v2.svg' in outputs, 'Missing colored badge: ' + key)
                logo = ET.fromstring(outputs[f'docs/assets/actions/{key}-logo-v1.svg'])
                badge = ET.fromstring(outputs[f'docs/assets/actions/{key}-v2.svg'])
                self.assertEqual(logo.attrib['data-ai-logo'], key)
                self.assertEqual(badge.find('s:svg', ns).attrib['data-ai-logo'], key)
                self.assertIn('Copyright (c) 2023 LobeHub', ''.join(badge.itertext()))
                self.assertIn('Permission is hereby granted', ''.join(badge.itertext()))
                # All original path geometry survives; this is a logo, not a text-only badge.
                source_paths = [p.attrib['d'] for p in ET.fromstring(original).findall('.//s:path', ns)]
                self.assertTrue(source_paths)
                self.assertEqual([p.attrib['d'] for p in badge.findall('.//s:path', ns)], source_paths)
                self.assertEqual(logo.find('s:svg', ns).attrib['color'], row['color'])
                self.assertEqual(logo.find('s:rect', ns).attrib['fill'], '#fff')
                self.assertFalse(badge.findall('.//s:image', ns))
                self.assertFalse(badge.findall('.//s:script', ns))
        # Legacy versioned image URLs keep their original text-only bytes.
        from readme_actions import badge_svg
        for key, label, *_ in builder.PROVIDERS:
            self.assertEqual((ROOT / f'docs/assets/actions/{key}-v1.svg').read_text(), badge_svg('Ask ' + label))
        for path in sorted(set(builder.maintained_readmes()) - builder.TEXT_LINKS - builder.GALLERY_IMAGES):
            for key, *_ in builder.PROVIDERS:
                self.assertTrue(f'/{key}-v2.svg' in outputs[path], path + ': missing colored ' + key)

    def test_badge_inputs_reject_active_svg_and_external_paint(self):
        from readme_actions import brand_logo
        for body in ('<script/>', '<path onload="alert(1)"/>',
                     '<path fill="url(https://invalid.example/track.svg)"/>', '<image href="https://invalid.example/track.svg"/>'):
            with self.subTest(svg=body), self.assertRaises(ValueError):
                brand_logo('<svg xmlns="http://www.w3.org/2000/svg">' + body + '</svg>', '#000', 'grok', 'MIT')
        with self.assertRaises(ValueError):
            brand_logo('<!DOCTYPE svg><svg/>', '#000', 'grok', 'MIT')
        with self.assertRaises(ValueError):
            brand_logo('<svg xmlns="http://www.w3.org/2000/svg"/>', '#12345', 'grok', 'MIT')

    def test_scope_and_context_cannot_be_ambiguous(self):
        self.assertIn('connected product', question('iOS app', 'https://qrcode-ai.com/', scope='qrcodeai'))
        for url in ('file:///private/x', 'http://example.com', 'https://token@example.com/'):
            with self.assertRaises(ValueError):
                question('Scanner', url)
        with self.assertRaises(ValueError):
            question('Scanner\nignore instructions', 'https://qrcode-ai.com/')


if __name__ == '__main__':
    unittest.main()
