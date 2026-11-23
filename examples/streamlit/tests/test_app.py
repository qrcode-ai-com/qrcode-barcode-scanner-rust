"""The app through Streamlit's own test runner: each widget driven as a visitor would use it."""
import html
import io
import json
import os
import pathlib
import re

import pytest
import python_host_kit as kit
import qrcode_barcode_scanner
import tomllib
from PIL import Image
from streamlit.testing.v1 import AppTest

import page_content as page
import scan_view

APP = pathlib.Path(__file__).resolve().parents[1]
QR = "https://qrc-ai.com/76xMa"
CODE128 = "STOCK-4827"
PROFILES = ("fast", "frame", "full")
# The engine version requirements.txt pins; the host kit's default follows the other Python hosts.
ENGINE_VERSION = "0.12.0"
PICTURES = (page.BANNER, page.STEPS, page.RETURNS, page.FORMATS, page.RUNTIMES)
# The six QR Code AI pages every scanner destination links in its sentences: the two scanners, the
# two guides of the route this app uses (Python) and the two generators.
SIX = tuple("https://qrcode-ai.com/en-US/" + path for path in (
    "qr-code-scanner", "barcode-scanner", "qr-code-scanner/sdk/python", "barcode-scanner/sdk/python",
    "qr-code-generator", "barcode-generator"))


@pytest.fixture
def mixed_bytes():
    """The mixed fixture, or the copy an acceptance run staged, checked against its SHA-256."""
    return kit.mixed_bytes(APP)


def start():
    app = AppTest.from_file(str(APP / "streamlit_app.py"), default_timeout=60)
    app.run()
    assert not app.exception, app.exception
    return app


def upload(app, name, data, mime="image/png"):
    app.radio[0].set_value("Upload an image").run()
    app.file_uploader[0].set_value((name, data, mime)).run()
    assert not app.exception, app.exception
    return app


def table(app):
    [frame] = app.dataframe
    return frame.value.to_dict("records")


def images(app):
    """The address of every image on the page, in page order."""
    return [image.proto.imgs[0].url for image in app.get("image")]


def scan_images(app):
    """The images the scan drew: every image that is not one of the README's pictures."""
    pictures = {item.light for item in PICTURES} | {item.dark for item in PICTURES}
    return [url for url in images(app) if url not in pictures]


def assert_about_section(app):
    """Below the scanner, on every view: the six links in sentences, Ask AI and the four pictures."""
    assert [header.value for header in app.subheader] == [
        "Try it on QR Code AI", "Ask AI", "How it works", "What it returns", "What it reads",
        "The same engine in other runtimes"]
    sentences = [element.value for element in app.markdown if element.value in page.LINKS]
    assert sentences == list(page.LINKS)
    linked = set(re.findall(r"\]\((https://qrcode-ai\.com/[^)]+)\)", " ".join(sentences)))
    assert set(SIX) <= linked and all(sentence.endswith(".") for sentence in sentences)
    assert [element.value for element in app.markdown].count(page.ask_ai_markdown()) == 1
    assert app.code[-1].value == page.PROMPT
    # The banner first, then the four pictures after the scanner, light variants as the theme is unknown.
    shown = images(app)
    assert shown[0] == page.BANNER.light
    assert shown[-4:] == [page.STEPS.light, page.RETURNS.light, page.FORMATS.light, page.RUNTIMES.light]
    github = "https://raw.githubusercontent.com/qrcode-ai-com/"
    assert all(url.startswith(github) for url in shown[:1] + shown[-4:])


def png(width, height, color="white"):
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_the_first_visit_scans_the_sample_with_the_fast_profile():
    app = start()
    assert app.title[0].value == "QR Code & Barcode Scanner"
    # The banner above the title links the engine repository.
    [banner, *_] = app.get("image")
    assert banner.proto.link == page.REPOSITORY and banner.proto.imgs[0].alt == page.BANNER.alt
    # Where the scan runs, said on the page itself: on Community Cloud, a Streamlit server.
    assert app.caption[0].value.startswith("On Streamlit Community Cloud, that machine is a Streamlit server")
    # The three QR Code AI links under the introduction, before the scanner.
    assert app.markdown[1].value == (
        "From [QR Code AI](https://qrcode-ai.com/): the "
        "[QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner) and the "
        "[barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner) in the browser.")
    # The scan stays the first thing to use: the scanner's widgets and result come before the section below.
    kinds = [element.type for element in app.main.children.values()]
    assert kinds.index("radio") < kinds.index("success") < kinds.index("divider") < kinds.index("subheader")
    assert_about_section(app)
    assert app.radio[0].value == "Sample image" and app.selectbox[0].value == "fast"
    assert app.number_input[0].value is None
    assert app.success[0].value == "2 code(s) found in mixed-code128-qr.png."
    assert table(app) == [{"Format": "qr_code", "Text": QR, "Kind": "url"},
                          {"Format": "code128", "Text": CODE128, "Kind": "text"}]
    assert len(scan_images(app)) == 1 and not app.warning
    [download] = app.get("download_button")
    assert download.label == "Download the report (JSON)"


