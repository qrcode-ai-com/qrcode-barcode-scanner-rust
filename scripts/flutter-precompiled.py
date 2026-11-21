#!/usr/bin/env python3
"""Sign, publish and verify the Flutter package's precompiled binaries.

cargokit, which builds the Rust library inside a consuming Flutter app, can
download a precompiled library instead: from `<url_prefix><crate hash>/<rust
target>_<artifact>`, with `<...>.sig` beside it, a raw 64-byte Ed25519
signature it checks against the `public_key` of the package's
rust/cargokit.yaml before it uses the file. A missing file or a bad signature
makes it build from source, which needs rustup. It downloads by default only
when rustup is absent; an app with rustup opts in with
`use_precompiled_binaries: true` in a cargokit_options.yaml at its root.

The private key never reaches GitHub: no workflow here reads a secret or
creates a release (scripts/check-publish-guards.py). CI builds the binaries
unsigned (.github/workflows/flutter-precompiled.yml, on the v* tag); the owner
signs them on their own machine with the seed kept in the macOS Keychain and
creates the `precompiled_<crate hash>` release.

  flutter-precompiled.py hash [--manifest-dir DIR]
      the crate hash, as cargokit computes it
  flutter-precompiled.py keygen [--key-file PATH] [--config PATH] [--url-prefix URL]
      a new Ed25519 key: the seed goes into the Keychain (or, for CI's
      throwaway key, to a new 0600 --key-file), the public key into the config
  flutter-precompiled.py check-config [--config PATH] [--url-prefix URL]
  flutter-precompiled.py merge --out DIR DIR...
      one unsigned set from the per-platform build outputs
  flutter-precompiled.py sign --dir DIR [--key-file PATH] [--config PATH] [--manifest-dir DIR]
  flutter-precompiled.py verify --dir DIR [--config PATH]
  flutter-precompiled.py verify-remote --manifest-dir DIR [--targets release|T,T]
      download every file and signature from the config's url_prefix
  flutter-precompiled.py path-without-rust --shadow DIR
      a PATH that reaches no rustup, cargo or rustc, for consumer checks
  flutter-precompiled.py publish --run RUN_ID [--repo OWNER/NAME] [--dry-run]
      the owner's release step, see RELEASING.md
  flutter-precompiled.py --self-test

Key material is never printed and never passed on a command line: openssl
reads it on stdin, `security -i` reads its command on stdin. Python >= 3.11,
stdlib only, plus OpenSSL 3 (LibreSSL lacks raw Ed25519), gh and, for the
Keychain, macOS `security`. Exit 0 done · 1 refused or failed.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "qrcode-ai-com/qrcode-barcode-scanner-rust"
URL_PREFIX = f"https://github.com/{REPO}/releases/download/precompiled_"
CONFIG = ROOT / "bindings" / "flutter" / "rust" / "cargokit.yaml"
SERVICE = "qrcode-barcode-scanner.flutter-precompiled"
ACCOUNT = "ed25519-seed"
LIBRARY = "qrcode_ai_scanner"
WORKFLOW = "Flutter precompiled binaries"
ARTIFACT = "flutter-precompiled-unsigned"
ANDROID = ("armv7-linux-androideabi", "aarch64-linux-android", "i686-linux-android", "x86_64-linux-android")
IOS = ("aarch64-apple-ios", "aarch64-apple-ios-sim", "x86_64-apple-ios")
RELEASE_TARGETS = ANDROID + IOS
# DER framing of an Ed25519 key: PKCS#8 private key (RFC 8410) and SubjectPublicKeyInfo.
PKCS8_PREFIX = bytes.fromhex("302e020100300506032b657004220420")
SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")
CONFIG_TEXT = (
    "# Signed precompiled binaries (scripts/flutter-precompiled.py keygen): cargokit\n"
    "# downloads <url_prefix><crate hash>/<target>_<library> and its .sig, and uses\n"
    "# the file only if public_key verifies the signature.\n"
    "precompiled_binaries:\n"
    "  url_prefix: {url}\n"
    "  public_key: {key}\n"
)
CONFIG_PATTERN = re.compile(re.escape(CONFIG_TEXT).replace(r"\{url\}", r"(?P<url>\S+)").replace(
    r"\{key\}", r"(?P<key>[0-9a-f]{64})"))


class Refused(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


# ---------------------------------------------------------------- crate hash


def dart_lines(text):
    """Dart's LineSplitter: CR, LF or CRLF ends a line; a final terminator adds no empty line."""
    lines = re.split(r"\r\n|\r|\n", text)
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def hashed_files(manifest_dir):
    """cargokit's CrateHash.getFiles: src/** sorted by path, then the four root files that exist."""
    manifest_dir = pathlib.Path(manifest_dir)
    src = manifest_dir / "src"
    found = []
    for directory, _, names in os.walk(src, followlinks=False):
        for name in names:
            path = pathlib.Path(directory) / name
            if path.is_file() and not path.is_symlink():
                found.append(str(path))
    found.sort()
    found += [str(manifest_dir / name) for name in ("Cargo.toml", "Cargo.lock", "build.rs", "cargokit.yaml")
              if (manifest_dir / name).is_file()]
    return found


