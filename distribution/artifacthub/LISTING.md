[![QR Code & Barcode Scanner CLI in a container: the Docker logo, the commands that pull and run the image, and a QR code and a barcode being read](https://raw.githubusercontent.com/qrcode-ai-com/.github/main/profile/assets/banner-container-light.gif?v=ae09c23a53de)](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust)

# QR Code & Barcode Scanner · container image

<!-- qrcode-ai-readme-actions:v2 -->

### Ask AI

[![ChatGPT](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/chatgpt-v2.svg)](https://chatgpt.com/?q=Help%20me%20understand%20QR%20Code%20%26%20Barcode%20Scanner%20%C2%B7%20container%20image%20%28distribution%2Fartifacthub%2FLISTING.md%29%20for%20QR%20Code%20%26%20Barcode%20Scanner%2C%20the%20open-source%20scanner.%20Source%20documentation%3B%20publication%20is%20not%20implied.%20Provided%20README%20context%20%28verify%20against%20the%20sources%29%3A%20This%20image%20runs%20qrscan%200.12.0%2C%20an%20offline%20QR%20code%20and%20barcode%20scanner.%20It%20reads%20every%20code%20in%20an%20image%20file%20and%20prints%20a%20JSON%20report.%20It%20has%20no%20HTTP%20service%20and%20makes%20no%20network%20call%3A%20mount%20the%20image%20folder%20read-only%20and%20run%20it%20with%20--network%20none.%20Read%20the%20public%20documentation%20below.%20Explain%20what%20this%20destination%20does%2C%20its%20documented%20installation%20or%20access%20steps%2C%20a%20minimal%20example%20if%20supported%2C%20prerequisites%2C%20limitations%20and%20license.%20Distinguish%20published%20packages%20from%20working%20source%20and%20preparation.%20Cite%20your%20sources%3B%20if%20a%20page%20is%20unavailable%20or%20a%20fact%20cannot%20be%20checked%2C%20say%20so.%20Do%20not%20invent%20installation%20commands%2C%20benchmark%20results%20or%20comparisons.%20Answer%20in%20my%20language.%20Public%20sources%3A%20https%3A%2F%2Fgithub.com%2Fqrcode-ai-com%2Fqrcode-barcode-scanner-rust%2Fblob%2Fmain%2Fdistribution%2Fartifacthub%2FLISTING.md%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-scanner%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-scanner%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-scanner%2Fdocker%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-scanner%2Fdocker%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-generator%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-generator)
[![Claude](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/claude-v2.svg)](https://claude.ai/new?q=Help%20me%20understand%20QR%20Code%20%26%20Barcode%20Scanner%20%C2%B7%20container%20image%20%28distribution%2Fartifacthub%2FLISTING.md%29%20for%20QR%20Code%20%26%20Barcode%20Scanner%2C%20the%20open-source%20scanner.%20Source%20documentation%3B%20publication%20is%20not%20implied.%20Provided%20README%20context%20%28verify%20against%20the%20sources%29%3A%20This%20image%20runs%20qrscan%200.12.0%2C%20an%20offline%20QR%20code%20and%20barcode%20scanner.%20It%20reads%20every%20code%20in%20an%20image%20file%20and%20prints%20a%20JSON%20report.%20It%20has%20no%20HTTP%20service%20and%20makes%20no%20network%20call%3A%20mount%20the%20image%20folder%20read-only%20and%20run%20it%20with%20--network%20none.%20Read%20the%20public%20documentation%20below.%20Explain%20what%20this%20destination%20does%2C%20its%20documented%20installation%20or%20access%20steps%2C%20a%20minimal%20example%20if%20supported%2C%20prerequisites%2C%20limitations%20and%20license.%20Distinguish%20published%20packages%20from%20working%20source%20and%20preparation.%20Cite%20your%20sources%3B%20if%20a%20page%20is%20unavailable%20or%20a%20fact%20cannot%20be%20checked%2C%20say%20so.%20Do%20not%20invent%20installation%20commands%2C%20benchmark%20results%20or%20comparisons.%20Answer%20in%20my%20language.%20Public%20sources%3A%20https%3A%2F%2Fgithub.com%2Fqrcode-ai-com%2Fqrcode-barcode-scanner-rust%2Fblob%2Fmain%2Fdistribution%2Fartifacthub%2FLISTING.md%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-scanner%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-scanner%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-scanner%2Fdocker%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-scanner%2Fdocker%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-generator%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-generator)
[![Gemini](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/gemini-v2.svg)](https://gemini.google.com/)
[![Grok](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/grok-v2.svg)](https://grok.com/?q=Help%20me%20understand%20QR%20Code%20%26%20Barcode%20Scanner%20%C2%B7%20container%20image%20%28distribution%2Fartifacthub%2FLISTING.md%29%20for%20QR%20Code%20%26%20Barcode%20Scanner%2C%20the%20open-source%20scanner.%20Source%20documentation%3B%20publication%20is%20not%20implied.%20Provided%20README%20context%20%28verify%20against%20the%20sources%29%3A%20This%20image%20runs%20qrscan%200.12.0%2C%20an%20offline%20QR%20code%20and%20barcode%20scanner.%20It%20reads%20every%20code%20in%20an%20image%20file%20and%20prints%20a%20JSON%20report.%20It%20has%20no%20HTTP%20service%20and%20makes%20no%20network%20call%3A%20mount%20the%20image%20folder%20read-only%20and%20run%20it%20with%20--network%20none.%20Read%20the%20public%20documentation%20below.%20Explain%20what%20this%20destination%20does%2C%20its%20documented%20installation%20or%20access%20steps%2C%20a%20minimal%20example%20if%20supported%2C%20prerequisites%2C%20limitations%20and%20license.%20Distinguish%20published%20packages%20from%20working%20source%20and%20preparation.%20Cite%20your%20sources%3B%20if%20a%20page%20is%20unavailable%20or%20a%20fact%20cannot%20be%20checked%2C%20say%20so.%20Do%20not%20invent%20installation%20commands%2C%20benchmark%20results%20or%20comparisons.%20Answer%20in%20my%20language.%20Public%20sources%3A%20https%3A%2F%2Fgithub.com%2Fqrcode-ai-com%2Fqrcode-barcode-scanner-rust%2Fblob%2Fmain%2Fdistribution%2Fartifacthub%2FLISTING.md%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-scanner%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-scanner%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-scanner%2Fdocker%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-scanner%2Fdocker%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-generator%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-generator)
[![Perplexity](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/perplexity-v2.svg)](https://www.perplexity.ai/?q=Help%20me%20understand%20QR%20Code%20%26%20Barcode%20Scanner%20%C2%B7%20container%20image%20%28distribution%2Fartifacthub%2FLISTING.md%29%20for%20QR%20Code%20%26%20Barcode%20Scanner%2C%20the%20open-source%20scanner.%20Source%20documentation%3B%20publication%20is%20not%20implied.%20Provided%20README%20context%20%28verify%20against%20the%20sources%29%3A%20This%20image%20runs%20qrscan%200.12.0%2C%20an%20offline%20QR%20code%20and%20barcode%20scanner.%20It%20reads%20every%20code%20in%20an%20image%20file%20and%20prints%20a%20JSON%20report.%20It%20has%20no%20HTTP%20service%20and%20makes%20no%20network%20call%3A%20mount%20the%20image%20folder%20read-only%20and%20run%20it%20with%20--network%20none.%20Read%20the%20public%20documentation%20below.%20Explain%20what%20this%20destination%20does%2C%20its%20documented%20installation%20or%20access%20steps%2C%20a%20minimal%20example%20if%20supported%2C%20prerequisites%2C%20limitations%20and%20license.%20Distinguish%20published%20packages%20from%20working%20source%20and%20preparation.%20Cite%20your%20sources%3B%20if%20a%20page%20is%20unavailable%20or%20a%20fact%20cannot%20be%20checked%2C%20say%20so.%20Do%20not%20invent%20installation%20commands%2C%20benchmark%20results%20or%20comparisons.%20Answer%20in%20my%20language.%20Public%20sources%3A%20https%3A%2F%2Fgithub.com%2Fqrcode-ai-com%2Fqrcode-barcode-scanner-rust%2Fblob%2Fmain%2Fdistribution%2Fartifacthub%2FLISTING.md%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-scanner%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-scanner%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-scanner%2Fdocker%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-scanner%2Fdocker%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fqr-code-generator%20https%3A%2F%2Fqrcode-ai.com%2Fen-US%2Fbarcode-generator)
[![Copilot](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/copilot-v2.svg)](https://copilot.com/)
[![DeepSeek](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/deepseek-v2.svg)](https://chat.deepseek.com/)
[![Meta AI](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/meta-ai-v2.svg)](https://www.meta.ai/)
[![Qwen](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/actions/qwen-v2.svg)](https://qwen.ai/)

Choose an AI assistant to explain this destination using its public sources. Gemini opens gemini.google.com. Gemini, Copilot, DeepSeek, Meta AI and Qwen require pasting the prompt below; the other links include it in their URL. Sign-in or a manual paste may still be required. Check the answer against the documentation.

**Copy the plain-text prompt**

Use the code block's copy control, or select its complete text, then paste it into your assistant.

```text
Help me understand QR Code & Barcode Scanner · container image (distribution/artifacthub/LISTING.md) for QR Code & Barcode Scanner, the open-source scanner. Source documentation; publication is not implied. Provided README context (verify against the sources): This image runs qrscan 0.12.0, an offline QR code and barcode scanner. It reads every code in an image file and prints a JSON report. It has no HTTP service and makes no network call: mount the image folder read-only and run it with --network none. Read the public documentation below. Explain what this destination does, its documented installation or access steps, a minimal example if supported, prerequisites, limitations and license. Distinguish published packages from working source and preparation. Cite your sources; if a page is unavailable or a fact cannot be checked, say so. Do not invent installation commands, benchmark results or comparisons. Answer in my language. Public sources: https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/blob/main/distribution/artifacthub/LISTING.md https://qrcode-ai.com/en-US/qr-code-scanner https://qrcode-ai.com/en-US/barcode-scanner https://qrcode-ai.com/en-US/qr-code-scanner/docker https://qrcode-ai.com/en-US/barcode-scanner/docker https://qrcode-ai.com/en-US/qr-code-generator https://qrcode-ai.com/en-US/barcode-generator
```

<!-- /qrcode-ai-readme-actions:v2 -->

This image runs `qrscan` 0.12.0, an offline QR code and barcode scanner. It reads every code in
an image file and prints a JSON report. It has no HTTP service and makes no network call: mount
the image folder read-only and run it with `--network none`.

You can try the same engine in a browser on the [QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner)
and [barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner) pages. The
[QR code Docker guide](https://qrcode-ai.com/en-US/qr-code-scanner/docker) and the
[barcode Docker guide](https://qrcode-ai.com/en-US/barcode-scanner/docker) explain the container
step by step. To make a code to test with, use the [QR code generator](https://qrcode-ai.com/en-US/qr-code-generator)
or the [barcode generator](https://qrcode-ai.com/en-US/barcode-generator).

## Run it

The image is the unchanged public Linux CLI of release v0.12.0, for Linux AMD64 and ARM64. Put
an image file named `label.png` in the current folder, then run:

```sh
image=ghcr.io/qrcode-ai-com/qrcode-barcode-scanner:0.12.0
docker pull "$image"
docker run --rm --network none --read-only --cap-drop ALL \
  --mount type=bind,src="$PWD",dst=/input,readonly "$image" /input/label.png
```

To get the same bytes on every pull, pull by digest instead of by tag: the
[container guide](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/blob/main/distribution/docker/v0.12/README.md)
records the digest of the multi-platform index and the receipts of its anonymous pulls. The tag
`0.12.0` itself carries the listing details, so this page has no separate listing tag.

## How it works

![Run the scanner in a container from GitHub Container Registry, on Linux AMD64 or ARM64, in three steps: choose the version and architecture, mount the image file, read the result on the host.](https://raw.githubusercontent.com/qrcode-ai-com/.github/main/profile/assets/journey-containers-light.gif?v=87909de2a95f)

The picture shows the three steps of the container route: choose the version and the
architecture, mount the image file read-only, and read the report on the host.

## What it returns

[![A QR code and Code 128 decoded from the same image, each outlined where the engine measured it](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/brand/examples-mixed-light.png?v=7f958679adcc)](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust#examples)

The report lists each code with its format, its text, its raw bytes and its position. A QR code
also gets a scannability score. The exit status is 0 when a code is found, 1 when none is found
and 2 on an error. The picture is a recorded scan of one image that holds a QR code and a Code
128 barcode: both come back in the same report.

## What it reads

[![The code families the engine reads: QR codes, matrix and stacked codes such as Data Matrix, retail barcodes such as EAN-13, and other linear barcodes such as Code 128](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/brand/formats-light.gif?v=bdfe5fc5f9b3)](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust#supported-formats)

It reads QR Code, Micro QR, rMQR, Data Matrix, Aztec, PDF417, MaxiCode, EAN-13, EAN-8, UPC-A,
UPC-E, Code 128, Code 39, Code 93, Codabar, ITF, GS1 DataBar and Telepen. Codes of different
formats in one image come back in one report.

## The same engine in other runtimes

[![One engine in the language you write: Rust on crates.io, Node.js and the browser on npm, Python on PyPI, Go, PHP, and the qrscan command line](https://raw.githubusercontent.com/qrcode-ai-com/qrcode-barcode-scanner-rust/main/docs/assets/brand/runtimes-light.png?v=6dbd5a8cf5ba)](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust#get-started)

The scanner engine also ships as packages for Rust, Node.js, the browser and Python, and as Go
and PHP packages that start `qrscan`. Each package has its own version and license. The
[scanner repository](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust) lists every
route.

## License

The 0.12.0 program in this image is licensed MIT. Two isolated parts of its rxing adapter keep
their Apache-2.0 notices, and the linked crates keep theirs. Those license texts, the third-party
notices and the source archive ship inside the image. The recipe and the build record are in
[the engine repository](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/main/distribution/docker/v0.12).
The earlier tags `0.11.0`, `0.11.0-r1` and `0.11.0-r2` hold the 0.11.0 program, which stays
licensed AGPL-3.0-or-later.

Maintained by **Thibaut Mélen & Nicolas Cella** for **QR Code AI**, a product of
**SuperNovae Studio**.
