#!/usr/bin/env bash
# Wrap the verified 0.12.0 CLI in a Debian binary package.
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 amd64|arm64 INPUT_DIRECTORY OUTPUT_DIRECTORY" >&2
  exit 2
fi

architecture=$1
case "$architecture" in
  amd64)
    target=x86_64-unknown-linux-gnu
    binary_sha256=cbc1ac6456a0a791ae636da55388f981dcbd740081af79abb680c3a876be5357
    ;;
  arm64)
    target=aarch64-unknown-linux-gnu
    binary_sha256=e400b7464357f35d43bae7172d5408a5e412fbd90a371577baca9473746fbe55
    ;;
  *)
    echo "Unsupported Debian architecture: $architecture" >&2
    exit 2
    ;;
esac

package=qrcode-barcode-scanner
version=0.12.0
archive_stem="$package-cli-$version-$target"
source_archive="$package-cli-$version-source.tar.gz"
checksums="$package-cli-$version-SHA256SUMS"
checksums_sha256=f3d7027a558992f9c07232110d06ee3c07e84d877120165b0e072429cb486691
input_dir=$(cd -- "$2" && pwd)
output_dir=$(cd -- "$3" && pwd)
filename="${package}_${version}-1_${architecture}.deb"

(
  cd -- "$input_dir"
  printf '%s  %s\n' "$checksums_sha256" "$checksums" | sha256sum --strict --check
  for name in "$archive_stem.tar.gz" "$source_archive"; do
    awk -v file="$name" '$2 == file { print }' "$checksums" | sha256sum --strict --check
  done
)

stage=$(mktemp -d "$output_dir/.deb-stage.XXXXXX")
trap 'find "$stage" -depth -delete' EXIT
root="$stage/package"
docdir="$root/usr/share/doc/$package"
install -d "$root/DEBIAN" "$root/usr/bin" "$docdir"
archive="$input_dir/$archive_stem.tar.gz"
tar -xOzf "$archive" "$archive_stem/qrscan" >"$root/usr/bin/qrscan"
chmod 0755 "$root/usr/bin/qrscan"
printf '%s  %s\n' "$binary_sha256" "$root/usr/bin/qrscan" | sha256sum --strict --check

for file in COPYRIGHT-rust-std.html LICENSE LICENSE-APACHE-2.0 LICENSING.md README.md SOURCE.md THIRD-PARTY-LICENSES.txt THIRD-PARTY.md build-info.json; do
  tar -xOzf "$archive" "$archive_stem/$file" >"$docdir/$file"
done

cat >"$docdir/copyright" <<'COPYRIGHT'
QR Code & Barcode Scanner is distributed under the MIT License. See LICENSE
and LICENSING.md in this directory for the license text and details.

THIRD-PARTY.md, THIRD-PARTY-LICENSES.txt, LICENSE-APACHE-2.0 and
COPYRIGHT-rust-std.html retain upstream third-party notices and licenses.

Corresponding source for the executable and its build inputs is identified
in SOURCE.md and build-info.json. The release source archive is available at:
https://github.com/qrcode-ai-com/qrcode-barcode-scanner/releases/download/v0.12.0/qrcode-barcode-scanner-cli-0.12.0-source.tar.gz
COPYRIGHT

gzip -n -9 >"$docdir/changelog.Debian.gz" <<'CHANGELOG'
qrcode-barcode-scanner (0.12.0-1) stable; urgency=medium

  * Package the official QR Code & Barcode Scanner 0.12.0 Linux CLI.

 -- QR Code AI <contact@qrcode-ai.com>  Sun, 22 Nov 2026 19:16:13 +0000
CHANGELOG

installed_size=$(find "$root/usr" -type f -printf '%s\n' \
  | awk '{ size += int(($1 + 1023) / 1024) } END { print size }')
cat >"$root/DEBIAN/control" <<CONTROL
Package: $package
Version: $version-1
Section: utils
Priority: optional
Architecture: $architecture
Maintainer: QR Code AI <contact@qrcode-ai.com>
Depends: libc6 (>= 2.28)
Installed-Size: $installed_size
Homepage: https://qrcode-ai.com/
Description: offline QR code and barcode scanner
 qrscan decodes QR codes and barcodes from images and reports results as JSON.
 It also provides scannability diagnostics for QR codes.
 .
 Web tools: https://qrcode-ai.com/en-US/qr-code-scanner
 and https://qrcode-ai.com/en-US/barcode-scanner
CONTROL

# Use the packaging changelog timestamp and retain root-owned payload files.
export SOURCE_DATE_EPOCH=1794225801
export TZ=UTC LC_ALL=C
find "$root" -type d -exec chmod 0755 {} +
find "$root" -type f ! -path "$root/usr/bin/qrscan" -exec chmod 0644 {} +
find "$root" -exec touch -d "@$SOURCE_DATE_EPOCH" {} +
dpkg-deb --root-owner-group -Zxz -z9 --build "$root" "$stage/$filename"
ln -T -- "$stage/$filename" "$output_dir/$filename"
