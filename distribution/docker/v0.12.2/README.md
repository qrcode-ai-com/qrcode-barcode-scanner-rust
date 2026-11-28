# QR Code & Barcode Scanner · OCI 0.12.2

The 0.12.2 recipe packages the **unchanged public Linux CLI** from `v0.12.2`,
under the MIT License. It runs locally and reads QR codes, linear barcodes and
matrix codes. There is no scanner HTTP service and no runtime download. What
the release changes in the scanner itself is in the
[changelog](../../../CHANGELOG.md).

This folder is separate from the [0.12.1 recipe](../v0.12.1/README.md) because
the release BOM of the published 0.12.1 image pins that folder's files by hash.
Nothing there changes for 0.12.2.

## What changes in the image

The scanner, its options and the command that runs it are the same. The system
underneath is not.

- **A smaller base.** The 0.11.0, 0.12.0 and 0.12.1 images are built on Debian
  12 (`bookworm-slim`), a general-purpose system of 88 packages. The binary needs
  the C library and the compiler runtime it links, and nothing else. This image
  is built on Chainguard's `glibc-dynamic`, from the Wolfi distribution: seven
  packages. `inputs.json` pins the base by its multi-platform index digest and
  lists the seven packages with their versions.
- **No known vulnerability on the day it is built.** The producer scans each
  image it has just tested with [Trivy](https://trivy.dev/) 0.76.2, pinned by
  digest, and stops on any finding: any severity, fixable or not. On
  27 November 2026 the same scanner listed 250 findings in the published 0.12.1
  image, on each platform, all of them in packages of its Debian base.
- **No shell and no package manager.** `docker run --entrypoint sh …` starts
  nothing in this image, and a Dockerfile that builds `FROM` it cannot use
  `RUN`. [Read a file of the image](#read-a-file-of-the-image) shows how to
  look inside without one.
- **The working directory belongs to root.** `/data` is still the working
  directory. In 0.12.1 it belonged to the image's user; here that user, 65532,
  owns nothing the recipe adds.

A scan is of its day. A package of the base can receive a finding after the
image is published, and another scanner, or the same one with a later
database, can then report it. The published image is never edited: the answer
to a finding is a new image. See [Scan again later](#scan-again-later).

## Run the public image

The [GHCR image 0.12.2](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/pkgs/container/qrcode-barcode-scanner)
supports Linux AMD64 and ARM64. The digest below names the verified multi-platform
index. Put an input image named `label.png` in the current directory before
running the command.

```sh
image=ghcr.io/qrcode-ai-com/qrcode-barcode-scanner@sha256:fbf5c619343241a7e5273225178dbc8a10447c5dce313f3a67bb2bfe59ac1479
docker pull "$image"
docker run --rm --network none --read-only --cap-drop ALL \
  --mount type=bind,src="$PWD",dst=/input,readonly "$image" /input/label.png --pretty
```

The index names the AMD64 manifest `sha256:47123b2da3d0de07ac479b784f6a1330ac08259b302b7e0347f2f3f7ae9d90ed`
and the ARM64 manifest `sha256:9a904855232fa0484fd271bcd544678393908ad58517ce8c7ff6eea8cad6a975`.
The [tag run](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/actions/runs/46152621680) pushed `0.12.2-amd64`, `0.12.2-arm64` and then
the index `0.12.2`, so the newest package version is the version tag.
[Anonymous public pulls](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/actions/runs/46152851945) and exact scans passed on both
native architectures. The 0.12.1 and 0.12.0 images and their tags stay
published; see the [0.12.1 recipe](../v0.12.1/README.md#run-the-public-image). The
0.11.0 image and its tags stay published under the AGPL; see the
[0.11 recipe](../v0.11/README.md#run-the-public-image).

### Read a file of the image

Without a shell, create a container that never starts and copy the file out
of it. This reads the source notice, which names the base and where the
sources of its packages are:

```sh
container=$(docker create "$image")
docker cp "$container":/usr/share/doc/qrscan/SOURCE.md .
docker rm "$container"
```

## Build and verify

Run input preparation without a GitHub token. `inputs.json` pins the published
SHA256SUMS, both Linux archives, the source archive, both published crates,
the base index with its packages, and the scanner image. Every source and
binary hash is checked before packaging. Only this generated context enters
Docker; no source checkout or host secrets are copied. The binary's original
build metadata and licenses ship with the image. No Cargo build or installer
is needed.

```bash
env -u GH_TOKEN -u GITHUB_TOKEN python3 distribution/docker/v0.12.2/prepare.py \
  --assets /tmp/qrscan-assets --out /tmp/qrscan-context \
  --receipt /tmp/qrscan-preparation.json
```

On a **native Linux** AMD64 or ARM64 producer, set `ARCHITECTURE` accordingly
and `PACKAGING_REVISION` to the reviewed packaging commit (separate from the
engine commit). The owning `distribution-checks` workflow runs:

```bash
docker build --no-cache --network none \
  -f distribution/docker/v0.12.2/Dockerfile \
  --platform "linux/$ARCHITECTURE" --build-arg "PACKAGING_REVISION=$PACKAGING_REVISION" \
  -t qrscan:qualified /tmp/qrscan-context
python3 distribution/docker/v0.12.2/verify.py qrscan:qualified fixtures/clean/gen_v5_q.png \
  --expected-platform "linux/$ARCHITECTURE" --packaging-revision "$PACKAGING_REVISION" \
  --native --receipt /tmp/qrscan-consumer.json
python3 distribution/docker/v0.12.2/scan.py qrscan:qualified --receipt /tmp/qrscan-scan.json
python3 distribution/docker/v0.12.2/record.py qrscan:qualified \
  --consumer /tmp/qrscan-consumer.json --scan /tmp/qrscan-scan.json --out /tmp/qrscan-export
```

### What the verifier checks

`verify.py` runs the shared exact-content truth set, mixed Code 128 + QR cases
in fast/frame/full, versions, scores, empty/error exits and mounted paths. It
checks the `MIT` license label and the version and engine revision that
`inputs.json` pins. It also reads the mixed QR + Code 128 input with
`--formats qr_code`: only the QR code comes back, `trace.formats` names what
was looked for, and an unknown name exits 2 with `QRS-006`. Every scan uses a
read-only filesystem and input mount, non-root user 65532, no capabilities and
`--network none`. The native guard refuses emulation as native producer
evidence.

The image has no shell, so nothing but `qrscan` runs in it. The rest is read
from the host: the verifier creates a container that never starts, exports its
filesystem as one tar stream and reads it in memory. From that stream it
checks:

- the SHA-256 of the binary, of the source archive and of both crates against
  `inputs.json`, that `build-info.json` describes that binary and that the
  installed `SOURCE.md` is this folder's;
- that no path is named like a shell or a package manager (`sh`, `bash`,
  `busybox`, `apk`, `apt`, `dpkg` and their kin), as a file or as a link, and
  that asking the runtime for `sh` fails;
- that the only files that can be executed are `qrscan` and three files of
  the base (`ld.so`, `ldconfig` and a hook script whose interpreter is not in
  the image), and that none is setuid or setgid;
- that the image's user can change nothing but three directories of the base
  (`/home/nonroot`, `/tmp`, `/var/tmp`), which a read-only root filesystem
  closes, and that everything the recipe adds belongs to root with fixed modes;
- that the system is Wolfi and its installed packages are exactly the seven
  that `inputs.json` lists, each with its SPDX file.

`verify.py --self-test` runs the judge of that list on a described image and
on images that each differ from it by one fault.

### What the scan checks

`scan.py` saves the tested image to a file and gives it to the pinned scanner.
The scanner gets neither the Docker socket nor a credential. It first fetches
its database with nothing mounted but an empty cache, then reads the image
with no network. The scan passes when the scanner saw the seven pinned
packages, built for the image's platform, its database is less than three days
old and it lists no finding. A report with no package in it fails: it would
prove nothing. The receipt names the scanner, the date of its database and
what it saw; `record.py` refuses an export whose scan is of another image and
puts the receipt in the export.

`record.py` pins every file that makes or judges the image. This README and
`published.json` are left out because they record the publication.

## Scan again later

Once the image is published, `published.json` in this folder records its index
digest. The weekly `deep-checks` workflow then runs
`scan.py --published`: the same pinned scanner, with the database of that day,
reads both platforms of the published image from the registry by that digest.
A finding makes the run fail and its receipt lists it. Until `published.json`
exists the job prints a notice and scans nothing.

## Release boundary

Run the native two-architecture producer on `main` first, record its official
artifact IDs and ZIP digests, then freeze those exact exports into a reviewed
0.12.2 release BOM. The independent `oci-v0.12.2` tag and the `container`
environment gate the GHCR upload. No `latest` tag or Docker Hub upload is part
of this delivery. Publication is complete only after anonymous pulls by
immutable index digest pass on both native architectures; `published.json`
then records that digest. Do not alter `v0.12.2`, its public CLI assets, or the
published 0.12.1, 0.12.0 and 0.11.0 images and their tags.

[QR Code AI](https://qrcode-ai.com/) ·
[QR code scanner](https://qrcode-ai.com/en-US/qr-code-scanner) ·
[Barcode scanner](https://qrcode-ai.com/en-US/barcode-scanner) ·
[Source and release](https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/releases/tag/v0.12.2)
