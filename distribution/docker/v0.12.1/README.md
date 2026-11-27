# QR Code & Barcode Scanner · OCI 0.12.1

The 0.12.1 recipe packages the **unchanged public Linux CLI** from `v0.12.1`,
under the MIT License. It runs locally and supports QR codes, linear barcodes
and matrix codes, with the mixed QR + Code 128 regression, physical-occurrence
geometry and pipeline 5 reports. Release 0.12.1 adds the `--formats` option
and reports score contract 6. There is no scanner HTTP service and no runtime
download.

This folder is separate from the [0.12 recipe](../v0.12/README.md) because the
release BOM of the published 0.12.0 image pins that folder's files by hash.
Nothing there changes for 0.12.1.

## Run the public image

The [GHCR image 0.12.1](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/pkgs/container/qrcode-barcode-scanner)
supports Linux AMD64 and ARM64. The digest below names the verified multi-platform
index. Put an input image named `label.png` in the current directory before
running the command.

```sh
image=ghcr.io/qrcode-ai-com/qrcode-barcode-scanner@sha256:1d9f3a3985b7198a8a2f3437289f2190735c550d9ef46baebc494e7e13142558
docker pull "$image"
docker run --rm --network none --read-only --cap-drop ALL \
  --mount type=bind,src="$PWD",dst=/input,readonly "$image" /input/label.png --pretty
```

The index names the AMD64 manifest `sha256:d697bef525e7de81b17e77cc8a3cadb907f0f8083d9541cd40880d07a99b37e4`
and the ARM64 manifest `sha256:7307b11160317d32b95abb5a93bea12a5b55408e993a5b8c4302fb4982f942df`.
The [tag run](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/actions/runs/45918280379) pushed `0.12.1-amd64`, `0.12.1-arm64` and then
the index `0.12.1`, so the newest package version is the version tag.
[Anonymous public pulls](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/actions/runs/45918697977) and exact scans passed on both
native architectures. The 0.12.0 image and its tags stay published; see the
[0.12 recipe](../v0.12/README.md#run-the-public-image). The 0.11.0 image and its
tags stay published under the AGPL; see the
[0.11 recipe](../v0.11/README.md#run-the-public-image).

## Build and verify

Run input preparation without a GitHub token. `inputs.json` pins the published
SHA256SUMS, both Linux archives, the source archive, both published crates and
the Debian base index. Every source and binary hash is checked before
packaging. Only this generated context enters Docker; no source checkout or
host secrets are copied. The binary's original Rust 1.99.1 build metadata and
licenses ship with the image. No Cargo build or installer is needed.

```bash
env -u GH_TOKEN -u GITHUB_TOKEN python3 distribution/docker/v0.12.1/prepare.py \
  --assets /tmp/qrscan-assets --out /tmp/qrscan-context \
  --receipt /tmp/qrscan-preparation.json
```

On a **native Linux** AMD64 or ARM64 producer, set `ARCHITECTURE` accordingly
and `PACKAGING_REVISION` to the reviewed packaging commit (separate from the
engine commit). The owning `distribution-checks` workflow runs:

```bash
docker build --no-cache --network none \
  -f distribution/docker/v0.12.1/Dockerfile \
  --platform "linux/$ARCHITECTURE" --build-arg "PACKAGING_REVISION=$PACKAGING_REVISION" \
  -t qrscan:qualified /tmp/qrscan-context
python3 distribution/docker/v0.12.1/verify.py qrscan:qualified fixtures/clean/gen_v5_q.png \
  --expected-platform "linux/$ARCHITECTURE" --packaging-revision "$PACKAGING_REVISION" \
  --native --receipt /tmp/qrscan-consumer.json
python3 distribution/docker/v0.12.1/record.py qrscan:qualified \
  --consumer /tmp/qrscan-consumer.json --out /tmp/qrscan-export
```

The verifier executes the shared exact-content truth set, mixed Code 128 + QR
cases in fast/frame/full, versions, scores, empty/error exits and mounted paths.
It checks the `MIT` license label, version `0.12.1` and engine revision
`5b2c580c78b0693e58909f889b66f24fc1c548b1`. It also reads the mixed QR + Code
128 input with `--formats qr_code`: only the QR code comes back, `trace.formats`
names what was looked for, and an unknown name exits 2 with `QRS-006`. Every
scan uses a read-only filesystem and input mount, non-root user 65532, no
capabilities and `--network none`. The native guard refuses emulation as native
producer evidence. The export records the tested image's config, raw layers,
binary and source hashes without rebuilding it. `record.py` pins every file
that makes or judges the image; this README is left out because it records the
publication.

## Release boundary

Run the native two-architecture producer on `main` first, record its official
artifact IDs and ZIP digests, then freeze those exact exports into a reviewed
0.12.1 release BOM. The independent `oci-v0.12.1` tag and the `container`
environment gate the GHCR upload. No `latest` tag or Docker Hub upload is part
of this delivery. Publication is complete only after anonymous pulls by
immutable index digest pass on both native architectures. Do not alter
`v0.12.1`, its public CLI assets, or the published 0.12.0 and 0.11.0 images and
their tags.

[QR Code AI](https://qrcode-ai.com/) ·
[QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner) ·
[Barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner) ·
[Source and release](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/releases/tag/v0.12.1)
