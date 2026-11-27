# Repackage the already-qualified public v0.12.2 binary; never compile at publish time.
# prepare.py verifies the release manifest, binary metadata and source archives.
# The base holds the C library the binary links and nothing to run beside it: no shell and
# no package manager. verify.py pins its package list; scan.py refuses any known finding.
FROM cgr.dev/chainguard/glibc-dynamic@sha256:a96ba3c8d5ffc646e1092c03d72000b5e2ccd9f6cda695d6342a0e31ce4d52ee
ARG TARGETARCH
ARG PACKAGING_REVISION
LABEL org.opencontainers.image.title="QR Code & Barcode Scanner" \
    org.opencontainers.image.description="Local QR code, barcode and matrix-code scanning. Mount input read-only and run qrscan without network access." \
    org.opencontainers.image.version="0.12.2" \
    org.opencontainers.image.revision="d0fcf8a27410f5ee182aab6477624e3fc52c4aa5" \
    org.opencontainers.image.source="https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust" \
    org.opencontainers.image.url="https://qrcode-ai.com/" \
    org.opencontainers.image.documentation="https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/main/distribution/docker/v0.12.2" \
    org.opencontainers.image.licenses="MIT" \
    io.qrcode-ai.scanner.packaging-revision="${PACKAGING_REVISION}"
# The base runs as 65532. The working directory is made as root, so the user the image runs
# as owns nothing the recipe adds.
USER 0:0
WORKDIR /data
COPY ${TARGETARCH}/qrscan /usr/local/bin/qrscan
COPY ${TARGETARCH}/docs/ /usr/share/doc/qrscan/
COPY source/ /usr/share/doc/qrscan/source/
COPY SOURCE.md /usr/share/doc/qrscan/SOURCE.md
USER 65532:65532
ENV RAYON_NUM_THREADS=2
ENTRYPOINT ["/usr/local/bin/qrscan"]
CMD ["--help"]
