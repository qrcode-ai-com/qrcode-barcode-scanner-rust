# QR Code & Barcode Scanner · OCI 0.12

The 0.12 recipe packages the **unchanged public Linux CLI** from `v0.12.0`, the
first engine release under the MIT License. It runs locally and supports QR
codes, linear barcodes and matrix codes, with the mixed QR + Code 128
regression, physical-occurrence geometry and pipeline 5 reports. There is no
scanner HTTP service and no runtime download.

## Run the image

The image target is `ghcr.io/qrcode-ai-com/qrcode-barcode-scanner`, tag `0.12.0`,
for Linux AMD64 and ARM64. This recipe is prepared; the image is not published
until the release boundary below is complete, and this section then names the
verified multi-platform index digest. Until then, the published image is
[0.11.0](../v0.11/README.md#run-the-public-image).

## Build and verify

Run input preparation without a GitHub token. `inputs.json` pins the published
SHA256SUMS, both Linux archives, the source archive, both published crates and
the Debian base index. Every source and binary hash is checked before
packaging. Only this generated context enters Docker; no source checkout or
host secrets are copied. The binary's original Rust 1.99.1 build metadata and
licenses ship with the image. No Cargo build or installer is needed.

```bash
env -u GH_TOKEN -u GITHUB_TOKEN python3 distribution/docker/v0.12/prepare.py \
  --assets /tmp/qrscan-assets --out /tmp/qrscan-context \
  --receipt /tmp/qrscan-preparation.json
```

On a **native Linux** AMD64 or ARM64 producer, set `ARCHITECTURE` accordingly
and `PACKAGING_REVISION` to the reviewed packaging commit (separate from the
engine commit). The owning `distribution-checks` workflow runs:

```bash
docker build --no-cache --network none \
  -f distribution/docker/v0.12/Dockerfile \
  --platform "linux/$ARCHITECTURE" --build-arg "PACKAGING_REVISION=$PACKAGING_REVISION" \
  -t qrscan:qualified /tmp/qrscan-context
python3 distribution/docker/v0.12/verify.py qrscan:qualified fixtures/clean/gen_v5_q.png \
  --expected-platform "linux/$ARCHITECTURE" --packaging-revision "$PACKAGING_REVISION" \
  --native --receipt /tmp/qrscan-consumer.json
python3 distribution/docker/v0.12/record.py qrscan:qualified \
  --consumer /tmp/qrscan-consumer.json --out /tmp/qrscan-export
```

The verifier executes the shared exact-content truth set, mixed Code 128 + QR
cases in fast/frame/full, versions, scores, empty/error exits and mounted paths.
It checks the `MIT` license label, version `0.12.0` and engine revision
`897dd50cdf27cbde54d408bf65e1ca4622035d42`. Every scan uses a read-only
filesystem and input mount, non-root user 65532, no capabilities and
`--network none`. The native guard refuses emulation as native producer
evidence. The export records the tested image's config, raw layers, binary and
source hashes without rebuilding it. `record.py` pins every file that makes or
judges the image; this README is left out because it records the publication.

## Release boundary

Run the native two-architecture producer on `main` first, record its official
artifact IDs and ZIP digests, then freeze those exact exports into a reviewed
0.12 release BOM. The independent `oci-v0.12.0` tag and the `container`
environment gate the GHCR upload. No `latest` tag or Docker Hub upload is part
of this delivery. Publication is complete only after anonymous pulls by
immutable index digest pass on both native architectures. Do not alter
`v0.12.0`, its public CLI assets, or the published 0.11.0 image and its tags.

[QR Code AI](https://qrcode-ai.com/) ·
[QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner) ·
[Barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner) ·
[Source and release](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/releases/tag/v0.12.0)
