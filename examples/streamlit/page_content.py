"""What the page shows around the scanner: its banner, the pictures, the QR Code AI links and Ask AI.

The pictures are the files README.md beside this app shows, at their absolute raw.githubusercontent.com
addresses: the browser loads them from GitHub, and the app reads no file of the repository to show them.
The Ask AI prompt and links are the README's own; the tests hold both to it.
"""
from typing import NamedTuple
from urllib.parse import quote, urlencode

REPOSITORY = "https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust"
PROFILE = "https://raw.githubusercontent.com/qrcode-ai-com/.github/main/profile/assets/"
BRAND = "https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/brand/"
BADGES = "https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/"


class Picture(NamedTuple):
    light: str
    dark: str
    alt: str
    link: str | None = None

    def url(self, dark: bool) -> str:
        """The variant drawn for the page's theme."""
        return self.dark if dark else self.light


BANNER = Picture(
    PROFILE + "banner-streamlit-light.gif?v=d093d40c3693", PROFILE + "banner-streamlit-dark.gif?v=37c9eb844366",
    "QR Code & Barcode Scanner in a Streamlit app: the Streamlit logo, the app's controls, "
    "and a QR code and a barcode being read", REPOSITORY)
STEPS = Picture(
    PROFILE + "how-python-light.gif?v=bb48f1698ce2", PROFILE + "how-python-dark.gif?v=60b4945fed7e",
    "How the Python package works, in three steps: install the package, pass an image or a camera frame "
    "to the engine inside your process, and read the report")
RETURNS = Picture(
    BRAND + "examples-mixed-light.png?v=7f958679adcc", BRAND + "examples-mixed-dark.png?v=385593c1c18d",
    "A QR code and Code 128 decoded from the same image, each outlined where the engine measured it",
    REPOSITORY + "#examples")
FORMATS = Picture(
    BRAND + "formats-light.gif?v=bdfe5fc5f9b3", BRAND + "formats-dark.gif?v=92fa0e8084df",
    "The code families the engine reads: QR codes, matrix and stacked codes such as Data Matrix, retail "
    "barcodes such as EAN-13, and other linear barcodes such as Code 128", REPOSITORY + "#supported-formats")
RUNTIMES = Picture(
    BRAND + "runtimes-light.png?v=6dbd5a8cf5ba", BRAND + "runtimes-dark.png?v=57c63428574b",
    "One engine in the language you write: Rust on crates.io, Node.js and the browser on npm, Python on PyPI, "
    "Go, PHP, and the qrscan command line", REPOSITORY + "#get-started")

# The six QR Code AI pages, in sentences: the two scanners, the two Python guides and the two generators.
LINKS = (
    "The [QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner) and the "
    "[barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner) read codes in your browser, on "
    "[QR Code AI](https://qrcode-ai.com/). This app runs the same engine through its Python package: the "
    "[QR code scanner Python guide](https://qrcode-ai.com/en-US/qr-code-scanner/sdk/python) and the "
    "[barcode scanner Python guide](https://qrcode-ai.com/en-US/barcode-scanner/sdk/python) show how to add "
    "this scan to your own code.",
    "To make a test image with a known value, use the "
    "[QR code generator](https://qrcode-ai.com/en-US/qr-code-generator) or the "
    "[barcode generator](https://qrcode-ai.com/en-US/barcode-generator). Upload the exported image above and "
    "compare the text in the table with the value you encoded, leading zeroes included.",
)

PROMPT = (
    "Help me understand Scan images in a Streamlit app (examples/streamlit/README.md) for QR Code & Barcode "
    "Scanner, the open-source scanner. Source documentation; publication is not implied. Provided README "
    "context (verify against the sources): A small Streamlit app that reads every QR code and barcode in an "
    "image. Take the sample or upload a picture, and the app lists each code beside the image, outlines it "
    "where the engine measured it, and shows the full report. The image is read on the server that runs the "
    "app, in memory, and the app stores nothing. Read the public documentation below. Explain what this "
    "destination does, its documented installation or access steps, a minimal example if supported, "
    "prerequisites, limitations and license. Distinguish published packages from working source and "
    "preparation. Cite your sources; if a page is unavailable or a fact cannot be checked, say so. Do not "
    "invent installation commands, benchmark results or comparisons. Answer in my language. Public sources: "
    "https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/blob/main/examples/streamlit/README.md "
    "https://qrcode-ai.com/en-US/qr-code-scanner https://qrcode-ai.com/en-US/barcode-scanner "
    "https://qrcode-ai.com/en-US/qr-code-scanner/sdk/python "
    "https://qrcode-ai.com/en-US/barcode-scanner/sdk/python "
    "https://qrcode-ai.com/en-US/qr-code-generator https://qrcode-ai.com/en-US/barcode-generator")

# (badge file, label, address, query parameter that carries the prompt): the README's nine assistants.
ASSISTANTS = (
    ("chatgpt", "ChatGPT", "https://chatgpt.com/", "q"),
    ("claude", "Claude", "https://claude.ai/new", "q"),
    ("gemini", "Gemini", "https://gemini.google.com/", None),
    ("grok", "Grok", "https://grok.com/", "q"),
    ("perplexity", "Perplexity", "https://www.perplexity.ai/", "q"),
    ("copilot", "Copilot", "https://copilot.com/", None),
    ("deepseek", "DeepSeek", "https://chat.deepseek.com/", None),
    ("meta-ai", "Meta AI", "https://www.meta.ai/", None),
    ("qwen", "Qwen", "https://qwen.ai/", None),
)
ASK_AI_NOTE = (
    "Choose an AI assistant to explain this scanner using its public sources. ChatGPT, Claude, Grok and "
    "Perplexity open with the prompt filled in; Gemini, Copilot, DeepSeek, Meta AI and Qwen open their home "
    "page, where you paste the prompt below. Sign-in may be required. Check the answer against the documentation.")


def ask_ai_links(prompt: str = PROMPT) -> list[tuple[str, str]]:
    """(label, address) of each assistant, the prompt in the address where the assistant reads one."""
    return [(label, base + ("?" + urlencode({param: prompt}, quote_via=quote) if param else ""))
            for _, label, base, param in ASSISTANTS]


def ask_ai_markdown(prompt: str = PROMPT) -> str:
    """The nine assistants as the README's badges, each a link that opens the assistant."""
    return "\n".join(f"[![Ask {label}]({BADGES}{key}-v2.svg)]({url})"
                     for (key, *_), (label, url) in zip(ASSISTANTS, ask_ai_links(prompt), strict=True))