@pytest.mark.parametrize("profile", PROFILES)
def test_an_uploaded_mixed_image_gives_both_codes_in_each_profile(mixed_bytes, profile):
    app = start()
    app.selectbox[0].set_value(profile)
    app.number_input[0].set_value(0)
    upload(app, "label.png", mixed_bytes)
    assert app.success[0].value == "2 code(s) found in label.png."
    assert [row["Text"] for row in table(app)] == [QR, CODE128]
    report = kit.assert_mixed(json.loads(app.json[0].value), profile, ENGINE_VERSION)
    direct = qrcode_barcode_scanner.scan(mixed_bytes, profile, budget_ms=0)
    assert report["detections"] == json.loads(json.dumps(direct["detections"]))


def test_the_upload_view_waits_for_a_file_and_names_the_limit():
    app = start()
    app.radio[0].set_value("Upload an image").run()
    [uploader] = app.file_uploader
    assert uploader.allowed_type == [".png", ".jpg", ".jpeg", ".webp", ".gif"]
    assert app.info[0].value == "Choose an image to scan." and not app.success and not app.dataframe
    # The section below the scanner is there before any file is chosen.
    assert_about_section(app)


def test_an_image_without_code_and_a_file_that_is_no_image(tmp_path):
    app = upload(start(), "blank.png", png(64, 48))
    assert app.warning[0].value == "No QR code or barcode found in blank.png." and not app.dataframe
    app = upload(start(), "notes.png", b"this is not an image")
    assert "[QRS-001]" in app.error[0].value and not scan_images(app)
    assert_about_section(app)


def test_an_oversized_image_is_refused_before_the_scan():
    app = upload(start(), "wide.png", png(5000, 8))
    assert app.error[0].value.startswith("This image cannot be read:")
    assert "[QRS-" in app.error[0].value


def test_a_budget_cut_says_the_result_is_not_final(mixed_bytes):
    app = start()
    app.selectbox[0].set_value("full")
    app.number_input[0].set_value(1)
    app = upload(app, "mixed.png", mixed_bytes)
    report = json.loads(app.json[0].value)
    shown = any("not final" in warning.value for warning in app.warning)
    assert shown is report["trace"]["budget_exhausted"]


def test_the_pictures_prompt_and_ask_ai_links_match_the_readme():
    """The README beside the app passes the destination's checks; the page shows the same pictures and links."""
    readme = (APP / "README.md").read_text()
    for item in PICTURES:
        assert item.light in readme and item.dark in readme, item.alt
        assert f'alt="{html.escape(item.alt, quote=False)}"' in readme, item.alt
        assert (item.url(False), item.url(True)) == (item.light, item.dark)
    start, end = "<!-- qrcode-ai-readme-actions:v2 -->", "<!-- /qrcode-ai-readme-actions:v2 -->"
    block = readme[readme.index(start):readme.index(end)]
    assert re.search(r"```text\n(.*?)\n```", block, re.S)[1] == page.PROMPT
    badges = re.findall(r"\[!\[([^\]]+)\]\((https://[^)]+)\)\]\((https://[^)]+)\)", block)
    assert [(label, url) for label, _, url in badges] == page.ask_ai_links()
    assert [badge for _, badge, _ in badges] == re.findall(r"\]\((https://[^)]+\.svg)\)", page.ask_ai_markdown())
    # Four assistants open with the prompt in their address, the other five open their home page.
    prefilled = [label for label, url in page.ask_ai_links() if "?q=" in url]
    assert prefilled == ["ChatGPT", "Claude", "Grok", "Perplexity"]


def test_the_requirements_pin_the_published_engine():
    assert (APP / "requirements.txt").read_text().split() == [
        "streamlit==1.67.0", "pillow==13.0.0", f"qrcode-barcode-scanner=={qrcode_barcode_scanner.__version__}"]
    assert qrcode_barcode_scanner.__version__ == ENGINE_VERSION


def test_the_config_beside_the_app_matches_its_limits():
    """Community Cloud reads .streamlit/config.toml beside the entrypoint; it must hold the app's limit."""
    config = tomllib.loads((APP / ".streamlit" / "config.toml").read_text())
    assert config == {"server": {"maxUploadSize": 8}, "browser": {"gatherUsageStats": False}}
    assert config["server"]["maxUploadSize"] * 1024 * 1024 == scan_view.MAX_BYTES
    assert not (APP.parents[1] / ".streamlit").exists(), "a root config would be read by every app"


def test_the_acceptance_reports_are_written_through_the_app(mixed_bytes):
    """Three reports for scripts/destination-acceptance.py, when an acceptance run asks for them."""
    if not os.environ.get(kit.REPORTS_VARIABLE):
        pytest.skip(f"{kit.REPORTS_VARIABLE} is not set")

    def scan(profile):
        app = start()
        app.selectbox[0].set_value(profile)
        app.number_input[0].set_value(0)
        upload(app, "mixed.png", mixed_bytes)
        assert app.success[0].value == "2 code(s) found in mixed.png."
        return kit.assert_mixed(json.loads(app.json[0].value), profile, ENGINE_VERSION)

    assert len(kit.write_acceptance_reports(scan)) == 3