def crate_hash(manifest_dir):
    """sha256 over the UTF-8 lines of every hashed file, without separators, first 16 bytes in hex."""
    digest = hashlib.sha256()
    for path in hashed_files(manifest_dir):
        for line in dart_lines(pathlib.Path(path).read_bytes().decode("utf-8")):
            digest.update(line.encode("utf-8"))
    return digest.digest()[:16].hex()


def artifact_name(target):
    require(target in RELEASE_TARGETS, f"unknown target {target}")
    return f"{target}_lib{LIBRARY}.{'a' if target in IOS else 'so'}"


# ---------------------------------------------------------------- OpenSSL Ed25519


def openssl():
    candidates = [os.environ.get("FLUTTER_PRECOMPILED_OPENSSL"), shutil.which("openssl"),
                  "/opt/homebrew/opt/openssl@3/bin/openssl", "/usr/local/opt/openssl@3/bin/openssl"]
    for candidate in filter(None, candidates):
        try:
            version = subprocess.run([candidate, "version"], capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            continue
        if version.startswith("OpenSSL 3"):
            return candidate
    raise Refused("OpenSSL 3 not found (LibreSSL cannot sign raw Ed25519); set FLUTTER_PRECOMPILED_OPENSSL")


def run_openssl(arguments, stdin=b""):
    proc = subprocess.run([openssl(), *arguments], input=stdin, capture_output=True, check=False)
    return proc.returncode, proc.stdout


def check_seed(seed):
    require(isinstance(seed, bytes) and len(seed) == 32, "an Ed25519 seed is 32 bytes")
    return seed


def generate_seed():
    code, der = run_openssl(["genpkey", "-algorithm", "ed25519", "-outform", "DER"])
    require(code == 0 and len(der) == 48 and der.startswith(PKCS8_PREFIX), "openssl genpkey failed")
    return der[len(PKCS8_PREFIX):]


def public_key(seed):
    code, der = run_openssl(["pkey", "-inform", "DER", "-in", "/dev/stdin", "-pubout", "-outform", "DER"],
                            PKCS8_PREFIX + check_seed(seed))
    require(code == 0 and len(der) == 44 and der.startswith(SPKI_PREFIX), "openssl cannot derive the public key")
    return der[len(SPKI_PREFIX):].hex()


def sign_file(seed, path, signature):
    code, _ = run_openssl(["pkeyutl", "-sign", "-keyform", "DER", "-inkey", "/dev/stdin", "-rawin",
                           "-in", str(path), "-out", str(signature)], PKCS8_PREFIX + check_seed(seed))
    require(code == 0 and pathlib.Path(signature).stat().st_size == 64, f"openssl cannot sign {path}")


def verify_bytes(public_hex, data, signature):
    """True when the raw Ed25519 signature verifies, as cargokit's ed25519_edwards verify does."""
    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        (temp / "key.der").write_bytes(SPKI_PREFIX + bytes.fromhex(public_hex))
        (temp / "data").write_bytes(data)
        (temp / "data.sig").write_bytes(signature)
        code, _ = run_openssl(["pkeyutl", "-verify", "-pubin", "-keyform", "DER", "-inkey", str(temp / "key.der"),
                               "-rawin", "-in", str(temp / "data"), "-sigfile", str(temp / "data.sig")])
        return code == 0 and len(signature) == 64


# ---------------------------------------------------------------- key storage


def security():
    return os.environ.get("FLUTTER_PRECOMPILED_SECURITY", "security")


def keychain_seed():
    proc = subprocess.run([security(), "find-generic-password", "-s", SERVICE, "-a", ACCOUNT, "-w"],
                          capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    require(re.fullmatch(r"[0-9a-f]{64}", value), f"the Keychain item {SERVICE} is not a 32-byte hex seed")
    return bytes.fromhex(value)


def keychain_store(seed):
    command = f"add-generic-password -s {SERVICE} -a {ACCOUNT} -l {SERVICE} -w {check_seed(seed).hex()}\n"
    proc = subprocess.run([security(), "-i"], input=command, capture_output=True, text=True, check=False)
    # `security -i` answers 0 even when the command inside fails: read the item back.
    require(proc.returncode == 0 and keychain_seed() == seed, "the Keychain did not store the seed")


def read_key_file(path):
    value = pathlib.Path(path).read_text().strip()
    require(re.fullmatch(r"[0-9a-f]{64}", value), f"{path} does not hold a 32-byte hex seed")
    return bytes.fromhex(value)


def write_key_file(path, seed):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        handle.write(check_seed(seed).hex() + "\n")


def load_seed(key_file):
    if key_file:
        return read_key_file(key_file)
    seed = keychain_seed()
    require(seed is not None, f"no Keychain item {SERVICE} (run keygen once)")
    return seed


# ---------------------------------------------------------------- config and sets


def read_config(path, url_prefix=URL_PREFIX):
    """The public key of a cargokit.yaml written by keygen: exactly that text and that url_prefix."""
    found = CONFIG_PATTERN.fullmatch(pathlib.Path(path).read_text())
    require(found, f"{path} is not the precompiled_binaries config keygen writes")
    require(found["url"] == url_prefix, f"{path} url_prefix {found['url']} is not {url_prefix}")
    return found["key"]


def write_config(path, url_prefix, key):
    require(re.fullmatch(r"https?://\S+", url_prefix), f"invalid url prefix {url_prefix}")
    text = CONFIG_TEXT.format(url=url_prefix, key=key)
    with open(path, "x") as handle:
        handle.write(text)
    require(read_config(path, url_prefix) == key, "config does not read back")


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def read_set(directory, signed=False):
    """manifest.json and exactly the files it lists, each with its digest (and .sig when signed)."""
    directory = pathlib.Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    require(set(manifest) == {"crate_hash", "package", "toolchain", "targets", "files"}, "unexpected manifest keys")
    require(re.fullmatch(r"[0-9a-f]{32}", manifest["crate_hash"]), "invalid crate hash")
    require(manifest["package"] == LIBRARY, f"package {manifest['package']} is not {LIBRARY}")
    targets = manifest["targets"]
    require(len(targets) == len(set(targets)) and targets, "invalid target list")
    expected = {artifact_name(target) for target in targets}
    require(set(manifest["files"]) == expected, "manifest files do not match its targets")
    present = {path.name for path in directory.iterdir()} - {"manifest.json"}
    wanted = expected | ({f"{name}.sig" for name in expected} if signed else set())
    require(present == wanted, f"unexpected files: {sorted(present ^ wanted)}")
    for name, digest in manifest["files"].items():
        require(sha256(directory / name) == digest, f"{name} does not match its manifest digest")
    return manifest


def merge(out, sources):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=False)
    merged = None
    for source in sources:
        manifest = read_set(source)
        if merged is None:
            merged = dict(manifest, targets=[], files={})
        for key in ("crate_hash", "package", "toolchain"):
            require(manifest[key] == merged[key], f"{source}: {key} differs")
        for target in manifest["targets"]:
            require(target not in merged["targets"], f"{target} built twice")
            merged["targets"].append(target)
            name = artifact_name(target)
            shutil.copyfile(pathlib.Path(source) / name, out / name)
            merged["files"][name] = manifest["files"][name]
    require(merged is not None, "nothing to merge")
    merged["targets"].sort(key=RELEASE_TARGETS.index)
    merged["files"] = dict(sorted(merged["files"].items()))
    (out / "manifest.json").write_text(json.dumps(merged, indent=2) + "\n")
    return read_set(out)


def sign_set(directory, seed, config, manifest_dir=None):
    manifest = read_set(directory)
    if manifest_dir:
        require(crate_hash(manifest_dir) == manifest["crate_hash"], "the set was built from another crate")
    key = read_config(config, url_prefix=config_prefix(config))
    require(public_key(seed) == key, "this key is not the one the config's public_key names")
    for name in manifest["files"]:
        sign_file(seed, pathlib.Path(directory) / name, pathlib.Path(directory) / f"{name}.sig")
    return verify_set(directory, config)


def verify_set(directory, config):
    manifest = read_set(directory, signed=True)
    key = read_config(config, url_prefix=config_prefix(config))
    for name in manifest["files"]:
        data = (pathlib.Path(directory) / name).read_bytes()
        signature = (pathlib.Path(directory) / f"{name}.sig").read_bytes()
        require(verify_bytes(key, data, signature), f"{name}: signature does not verify")
    return manifest


def config_prefix(config):
    found = CONFIG_PATTERN.fullmatch(pathlib.Path(config).read_text())
    require(found, f"{config} is not the precompiled_binaries config keygen writes")
    return found["url"]


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise Refused(f"{url}: HTTP {error.code}") from None


def verify_remote(manifest_dir, targets):
    """What cargokit does on a consumer: download each file and its signature, verify both."""
    config = pathlib.Path(manifest_dir) / "cargokit.yaml"
    prefix = config_prefix(config)
    key = read_config(config, url_prefix=prefix)
    digest = crate_hash(manifest_dir)
    verified = {}
    for target in targets:
        name = artifact_name(target)
        data = fetch(f"{prefix}{digest}/{name}")
        signature = fetch(f"{prefix}{digest}/{name}.sig")
        require(verify_bytes(key, data, signature), f"{name}: signature does not verify")
        verified[name] = hashlib.sha256(data).hexdigest()
        print(f"ok {prefix}{digest}/{name} sha256 {verified[name]}")
    return digest, verified


RUST_TOOLS = re.compile(r"(rustup.*|cargo|cargo-.*|rustc|rustdoc|rustfmt|rust-gdb.*|rust-lldb|clippy-driver)")


def path_without_rust(path, shadow):
    """PATH with no rustup, cargo or rustc: a directory holding one is replaced by a copy of its
    other entries (symbolic links under SHADOW), so the tools beside them stay reachable."""
    shadow = pathlib.Path(shadow)
    shadow.mkdir(parents=True, exist_ok=False)
    kept = []
    for index, directory in enumerate(filter(None, path.split(os.pathsep))):
        directory = pathlib.Path(directory)
        if not directory.is_dir():
            continue
        names = sorted(entry.name for entry in directory.iterdir())
        if not any(RUST_TOOLS.fullmatch(name) for name in names):
            kept.append(str(directory))
            continue
        copy = shadow / str(index)
        copy.mkdir()
        for name in names:
            if not RUST_TOOLS.fullmatch(name):
                (copy / name).symlink_to(directory / name)
        kept.append(str(copy))
    return os.pathsep.join(kept)


# ---------------------------------------------------------------- publish


def staging():
    spec = importlib.util.spec_from_file_location("flutter_staging", ROOT / "scripts" / "stage-flutter-package.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gh(*arguments, capture=True):
    proc = subprocess.run(["gh", *arguments], capture_output=capture, text=True, check=False)
    require(proc.returncode == 0, f"gh {' '.join(arguments[:2])} failed: {proc.stderr.strip() if capture else ''}")
    return proc.stdout


def check_run(run):
    """The unsigned set comes from a successful tag run of this workflow, on a v* tag."""
    require(run.get("workflowName") == WORKFLOW, f"run is {run.get('workflowName')!r}, not {WORKFLOW!r}")
    require(run.get("event") == "push" and str(run.get("headBranch", "")).startswith("v"),
            "run is not a push of a v* tag")
    require(run.get("status") == "completed" and run.get("conclusion") == "success", "run did not succeed")
    require(re.fullmatch(r"[0-9a-f]{40}", run.get("headSha", "")), "run has no commit")
    return run["headSha"], run["headBranch"]


def publish(run_id, repo, dry_run, key_file=None):
    run = json.loads(gh("run", "view", str(run_id), "--repo", repo, "--json",
                        "workflowName,event,headBranch,headSha,status,conclusion"))
    commit, tag = check_run(run)
    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        gh("run", "download", str(run_id), "--repo", repo, "--name", ARTIFACT, "--dir", str(temp / "artifact"))
        artifact = temp / "artifact"
        archive = artifact / "flutter-stage.tar.gz"
        recorded = (artifact / "flutter-stage.sha256").read_text().split()[0]
        require(sha256(archive) == recorded, "staged archive does not match its digest")
        receipt = json.loads((artifact / "flutter-stage.json").read_text())
        require(receipt.get("candidate") == commit, "staged archive is not the run's commit")
        require(receipt.get("package-archive-sha256") == recorded, "receipt names another archive")
        stage = staging()
        package = temp / "package"
        stage.write_tree(package, stage.read_archive(archive.read_bytes()))
        manifest = read_set(artifact / "binaries")
        require(tuple(manifest["targets"]) == RELEASE_TARGETS, "the set does not hold every release target")
        digest = crate_hash(package / "rust")
        require(manifest["crate_hash"] == digest, "the set was built from another crate")
        config = package / "rust" / "cargokit.yaml"
        key = read_config(config)
        seed = load_seed(key_file)
        require(public_key(seed) == key, "this key is not the one the staged package names")
        release = f"precompiled_{digest}"
        exists = subprocess.run(["gh", "release", "view", release, "--repo", repo, "--json", "assets"],
                                capture_output=True, text=True, check=False)
        print(f"{tag} {commit}: crate hash {digest}, {len(manifest['files'])} binaries, release {release}")
        if exists.returncode == 0:
            print(f"{release} exists: verifying what it serves, uploading nothing")
            verify_remote(package / "rust", RELEASE_TARGETS)
            return 0
        if dry_run:
            print("dry run: nothing signed, nothing created")
            return 0
        sign_set(artifact / "binaries", seed, config, package / "rust")
        files = [str(artifact / "binaries" / name) for name in manifest["files"]]
        files += [f"{name}.sig" for name in files]
        gh("release", "create", release, "--repo", repo, "--target", commit, "--latest=false",
           "--title", f"Precompiled Flutter binaries {digest[:8]} ({tag})",
           "--notes", f"Signed precompiled native libraries of the Flutter package qr_barcode_scanner "
                      f"at {tag} ({commit}), crate hash {digest}. cargokit downloads them and verifies "
                      f"each signature against the public key in rust/cargokit.yaml.", *files, capture=True)
        verify_remote(package / "rust", RELEASE_TARGETS)
        print(f"published {release}")
    return 0


# ---------------------------------------------------------------- self-test


def self_test():
    class Tests(unittest.TestCase):
        def setUp(self):
            self.temp = pathlib.Path(tempfile.mkdtemp())

        def tearDown(self):
            shutil.rmtree(self.temp)

        def crate(self, cargokit=None):
            root = self.temp / "rust"
            (root / "src" / "api").mkdir(parents=True)
            (root / "src" / "lib.rs").write_bytes(b"mod api;\r\npub fn a() {}\n")
            (root / "src" / "api" / "scan.rs").write_bytes(b"pub fn scan() {}\n\n")
            (root / "src" / "api" / "mod.rs").write_bytes(b"pub mod scan;")
            (root / "Cargo.toml").write_bytes(b"[package]\nname = \"qrcode_ai_scanner\"\n")
            (root / "Cargo.lock").write_bytes(b"version = 4\n")
            (root / "vendor").mkdir()
            (root / "vendor" / "ignored.rs").write_bytes(b"not hashed\n")
            if cargokit:
                (root / "cargokit.yaml").write_text(cargokit)
            return root

        def test_dart_line_splitter(self):
            for text, lines in (("", []), ("\n", [""]), ("a", ["a"]), ("a\n", ["a"]), ("a\r\nb", ["a", "b"]),
                                ("a\rb\r", ["a", "b"]), ("a\n\nb\n", ["a", "", "b"]), ("a\x0cb c", ["a\x0cb c"])):
                self.assertEqual(dart_lines(text), lines, repr(text))

        def test_crate_hash_order_and_lines(self):
            root = self.crate()
            expected = hashlib.sha256(b"".join((
                b"pub mod scan;", b"pub fn scan() {}", b"", b"mod api;", b"pub fn a() {}",
                b"[package]", b'name = "qrcode_ai_scanner"', b"version = 4"))).digest()[:16].hex()
            self.assertEqual(crate_hash(root), expected)
            (root / "src" / "link.rs").symlink_to(root / "src" / "lib.rs")
            self.assertEqual(crate_hash(root), expected, "a symbolic link is not hashed")
            (root / "vendor" / "ignored.rs").write_bytes(b"changed\n")
            self.assertEqual(crate_hash(root), expected, "only src and the root files are hashed")
            (root / "Cargo.lock").write_bytes(b"version = 4\r\n")
            self.assertEqual(crate_hash(root), expected, "line endings do not change the hash")
            (root / "build.rs").write_bytes(b"fn main() {}\n")
            self.assertNotEqual(crate_hash(root), expected)

        def test_config_round_trip_and_refusals(self):
            path = self.temp / "cargokit.yaml"
            write_config(path, URL_PREFIX, "ab" * 32)
            self.assertEqual(read_config(path), "ab" * 32)
            with self.assertRaises(FileExistsError):
                write_config(path, URL_PREFIX, "cd" * 32)
            with self.assertRaisesRegex(Refused, "url_prefix"):
                read_config(path, url_prefix="http://127.0.0.1:8765/precompiled_")
            path.write_text(path.read_text() + "  extra: 1\n")
            with self.assertRaisesRegex(Refused, "not the precompiled_binaries config"):
                read_config(path)

        def test_sign_verify_tamper(self):
            try:
                openssl()
            except Refused:
                self.skipTest("OpenSSL 3 absent")
            seed = generate_seed()
            key_file = self.temp / "key"
            write_key_file(key_file, seed)
            self.assertEqual(oct(key_file.stat().st_mode & 0o777), "0o600")
            with self.assertRaises(FileExistsError):
                write_key_file(key_file, seed)
            self.assertEqual(read_key_file(key_file), seed)
            root = self.crate()
            config = root / "cargokit.yaml"
            write_config(config, "http://127.0.0.1:8765/precompiled_", public_key(seed))
            binaries = self.temp / "binaries"
            binaries.mkdir()
            name = artifact_name("aarch64-linux-android")
            (binaries / name).write_bytes(b"\x7fELF fake library")
            manifest = {"crate_hash": crate_hash(root), "package": LIBRARY, "toolchain": "1.99.1",
                        "targets": ["aarch64-linux-android"], "files": {name: sha256(binaries / name)}}
            (binaries / "manifest.json").write_text(json.dumps(manifest))
            other = self.temp / "other.yaml"
            write_config(other, URL_PREFIX, public_key(generate_seed()))
            with self.assertRaisesRegex(Refused, "not the one"):
                sign_set(binaries, seed, other)
            sign_set(binaries, seed, config, root)
            self.assertEqual(len((binaries / f"{name}.sig").read_bytes()), 64)
            verify_set(binaries, config)
            data = bytearray((binaries / name).read_bytes())
            data[0] ^= 1
            self.assertFalse(verify_bytes(public_key(seed), bytes(data), (binaries / f"{name}.sig").read_bytes()))
            (binaries / name).write_bytes(bytes(data))
            with self.assertRaisesRegex(Refused, "manifest digest"):
                verify_set(binaries, config)

        def test_set_shape(self):
            binaries = self.temp / "set"
            binaries.mkdir()
            name = artifact_name("aarch64-apple-ios")
            self.assertEqual(name, "aarch64-apple-ios_libqrcode_ai_scanner.a")
            (binaries / name).write_bytes(b"!<arch>\n")
            manifest = {"crate_hash": "0" * 32, "package": LIBRARY, "toolchain": "1.99.1",
                        "targets": ["aarch64-apple-ios"], "files": {name: sha256(binaries / name)}}
            (binaries / "manifest.json").write_text(json.dumps(manifest))
            read_set(binaries)
            (binaries / "stray.so").write_bytes(b"")
            with self.assertRaisesRegex(Refused, "unexpected files"):
                read_set(binaries)
            (binaries / "stray.so").unlink()
            with self.assertRaisesRegex(Refused, "unknown target"):
                artifact_name("x86_64-pc-windows-msvc")
            android = self.temp / "android"
            android.mkdir()
            other = artifact_name("x86_64-linux-android")
            (android / other).write_bytes(b"\x7fELF")
            (android / "manifest.json").write_text(json.dumps(dict(
                manifest, targets=["x86_64-linux-android"], files={other: sha256(android / other)})))
            merged = merge(self.temp / "merged", [binaries, android])
            self.assertEqual(merged["targets"], ["x86_64-linux-android", "aarch64-apple-ios"])
            (android / "manifest.json").write_text(json.dumps(dict(
                manifest, crate_hash="1" * 32, targets=["x86_64-linux-android"],
                files={other: sha256(android / other)})))
            with self.assertRaisesRegex(Refused, "crate_hash differs"):
                merge(self.temp / "merged2", [binaries, android])

        def test_keychain_store_reads_command_on_stdin(self):
            log = self.temp / "security.log"
            stub = self.temp / "security"
            stub.write_text(
                "#!/bin/sh\n"
                f'printf "%s\\n" "$*" >> "{log}"\n'
                'if [ "$1" = "-i" ]; then cat > "$0.stdin"; exit 0; fi\n'
                'if [ -f "$0.stdin" ]; then sed -n "s/.* -w \\([0-9a-f]*\\)$/\\1/p" "$0.stdin"; exit 0; fi\n'
                "exit 44\n")
            stub.chmod(0o700)
            os.environ["FLUTTER_PRECOMPILED_SECURITY"] = str(stub)
            try:
                self.assertIsNone(keychain_seed())
                seed = bytes(range(32))
                keychain_store(seed)
                self.assertEqual(keychain_seed(), seed)
                self.assertNotIn(seed.hex(), log.read_text(), "the seed never appears in an argument")
                self.assertIn(f"add-generic-password -s {SERVICE} -a {ACCOUNT}",
                              pathlib.Path(f"{stub}.stdin").read_text())
            finally:
                del os.environ["FLUTTER_PRECOMPILED_SECURITY"]

        def test_path_without_rust(self):
            tools, other = self.temp / "tools", self.temp / "other"
            for directory, names in ((tools, ("rustup", "cargo", "cargo-clippy", "rustc", "pod", "git")),
                                     (other, ("python3",))):
                directory.mkdir()
                for name in names:
                    (directory / name).write_text("#!/bin/sh\n")
                    (directory / name).chmod(0o755)
            path = path_without_rust(os.pathsep.join([str(tools), str(self.temp / "absent"), str(other)]),
                                     self.temp / "shadow")
            entries = path.split(os.pathsep)
            self.assertEqual(entries[1], str(other))
            self.assertEqual(sorted(p.name for p in pathlib.Path(entries[0]).iterdir()), ["git", "pod"])
            for name in ("rustup", "cargo", "rustc"):
                self.assertIsNone(shutil.which(name, path=path))
            self.assertIsNotNone(shutil.which("pod", path=path))

        def test_run_checks(self):
            good = {"workflowName": WORKFLOW, "event": "push", "headBranch": "v0.12.0", "status": "completed",
                    "conclusion": "success", "headSha": "a" * 40}
            self.assertEqual(check_run(good), ("a" * 40, "v0.12.0"))
            for change in ({"workflowName": "Flutter candidate qualification"}, {"event": "pull_request"},
                           {"headBranch": "main"}, {"conclusion": "failure"}, {"headSha": ""}):
                with self.assertRaises(Refused):
                    check_run(dict(good, **change))

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


# ---------------------------------------------------------------- command line


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    commands = parser.add_subparsers(dest="command")
    command = commands.add_parser("hash")
    command.add_argument("--manifest-dir", type=pathlib.Path, default=CONFIG.parent)
    command = commands.add_parser("keygen")
    command.add_argument("--key-file", type=pathlib.Path)
    command.add_argument("--config", type=pathlib.Path, default=CONFIG)
    command.add_argument("--url-prefix", default=URL_PREFIX)
    command = commands.add_parser("check-config")
    command.add_argument("--config", type=pathlib.Path, default=CONFIG)
    command.add_argument("--url-prefix", default=URL_PREFIX)
    command = commands.add_parser("merge")
    command.add_argument("--out", type=pathlib.Path, required=True)
    command.add_argument("sources", type=pathlib.Path, nargs="+")
    command = commands.add_parser("sign")
    command.add_argument("--dir", type=pathlib.Path, required=True)
    command.add_argument("--key-file", type=pathlib.Path)
    command.add_argument("--config", type=pathlib.Path, default=CONFIG)
    command.add_argument("--manifest-dir", type=pathlib.Path)
    command = commands.add_parser("verify")
    command.add_argument("--dir", type=pathlib.Path, required=True)
    command.add_argument("--config", type=pathlib.Path, default=CONFIG)
    command = commands.add_parser("verify-remote")
    command.add_argument("--manifest-dir", type=pathlib.Path, default=CONFIG.parent)
    command.add_argument("--targets", default="release")
    command = commands.add_parser("path-without-rust")
    command.add_argument("--shadow", type=pathlib.Path, required=True)
    command = commands.add_parser("publish")
    command.add_argument("--run", required=True)
    command.add_argument("--repo", default=REPO)
    command.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.command == "hash":
        print(crate_hash(args.manifest_dir))
    elif args.command == "keygen":
        require(not args.config.exists(), f"{args.config} exists: the key is already chosen")
        if not args.key_file:
            require(keychain_seed() is None, f"the Keychain already holds {SERVICE}: refusing to replace it")
        seed = generate_seed()
        if args.key_file:
            write_key_file(args.key_file, seed)
        else:
            keychain_store(seed)
        key = public_key(seed)
        write_config(args.config, args.url_prefix, key)
        where = args.key_file or f"the Keychain item {SERVICE}"
        print(f"public key {key}\nseed stored in {where}\nconfig written to {args.config}")
    elif args.command == "check-config":
        print(f"public key {read_config(args.config, args.url_prefix)}")
    elif args.command == "merge":
        manifest = merge(args.out, args.sources)
        print(f"merged {', '.join(manifest['targets'])} · crate hash {manifest['crate_hash']}")
    elif args.command == "sign":
        manifest = sign_set(args.dir, load_seed(args.key_file), args.config, args.manifest_dir)
        print(f"signed and verified {len(manifest['files'])} files · crate hash {manifest['crate_hash']}")
    elif args.command == "verify":
        manifest = verify_set(args.dir, args.config)
        print(f"verified {len(manifest['files'])} files · crate hash {manifest['crate_hash']}")
    elif args.command == "verify-remote":
        targets = RELEASE_TARGETS if args.targets == "release" else tuple(args.targets.split(","))
        digest, verified = verify_remote(args.manifest_dir, targets)
        print(f"verified {len(verified)} remote binaries · crate hash {digest}")
    elif args.command == "path-without-rust":
        print(path_without_rust(os.environ.get("PATH", ""), args.shadow))
    elif args.command == "publish":
        return publish(args.run, args.repo, args.dry_run)
    else:
        parser.error("give a command or --self-test")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Refused, OSError, ValueError, json.JSONDecodeError) as error:
        sys.exit(f"flutter-precompiled: {error}")
