Name:           qrcode-barcode-scanner
Version:        0.12.0
Release:        1%{?dist}
Summary:        Offline QR code and barcode scanner
# Both release archives retain the complete upstream license expressions.
# Apache-2.0 and MIT satisfy the dual-licensed alternatives in the payload.
License:        AGPL-3.0-or-later AND Apache-2.0 AND BSD-3-Clause AND ISC AND MIT AND Zlib
URL:            https://qrcode-ai.com/
ExclusiveArch:  x86_64 aarch64

%global upstream https://github.com/qrcode-ai-com/qrcode-barcode-scanner
%global archive qrcode-barcode-scanner-cli-%{version}
Source0:        %{upstream}/releases/download/v%{version}/%{archive}-x86_64-unknown-linux-gnu.tar.gz
Source1:        %{upstream}/releases/download/v%{version}/%{archive}-aarch64-unknown-linux-gnu.tar.gz
Source2:        %{upstream}/releases/download/v%{version}/%{archive}-source.tar.gz
BuildRequires:  coreutils
BuildRequires:  gzip
BuildRequires:  tar
Requires:       glibc >= 2.28

# The prebuilt executable must remain byte-identical to the published CLI.
%global debug_package %{nil}
%global __os_install_post %{nil}
%global _build_id_links none
%global source_date_epoch_from_changelog 1
%global use_source_date_epoch_as_buildtime 1
%global build_mtime_policy clamp_to_source_date_epoch

%description
qrscan decodes QR codes and barcodes from images and returns JSON.
It also provides scannability diagnostics for QR codes.

Web tools: https://qrcode-ai.com/en-US/qr-code-scanner and
https://qrcode-ai.com/en-US/barcode-scanner

%prep
printf '%s  %s\n' \
  1e6aea17507d22b13a370de3531697264dc748f34a1039425e892c3ee008217c '%{SOURCE0}' \
  17512dea779823b0ab26e1556966c9ac6d8be0d544a99dbbb43edc4b47d57d6a '%{SOURCE1}' \
  642f1cd4abcf16c2100eb8fdc2a84691a2af3d78549af4efce7398c2c6a78e17 '%{SOURCE2}' \
  | sha256sum --strict --check

%ifarch x86_64
%global cli_input %{SOURCE0}
%global executable_sha256 cbc1ac6456a0a791ae636da55388f981dcbd740081af79abb680c3a876be5357
%endif
%ifarch aarch64
%global cli_input %{SOURCE1}
%global executable_sha256 e400b7464357f35d43bae7172d5408a5e412fbd90a371577baca9473746fbe55
%endif
%global cli_archive %{archive}-%{_arch}-unknown-linux-gnu

mkdir '%{cli_archive}'
for name in qrscan LICENSE LICENSE-APACHE-2.0 LICENSING.md THIRD-PARTY.md \
  THIRD-PARTY-LICENSES.txt COPYRIGHT-rust-std.html SOURCE.md README.md build-info.json; do
  tar -xOzf '%{cli_input}' "%{cli_archive}/$name" >"%{cli_archive}/$name"
done

%install
cd '%{cli_archive}'
printf '%s  qrscan\n' '%{executable_sha256}' | sha256sum --strict --check
install -Dm0755 qrscan '%{buildroot}%{_bindir}/qrscan'
install -d '%{buildroot}%{_licensedir}/%{name}' '%{buildroot}%{_docdir}/%{name}'
install -m0644 LICENSE LICENSE-APACHE-2.0 LICENSING.md THIRD-PARTY.md \
  THIRD-PARTY-LICENSES.txt COPYRIGHT-rust-std.html SOURCE.md \
  '%{buildroot}%{_licensedir}/%{name}/'
install -m0644 README.md build-info.json '%{buildroot}%{_docdir}/%{name}/'

%files
%{_bindir}/qrscan
%license %{_licensedir}/%{name}
%doc %{_docdir}/%{name}

%changelog
* Sun Nov 22 2026 QR Code AI <contact@qrcode-ai.com> - 0.12.0-1
- Package the published 0.12.0 CLI for Fedora.

* Mon Nov 09 2026 QR Code AI <contact@qrcode-ai.com> - 0.11.0-1
- Package the published 0.11.0 CLI for Fedora.
