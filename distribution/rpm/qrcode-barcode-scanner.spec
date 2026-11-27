Name:           qrcode-barcode-scanner
Version:        0.12.2
Release:        1%{?dist}
Summary:        Offline QR code and barcode scanner
# Both release archives retain the complete upstream license expressions.
# Apache-2.0 and MIT satisfy the dual-licensed alternatives in the payload.
License:        MIT AND Apache-2.0 AND BSD-3-Clause AND ISC AND Zlib
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
  320e13c0ffd87953b9b2002dbe9a5cd23cb534c12dbd8206f0aa7e88640435f6 '%{SOURCE0}' \
  7c0258697839d8aa9b54602ec6a56d9961a5e9ed793419b8bd751a83f22f0c79 '%{SOURCE1}' \
  ceed71c46c7a8b908d53ad79a7b7fb67e8bc04c6e4b30e61dbfd9bff6db402f8 '%{SOURCE2}' \
  | sha256sum --strict --check

%ifarch x86_64
%global cli_input %{SOURCE0}
%global executable_sha256 eca19b7eb8e407d19380d5d4d9d11ed925b06bc36663fbc9d87d8f81fd4900f7
%endif
%ifarch aarch64
%global cli_input %{SOURCE1}
%global executable_sha256 175f69309b439f27bdda855e523bf9f4c32a7540f8db8476d99007b8e2de459b
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
* Fri Nov 27 2026 QR Code AI <contact@qrcode-ai.com> - 0.12.2-1
- Package the published 0.12.2 CLI for Fedora.

* Thu Nov 26 2026 QR Code AI <contact@qrcode-ai.com> - 0.12.1-1
- Package the published 0.12.1 CLI for Fedora.

* Sun Nov 22 2026 QR Code AI <contact@qrcode-ai.com> - 0.12.0-1
- Package the published 0.12.0 CLI for Fedora.

* Mon Nov 09 2026 QR Code AI <contact@qrcode-ai.com> - 0.11.0-1
- Package the published 0.11.0 CLI for Fedora.
