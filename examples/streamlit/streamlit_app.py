"""Upload an image, or take the sample, and read every QR code and barcode in it.

Run it with `streamlit run examples/streamlit/streamlit_app.py`. The engine runs in the process of
this app, on the machine that serves it. The image is read in memory and is not stored.
"""
import json

import qrcode_barcode_scanner as scanner
import streamlit as st

import page_content as page
import scan_view

st.set_page_config(page_title="QR Code & Barcode Scanner", page_icon="🔎", layout="centered")
# None until the browser has reported its theme: the light pictures, as on a light page.
DARK = st.context.theme.type == "dark"


def picture(item: page.Picture) -> None:
    """One of the README's pictures, loaded by the browser from its absolute address."""
    st.image(item.url(DARK), alt=item.alt, link=item.link, width="stretch")


def scanner_section() -> None:
    """The scanner: the image, the profile and the budget, then the codes found and the report."""
    source = st.radio("Image", ["Sample image", "Upload an image"], horizontal=True)
    profile = st.selectbox("Scan profile", list(scan_view.PROFILES), format_func=scan_view.PROFILES.get)
    budget = st.number_input(
        "Time budget in milliseconds", min_value=0, max_value=scan_view.MAX_BUDGET_MS, value=None, step=100,
        placeholder="The profile's own budget",
        help="Empty keeps the profile's budget: fast 800 ms, frame 80 ms, full 4000 ms. 0 removes the budget.")

    if source == "Sample image":
        name, data = scan_view.SAMPLE_NAME, scan_view.sample()
        st.caption("The sample holds a QR code and a Code 128 barcode.")
    else:
        upload = st.file_uploader("PNG, JPEG, WebP or GIF", type=["png", "jpg", "jpeg", "webp", "gif"],
                                  max_upload_size=scan_view.MAX_BYTES // (1024 * 1024))
        if upload is None:
            st.info("Choose an image to scan.")
            return
        name, data = upload.name, upload.getvalue()

    try:
        report = scan_view.scan(data, profile, None if budget is None else int(budget))
    except ValueError as error:
        st.error(f"This image cannot be read: {error}")
        return

    found = scan_view.rows(report)
    if found:
        st.success(f"{len(found)} code(s) found in {name}.")
        st.dataframe(found, hide_index=True)
    else:
        st.warning(f"No QR code or barcode found in {name}.")
    if report["trace"]["budget_exhausted"]:
        st.warning("The time budget cut the scan, so this result is not final. Raise the budget or set it to 0.")
    try:
        st.image(scan_view.outlined(data, report), caption="Each code is outlined where the engine measured it.")
    except (OSError, ValueError):
        st.caption("This image has no preview here; the report below is complete.")

    with st.expander("The engine's full report"):
        st.json(report, expanded=False)
    st.download_button("Download the report (JSON)", json.dumps(report, ensure_ascii=False, indent=2),
                       file_name="scan-report.json", mime="application/json")


def about_section() -> None:
    """Below the scanner: the QR Code AI pages, Ask AI, then how the engine works and what it reads."""
    st.divider()
    st.subheader("Try it on QR Code AI")
    for paragraph in page.LINKS:
        st.markdown(paragraph)

    st.subheader("Ask AI")
    st.markdown(page.ask_ai_markdown())
    st.caption(page.ASK_AI_NOTE)
    with st.expander("Copy the plain-text prompt"):
        st.code(page.PROMPT, language=None, wrap_lines=True)

    st.subheader("How it works")
    picture(page.STEPS)
    st.write("The app passes the image's bytes to the engine, which runs in the app's Python process on the "
             "server, and draws the outlines from the report.")

    st.subheader("What it returns")
    picture(page.RETURNS)
    st.write("The picture is a recorded scan of the sample image, which holds a QR code and a Code 128 barcode. "
             "Both come back in one report, each with its format, its exact text and the place where the engine "
             "measured it: `https://qrc-ai.com/76xMa` and `STOCK-4827`.")

    st.subheader("What it reads")
    picture(page.FORMATS)
    st.markdown(
        "- QR: QR Code, Micro QR, rectangular Micro QR (rMQR)\n"
        "- Matrix and stacked: Data Matrix, Aztec, PDF417, MaxiCode\n"
        "- Retail: EAN-13, EAN-8, UPC-A, UPC-E\n"
        "- Other linear: Code 128, Code 39, Code 93, Codabar, ITF, GS1 DataBar, GS1 DataBar Expanded, Telepen")
    st.write("Codes of different formats in one image come back in one report. The engine's "
             f"[supported formats]({page.REPOSITORY}#supported-formats) section states the known limits.")

    st.subheader("The same engine in other runtimes")
    picture(page.RUNTIMES)
    st.write("The Rust, Node.js, browser and Python packages hold the engine. The Go and PHP packages hold no "
             "decoder: each one starts `qrscan` and hands you its report. The "
             f"[scanner repository]({page.REPOSITORY}) lists every route.")


picture(page.BANNER)
st.title("QR Code & Barcode Scanner")
st.write(
    "Read every QR code and barcode in an image with the open-source "
    "[QR Code & Barcode Scanner](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust) engine, "
    f"version {scanner.__version__}. The scan runs on the machine that serves this page, "
    "and the image is read in memory: this app stores nothing.")
st.caption(
    "On Streamlit Community Cloud, that machine is a Streamlit server in the United States, and "
    "Streamlit records usage statistics of the page. Run the app on your own machine to keep your "
    "images there.")
st.markdown(
    "From [QR Code AI](https://qrcode-ai.com/): the "
    "[QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner) and the "
    "[barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner) in the browser.")

scanner_section()
about_section()
