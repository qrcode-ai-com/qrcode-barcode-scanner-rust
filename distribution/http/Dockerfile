# The QR Code & Barcode Scanner HTTP service. It installs the published engine 0.12.2 from npm,
# pinned with its six native packages by package-lock.json, compiles nothing and serves
# server.mjs as a non-root user. The native engine comes from its linux-x64-gnu or
# linux-arm64-gnu package, so the base is glibc: Chainguard's Node.js image, built on Wolfi, with
# Node.js 26, npm and a busybox shell, and no package manager. Its multi-platform index is pinned by
# digest. npm reaches the registry while the image is built; the running service needs no network
# and writes no file.
FROM cgr.dev/chainguard/node:latest@sha256:74b28494d25c04046835cf2ebb354c992129f9c73a633f051090889d14e0b6f6

ARG SOURCE_REVISION=""
LABEL org.opencontainers.image.title="QR Code & Barcode Scanner HTTP service" \
      org.opencontainers.image.description="Scan QR codes and barcodes over HTTP with the open-source scanner engine 0.12.2. Images are scanned in memory and never stored." \
      org.opencontainers.image.version="0.1.4" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust" \
      org.opencontainers.image.url="https://qrcode-ai.com/" \
      org.opencontainers.image.documentation="https://github.com/qrcode-ai-com/qrcode-barcode-scanner-rust/tree/main/distribution/http" \
      org.opencontainers.image.vendor="QR Code AI" \
      org.opencontainers.image.revision="${SOURCE_REVISION}"

ENV NODE_ENV=production \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false \
    PORT=8080

# The base runs as its own user 65532; the install writes the service's folder as root.
USER root
WORKDIR /opt/qrscan-http
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts \
    && npm cache clean --force \
    && test "$(node -p 'require("@qrcode-ai-com/qrcode-barcode-scanner/package.json").version')" = 0.12.2
# SOURCE.json names the engine commit this tree was generated from; the service names it as its source.
COPY server.mjs LICENSE LICENSE-NOTES.md SOURCE.json* ./
COPY licenses/ ./licenses/

USER 1000:1000
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:' + process.env.PORT + '/healthz').then((r) => process.exit(r.ok ? 0 : 1), () => process.exit(1))"]
# The base's entrypoint is node itself: clear it, so the command below is the whole command.
ENTRYPOINT []
CMD ["node", "/opt/qrscan-http/server.mjs"]
