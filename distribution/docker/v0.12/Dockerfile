# Repackage the already-qualified public v0.12.0 binary; never compile at publish time.
# prepare.py verifies the release manifest, binary metadata and source archives.
FROM debian:bookworm-slim@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc
ARG TARGETARCH
ARG PACKAGING_REVISION
LABEL org.opencontainers.image.title="QR Code & Barcode Scanner" \
    org.opencontainers.image.description="Local QR code, barcode and matrix-code scanning. Mount input read-only and run qrscan without network access." \
    org.opencontainers.image.version="0.12.0" \
    org.opencontainers.image.revision="897dd50cdf27cbde54d408bf65e1ca4622035d42" \
    org.opencontainers.image.source="https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust" \
    org.opencontainers.image.url="https://qrcode-ai.com/" \
    org.opencontainers.image.documentation="https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/main/distribution/docker/v0.12" \
    org.opencontainers.image.licenses="MIT" \
    io.qrcode-ai.scanner.packaging-revision="${PACKAGING_REVISION}"
COPY ${TARGETARCH}/qrscan /usr/local/bin/qrscan
COPY ${TARGETARCH}/docs/ /usr/share/doc/qrscan/
COPY source/ /usr/share/doc/qrscan/source/
COPY SOURCE.md /usr/share/doc/qrscan/SOURCE.md
USER 65532:65532
WORKDIR /data
ENV RAYON_NUM_THREADS=2
ENTRYPOINT ["/usr/local/bin/qrscan"]
CMD ["--help"]
