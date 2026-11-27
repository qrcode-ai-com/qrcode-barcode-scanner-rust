# The MCP server @qrcode-ai-com/qrcode-barcode-scanner-mcp 0.3.4, as Glama builds and runs it.
# It installs the published npm package from package-lock.json, compiles nothing and speaks MCP
# over stdio. The native scanner 0.12.1 comes from its pinned linux-x64-gnu or linux-arm64-gnu
# npm package, so the base is glibc, not musl: Chainguard's Node image (Wolfi, Node.js 26 LTS, npm
# and a busybox shell, no package manager), pinned by the digest of its amd64 and arm64 index.
# Chainguard's free tier publishes this image as latest only: moving the pin moves the digest,
# and the Node.js version behind the new digest must be read again. Scans need no network access.
FROM cgr.dev/chainguard/node:latest@sha256:74b28494d25c04046835cf2ebb354c992129f9c73a633f051090889d14e0b6f6

ENV NODE_ENV=production \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false

# The base runs as its non-root user: root installs, so the server cannot change what it runs.
USER root
WORKDIR /opt/qrscan-mcp
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts \
    && npm cache clean --force \
    && test "$(node -p 'require("@qrcode-ai-com/qrcode-barcode-scanner-mcp/package.json").version')" = 0.3.4

# node, the base image's non-root user. The server reads stdin and writes nothing to disk.
USER 65532:65532
ENTRYPOINT ["node", "/opt/qrscan-mcp/node_modules/@qrcode-ai-com/qrcode-barcode-scanner-mcp/src/cli.mjs"]
