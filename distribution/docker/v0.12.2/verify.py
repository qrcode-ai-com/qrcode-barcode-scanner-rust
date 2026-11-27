#!/usr/bin/env python3
"""Qualify the repackaged public CLI image; never build Rust or access a registry.

  verify.py IMAGE FIXTURE --packaging-revision SHA [--expected-platform P] [--native] [--receipt F]
  verify.py --self-test

The image holds no shell and no tool beside the scanner, so nothing here runs a command in
it but `qrscan` itself. What the image contains is read from the host: a container is created
and never started, its filesystem is exported as one tar stream and read in memory. From that
stream come the hash of the binary and of every source archive, the build record, the owner
and mode of every path, the installed packages and the proof that no shell is there.
"""

import argparse
import base64
import copy
import hashlib
import json
import platform
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import zlib
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import consumer_truth

INPUTS = json.loads(Path(__file__).with_name("inputs.json").read_text())
VERSION = INPUTS["version"]
CRATES = [name for name in INPUTS["sources"] if name.endswith(".crate")]
BASE = INPUTS["base"]
RUN_AS = 65532
BINARY = "usr/local/bin/qrscan"
DOC = "usr/share/doc/qrscan"
# What the image installs beside the binary: the notices of the release archive, the
# archive's own source note under another name, and this recipe's SOURCE.md.
NOTICES = {
    "CLI-SOURCE.md",
    "COPYRIGHT-rust-std.html",
    "LICENSE",
    "LICENSE-APACHE-2.0",
    "LICENSING.md",
    "README.md",
    "SOURCE.md",
    "THIRD-PARTY-LICENSES.txt",
    "THIRD-PARTY.md",
    "build-info.json",
}
# What the container runtime puts into every container, whatever the image holds.
RUNTIME_MADE = {
    ".dockerenv",
    "dev",
    "proc",
    "sys",
    "etc/hostname",
    "etc/hosts",
    "etc/mtab",
    "etc/resolv.conf",
}
# A shell or a package manager would let a caller run or install something else.
FORBIDDEN = {
    "sh",
    "ash",
    "bash",
    "dash",
    "zsh",
    "busybox",
    "toybox",
    "apk",
    "apt",
    "apt-get",
    "dpkg",
    "rpm",
    "dnf",
    "yum",
}
PROGRAM_DIRECTORIES = {
    "bin",
    "sbin",
    "usr/bin",
    "usr/sbin",
    "usr/local/bin",
    "usr/local/sbin",
}
SBOM = "var/lib/db/sbom"
PACKAGES = "usr/lib/apk/db/installed"
READ = {DOC + "/build-info.json", "etc/os-release", PACKAGES}
# The notice the image installs is the one this recipe holds, not an earlier text.
SOURCE_NOTICE = hashlib.sha256(
    Path(__file__).with_name("SOURCE.md").read_bytes()
).hexdigest()


def read_filesystem(image, platform_name):
    """Every path of the image, with the bytes this program judges, from one export.

    The container is created and never started. Its filesystem leaves the daemon as a tar
    stream that is read member by member: nothing is unpacked on the host.
    """
    container = subprocess.check_output(
        ["docker", "create", "--platform", platform_name, "--network", "none", image],
        text=True,
        timeout=120,
    ).strip()
    members, hashes, texts = [], {}, {}
    try:
        process = subprocess.Popen(
            ["docker", "export", container], stdout=subprocess.PIPE
        )
        with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            for member in archive:
                name = member.name.removeprefix("./").rstrip("/")
                kind = (
                    "directory"
                    if member.isdir()
                    else "file"
                    if member.isfile()
                    else "link"
                    if member.issym()
                    else "other"
                )
                members.append(
                    {
                        "name": name,
                        "kind": kind,
                        "uid": member.uid,
                        "gid": member.gid,
                        "mode": member.mode & 0o7777,
                    }
                )
                wanted = name == BINARY or name.startswith(DOC + "/") or name in READ
                if kind == "file" and wanted and name not in hashes:
                    data = archive.extractfile(member).read()
                    hashes[name] = hashlib.sha256(data).hexdigest()
                    if name in READ:
                        texts[name] = data.decode()
        assert process.wait(timeout=120) == 0, "docker export failed"
    finally:
        subprocess.run(
            ["docker", "rm", "--force", container],
            stdout=subprocess.DEVNULL,
            check=False,
            timeout=120,
        )
    return members, hashes, texts


def judge_filesystem(members, hashes, texts, architecture):
    """The problems of an image's filesystem, and what the receipt records of it."""
    problems = []
    listed = [
        member
        for member in members
        if member["name"]
        and member["name"] not in RUNTIME_MADE
        and not member["name"].startswith("dev/")
    ]
    names = [member["name"] for member in listed]
    by_name = {member["name"]: member for member in listed}
    if len(by_name) != len(names):
        problems.append("a path appears twice in the export")
    other = sorted(member["name"] for member in listed if member["kind"] == "other")
    if other:
        problems.append(f"hard links or special files: {other}")

    # No shell and no package manager, under any directory and as a link too.
    tools = sorted(
        member["name"]
        for member in listed
        if member["kind"] != "directory"
        and PurePosixPath(member["name"]).name in FORBIDDEN
    )
    if tools:
        problems.append(f"a shell or a package manager is in the image: {tools}")
    # What can be executed: the scanner, and the two loader tools of the C library.
    programs = sorted(
        member["name"]
        for member in listed
        if member["kind"] != "directory"
        and (
            str(PurePosixPath(member["name"]).parent) in PROGRAM_DIRECTORIES
            or (
                member["kind"] == "file"
                and member["mode"] & 0o111
                and not member["name"].startswith("usr/lib/")
            )
        )
    )
    if programs != sorted([*BASE["programs"], BINARY]):
        problems.append(
            f"other programs than the scanner and the pinned base's: {programs}"
        )
    elevated = sorted(
        member["name"]
        for member in listed
        if member["kind"] == "file" and member["mode"] & 0o6000
    )
    if elevated:
        problems.append(f"setuid or setgid files: {elevated}")

    # The image runs as 65532:65532, with no other group and no capability. What that user
    # could change is what it or its group owns and what is open to everyone: the pinned
    # directories of the base and nothing else. With a read-only root filesystem, as the
    # documented command runs it, those are closed too.
    held = sorted(
        member["name"]
        for member in listed
        if member["kind"] != "link"
        and (
            member["uid"] == RUN_AS or member["gid"] == RUN_AS or member["mode"] & 0o002
        )
    )
    # The base also keeps empty home directories of system accounts, closed to everyone else.
    accounts = sorted(
        member["name"]
        for member in listed
        if member["kind"] != "link"
        and member["name"] not in held
        and (member["uid"] != 0 or member["gid"] != 0)
    )
    loose = [
        name
        for name in accounts
        if by_name[name]["kind"] != "directory" or by_name[name]["mode"] & 0o077
    ]
    if loose:
        problems.append(
            f"paths of other accounts that are not closed directories: {loose}"
        )
    if held != BASE["writable"]:
        problems.append(
            f"paths the image's user can change, beside the pinned ones: {held}"
        )
    for name in BASE["writable"]:
        member = by_name.get(name)
        if member and member["kind"] != "directory":
            problems.append(f"{name} is not a directory")
        if member and (
            member["uid"] not in (0, RUN_AS) or member["gid"] not in (0, RUN_AS)
        ):
            problems.append(f"{name} belongs to neither root nor the image's user")

    # What the recipe adds, with the owner and the modes it is meant to have.
    added = {
        "data": ("directory", 0o755),
        BINARY: ("file", 0o755),
        DOC: ("directory", 0o755),
    }
    added[DOC + "/source"] = ("directory", 0o755)
    added |= {DOC + "/" + name: ("file", 0o644) for name in NOTICES}
    added |= {DOC + "/source/" + name: ("file", 0o644) for name in INPUTS["sources"]}
    installed = {
        name
        for name in by_name
        if name in ("data", BINARY) or name == DOC or name.startswith(DOC + "/")
    }
    if installed != set(added):
        problems.append(
            f"the recipe's own paths differ: {sorted(installed ^ set(added))}"
        )
    for name, (kind, mode) in sorted(added.items()):
        member = by_name.get(name)
        if member and (
            member["kind"],
            member["uid"],
            member["gid"],
            member["mode"],
        ) != (
            kind,
            0,
            0,
            mode,
        ):
            problems.append(f"{name} is not a root-owned {kind} of mode {mode:o}")

    # The bytes: the published binary, the published sources, the build record.
    platform_inputs = INPUTS["platforms"][architecture]
    if hashes.get(BINARY) != platform_inputs["binarySha256"]:
        problems.append("the binary is not the published one")
    sources = {name: hashes.get(DOC + "/source/" + name) for name in INPUTS["sources"]}
    for name, item in INPUTS["sources"].items():
        if sources[name] != item["sha256"]:
            problems.append(f"{name} is not the published source")
    if hashes.get(DOC + "/SOURCE.md") != SOURCE_NOTICE:
        problems.append("the installed SOURCE.md is not this recipe's")
    try:
        build_info = json.loads(texts[DOC + "/build-info.json"])
        recorded = (
            build_info["binary"]["sha256"],
            build_info["source"]["commit"],
            build_info["source"]["dirty"],
            build_info["target"],
            build_info["version"],
        )
    except (KeyError, TypeError, ValueError):
        recorded = None
    if recorded != (
        platform_inputs["binarySha256"],
        INPUTS["engineSource"],
        False,
        platform_inputs["target"],
        VERSION,
    ):
        problems.append(f"build-info.json does not describe this binary: {recorded}")

    # The base: its system, its exact packages, and one SPDX file for each.
    system = (
        dict(
            line.split("=", 1)
            for line in texts.get("etc/os-release", "").splitlines()
            if "=" in line
        )
        .get("ID", "")
        .strip('"')
    )
    if system != BASE["os"]:
        problems.append(f"the base system is {system or 'unknown'}, not {BASE['os']}")
    packages = []
    for record in texts.get(PACKAGES, "").split("\n\n"):
        fields = dict(
            line.split(":", 1) for line in record.splitlines() if line[1:2] == ":"
        )
        if "P" in fields or "V" in fields:
            packages.append(f"{fields.get('P')} {fields.get('V')}")
    packages.sort()
    if packages != BASE["packages"]:
        problems.append(f"the installed packages are not the pinned ones: {packages}")
    records = sorted(
        PurePosixPath(name).name for name in by_name if name.startswith(SBOM + "/")
    )
    if records != sorted(
        item.replace(" ", "-") + ".spdx.json" for item in BASE["packages"]
    ):
        problems.append(f"the SPDX files do not match the pinned packages: {records}")
    return problems, {
        "paths": len(listed),
        "system": system,
        "packages": packages,
        "programs": programs,
        "changeable_by_the_image_user": held,
        "closed_directories_of_system_accounts": accounts,
        "shell_or_package_manager": tools,
        "setuid_or_setgid": elevated,
        "binary_sha256": hashes.get(BINARY),
        "source_sha256": sources,
        "installed_files": {
            name: hashes.get(name) for name in sorted(added) if added[name][0] == "file"
        },
    }


def white_png():
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data))
        )

    row = b"\x00" + b"\xff\xff\xff" * 64
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(row * 64))
        + chunk(b"IEND", b"")
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?")
    parser.add_argument("fixture", type=Path, nargs="?")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--expected-platform", choices=("linux/amd64", "linux/arm64"))
    parser.add_argument(
        "--native",
        action="store_true",
        help="require native Linux host and Docker engine",
    )
    parser.add_argument("--packaging-revision")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.image or not args.fixture or not args.packaging_revision:
        parser.error("image, fixture and --packaging-revision are required")
    image = json.loads(
        subprocess.check_output(["docker", "image", "inspect", args.image], text=True)
    )[0]
    assert image["Config"]["User"] == "65532:65532"
    assert image["Config"]["Entrypoint"] == ["/usr/local/bin/qrscan"]
    assert image["Config"]["Labels"]["org.opencontainers.image.version"] == VERSION
    assert (
        image["Config"]["Labels"]["org.opencontainers.image.licenses"]
        == INPUTS["license"]
    )
    labels = image["Config"]["Labels"]
    assert re.fullmatch(r"[0-9a-f]{40}", args.packaging_revision)
    assert args.packaging_revision != INPUTS["engineSource"]
    assert labels["io.qrcode-ai.scanner.packaging-revision"] == args.packaging_revision
    assert labels["org.opencontainers.image.revision"] == INPUTS["engineSource"]
    assert labels["org.opencontainers.image.source"] == INPUTS["repository"]
    assert labels["org.opencontainers.image.title"] == "QR Code & Barcode Scanner"
    assert labels["org.opencontainers.image.url"] == "https://qrcode-ai.com/"
    assert (
        labels["org.opencontainers.image.documentation"]
        == INPUTS["repository"] + "/tree/main/distribution/docker/v0.12.2"
    )
    assert (
        labels["org.opencontainers.image.description"]
        == "Local QR code, barcode and matrix-code scanning. Mount input read-only and run qrscan without network access."
    )
    assert image["Config"]["WorkingDir"] == "/data"
    assert image["Config"]["Cmd"] == ["--help"]
    assert "RAYON_NUM_THREADS=2" in image["Config"]["Env"]
    assert image["Architecture"] in ("amd64", "arm64")
    actual_platform = image["Os"] + "/" + image["Architecture"]
    if args.expected_platform:
        assert actual_platform == args.expected_platform, (
            actual_platform,
            args.expected_platform,
        )
    aliases = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    daemon_arch = subprocess.check_output(
        ["docker", "info", "--format", "{{.Architecture}}"], text=True
    ).strip()
    execution = (
        "native-daemon"
        if aliases.get(daemon_arch) == image["Architecture"]
        else "emulated"
    )
    if args.native:
        assert (
            platform.system() == "Linux"
            and aliases.get(platform.machine()) == image["Architecture"]
        )
        assert execution == "native-daemon"
    fixture = args.fixture.resolve()
    assert (
        hashlib.sha256(fixture.read_bytes()).hexdigest()
        == "1dc399cad19623a145b20251cf1c0da42ea4f54fd79871a4dd796c9554822dd6"
    )
    cases = []
    with tempfile.TemporaryDirectory(prefix="qrscan-oci-") as directory:
        root = Path(directory)
        root.chmod(0o755)
        shutil.copyfile(fixture, root / "input with spaces.png")
        (root / "white.png").write_bytes(white_png())
        (root / "invalid.bin").write_bytes(b"this is not an image")
        for file in root.iterdir():
            file.chmod(0o644)
        prefix = [
            "docker",
            "run",
            "--rm",
            "--platform",
            actual_platform,
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--memory",
            "512m",
            "--cpus",
            "2",
            "--pids-limit",
            "128",
            "--mount",
            f"type=bind,src={root},dst=/data,readonly",
            args.image,
        ]

        def run(arguments, code):
            result = subprocess.run(
                prefix + arguments,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            cases.append(
                {
                    "arguments": arguments,
                    "exit": result.returncode,
                    "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
                    "stderr": result.stderr,
                }
            )
            assert result.returncode == code, (
                arguments,
                result.returncode,
                result.stderr,
            )
            if code == 2:
                assert result.stdout == "" and result.stderr.strip(), (
                    arguments,
                    result.stdout,
                    result.stderr,
                )
            return result.stdout

        assert run(["--version"], 0).strip() == "qrscan " + VERSION
        usage = run(["--help"], 0)
        assert "--profile" in usage and "--formats" in usage
        full = json.loads(
            run(
                [
                    "/data/input with spaces.png",
                    "--profile",
                    "full",
                    "--budget-ms",
                    "0",
                ],
                0,
            )
        )
        assert full["versions"] == {
            "scanner": VERSION,
            "pipeline": 5,
            "score_contract": 6,
        }
        text = "https://qrcode-ai.com/c/v5q"
        assert [d["content"] for d in full["detections"]] == [
            {
                "text": text,
                "raw": base64.b64encode(text.encode()).decode(),
                "charset": "utf8",
            }
        ]
        assert [d["symbology"] for d in full["detections"]] == ["qr_code"]
        assert full["score"]["value"] == 100
        assert full["trace"]["budget_exhausted"] is False
        assert "alpha" not in full
        frame = json.loads(
            run(
                [
                    "/data/input with spaces.png",
                    "--profile",
                    "frame",
                    "--budget-ms",
                    "0",
                ],
                0,
            )
        )
        assert frame["versions"] == full["versions"]
        assert frame["score"] is None
        assert [(d["symbology"], d["content"]) for d in frame["detections"]] == [
            (d["symbology"], d["content"]) for d in full["detections"]
        ]
        assert frame["trace"]["budget_exhausted"] is False and "alpha" not in frame
        empty = json.loads(
            run(["/data/white.png", "--profile", "full", "--budget-ms", "0"], 1)
        )
        assert empty["versions"] == full["versions"]
        assert empty["detections"] == [] and empty["score"] is None
        assert empty["trace"]["budget_exhausted"] is False and "alpha" not in empty
        assert (
            run(
                ["/data/input with spaces.png", "--budget-ms", "0", "--score-only"], 0
            ).strip()
            == "100"
        )
        assert (
            run(
                ["/data/input with spaces.png", "--profile", "frame", "--score-only"], 2
            )
            == ""
        )
        assert run(["/data/invalid.bin"], 2) == ""
        assert run(["/data/absent.png"], 2) == ""
        assert run(["/data/input with spaces.png", "--profile", "invalid"], 2) == ""
        truth = consumer_truth.load()
        staged = consumer_truth.stage(truth, root / "truth")
        for file in (root / "truth").rglob("*"):
            file.chmod(0o755 if file.is_dir() else 0o644)
        truth_profiles = []
        for case, path in staged:
            profiles = (
                ("full", "fast", "frame")
                if case["id"] in {"qr-and-code128", "qr-twins-and-code128"}
                else ("full",)
            )
            for profile in profiles:
                code = 2 if "error" in case else 0 if case["contents"] else 1
                output = run(
                    [
                        "/data/" + str(path.relative_to(root)),
                        "--profile",
                        profile,
                        "--budget-ms",
                        "0",
                    ],
                    code,
                )
                if "error" not in case:
                    report = json.loads(output)
                    expected = copy.deepcopy(case)
                    if profile == "frame":
                        expected["score"] = None
                    problems = consumer_truth.judge(expected, report, full["versions"])
                    assert not problems, (case["id"], profile, problems)
                    assert report["trace"]["engine_panics"] == 0, (case["id"], profile)
                    # An unrestricted scan does not name what it looked for.
                    assert "formats" not in report["trace"], (case["id"], profile)
                truth_profiles.append(
                    {"id": case["id"], "profile": profile, "exit": code}
                )
        # --formats: only the listed symbologies are looked for, the report names
        # them in trace.formats, and an unknown name is refused with QRS-006
        # before the image is read.
        mixed, mixed_path = next(
            item for item in staged if item[0]["id"] == "qr-and-code128"
        )
        assert {content["symbology"] for content in mixed["contents"]} == {
            "qr_code",
            "code128",
        }
        mixed_input = "/data/" + str(mixed_path.relative_to(root))
        only_qr = json.loads(
            run(
                [
                    mixed_input,
                    "--profile",
                    "full",
                    "--budget-ms",
                    "0",
                    "--formats",
                    "qr_code",
                ],
                0,
            )
        )
        assert only_qr["versions"] == full["versions"]
        assert [
            (d["symbology"], d["content"]["text"]) for d in only_qr["detections"]
        ] == [
            (content["symbology"], content["text"])
            for content in mixed["contents"]
            if content["symbology"] == "qr_code"
        ]
        assert only_qr["trace"]["formats"] == ["qr_code"]
        assert only_qr["trace"]["budget_exhausted"] is False
        assert only_qr["trace"]["engine_panics"] == 0
        assert run([mixed_input, "--formats", "not_a_symbology"], 2) == ""
        assert "QRS-006" in cases[-1]["stderr"], cases[-1]["stderr"]
        # A caller who asks for a shell gets none: the runtime finds nothing to start.
        shell = subprocess.run(
            prefix[:-1] + ["--entrypoint", "sh", args.image, "-c", "true"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert shell.returncode in (125, 126, 127) and shell.stdout == "", (
            shell.returncode,
            shell.stdout,
            shell.stderr,
        )
    assert CRATES == [
        "qrcode-barcode-scanner-" + VERSION + ".crate",
        "qrcode-barcode-scanner-cli-" + VERSION + ".crate",
    ]
    problems, filesystem = judge_filesystem(
        *read_filesystem(args.image, actual_platform), image["Architecture"]
    )
    assert not problems, problems
    binary_hash = filesystem["binary_sha256"]
    source_hashes = [
        filesystem["source_sha256"][name] + "  /" + DOC + "/source/" + name
        for name in CRATES
    ]
    recipe = Path(__file__).with_name("Dockerfile").read_text()
    base_images = re.findall(r"^FROM (\S+)", recipe, re.MULTILINE)
    assert base_images == [INPUTS["baseImage"]]
    receipt = {
        "image": args.image,
        "image_id": image["Id"],
        "platform": actual_platform,
        "expected_platform": args.expected_platform,
        "host": platform.platform(),
        "source": image["Config"]["Labels"]["org.opencontainers.image.revision"],
        "packaging_revision": args.packaging_revision,
        "cases": cases,
        "execution": execution,
        "native_linux_host_required": args.native,
        "daemon_architecture": daemon_arch,
        "truth_profiles": truth_profiles,
        "truth_sha256": hashlib.sha256(
            (ROOT / "fixtures/consumer-truth.json").read_bytes()
        ).hexdigest(),
        "base_images": base_images,
        "source_archive_checksums": source_hashes,
        "binary_sha256": binary_hash,
        "runtime_permissions": "nonroot/read-only/no-network/no-capabilities",
        "shell_exit": shell.returncode,
        "filesystem": filesystem,
        "result": "PASS",
    }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


def self_test():
    """The filesystem judge accepts the image the recipe describes and nothing near it."""
    architecture = "arm64"
    platform_inputs = INPUTS["platforms"][architecture]

    def entry(name, kind="file", mode=0o644, uid=0, gid=0):
        return {"name": name, "kind": kind, "uid": uid, "gid": gid, "mode": mode}

    def image():
        members = [
            entry(name, "directory", 0o755)
            for name in (
                "etc",
                "usr",
                "usr/bin",
                "usr/lib",
                "usr/local",
                "usr/local/bin",
                "var",
                "data",
                DOC,
                DOC + "/source",
                SBOM,
                "home",
            )
        ]
        members += [
            entry("home/nonroot", "directory", 0o700, RUN_AS, RUN_AS),
            entry("tmp", "directory", 0o1777),
            entry("var/mail", "directory", 0o700, 8, 12),
            entry("var/tmp", "directory", 0o777),
            entry("bin", "link", 0o777),
            entry("usr/bin/ld.so", "link", 0o777),
            entry("usr/bin/ldconfig", mode=0o755),
            entry("etc/apk/commit_hooks.d/ldconfig-commit.sh", mode=0o755),
            entry("etc/apk", "directory", 0o755),
            entry("usr/lib/libc.so.6", mode=0o755),
            entry("etc/os-release"),
            entry(PACKAGES),
            entry(BINARY, mode=0o755),
            entry(".dockerenv", mode=0o755),
            entry("dev", "directory", 0o755),
            entry("dev/console", "other", 0o755),
            entry("etc/hosts", mode=0o755),
        ]
        members += [entry(DOC + "/" + name) for name in sorted(NOTICES)]
        members += [entry(DOC + "/source/" + name) for name in INPUTS["sources"]]
        members += [
            entry(SBOM + "/" + item.replace(" ", "-") + ".spdx.json")
            for item in BASE["packages"]
        ]
        hashes = {
            BINARY: platform_inputs["binarySha256"],
            DOC + "/SOURCE.md": SOURCE_NOTICE,
        } | {
            DOC + "/source/" + name: item["sha256"]
            for name, item in INPUTS["sources"].items()
        }
        texts = {
            DOC + "/build-info.json": json.dumps(
                {
                    "binary": {"sha256": platform_inputs["binarySha256"]},
                    "source": {"commit": INPUTS["engineSource"], "dirty": False},
                    "target": platform_inputs["target"],
                    "version": VERSION,
                }
            ),
            "etc/os-release": "ID=" + BASE["os"] + '\nNAME="Test"\n',
            PACKAGES: "\n\n".join(
                "P:{}\nV:{}\nA:test\nF:etc\nR:group".format(*item.split(" "))
                for item in BASE["packages"]
            )
            + "\n\n",
        }
        return members, hashes, texts

    assert sorted(BASE["programs"]) == BASE["programs"]
    assert sorted(BASE["packages"]) == BASE["packages"]
    assert sorted(BASE["writable"]) == BASE["writable"]
    problems, summary = judge_filesystem(*image(), architecture)
    assert problems == [], problems
    assert summary["packages"] == BASE["packages"]
    assert summary["changeable_by_the_image_user"] == BASE["writable"]
    assert summary["closed_directories_of_system_accounts"] == ["var/mail"]

    def member(members, name):
        return next(item for item in members if item["name"] == name)

    def drop(members, name):
        members.remove(member(members, name))

    changes = {
        "a shell": lambda m, h, t: m.append(entry("usr/bin/sh", mode=0o755)),
        "a shell as a link": lambda m, h, t: m.append(
            entry("usr/lib/x/bash", "link", 0o777)
        ),
        "a multi-call binary outside the program directories": lambda m, h, t: m.append(
            entry("usr/lib/busybox", mode=0o755)
        ),
        "a package manager": lambda m, h, t: m.append(entry("usr/bin/apk", mode=0o755)),
        "another program": lambda m, h, t: m.append(entry("usr/bin/env", mode=0o755)),
        "an executable elsewhere": lambda m, h, t: m.append(
            entry("opt/tool", mode=0o755)
        ),
        "a setuid file": lambda m, h, t: member(m, "usr/lib/libc.so.6").update(
            mode=0o4755
        ),
        "a working directory owned by the image's user": lambda m, h, t: member(
            m, "data"
        ).update(uid=RUN_AS, gid=RUN_AS),
        "a working directory open to others": lambda m, h, t: member(m, "data").update(
            mode=0o777
        ),
        "a binary owned by the image's user": lambda m, h, t: member(m, BINARY).update(
            uid=RUN_AS
        ),
        "a binary writable by its group": lambda m, h, t: member(m, BINARY).update(
            mode=0o775
        ),
        "a notice writable by others": lambda m, h, t: member(
            m, DOC + "/LICENSE"
        ).update(mode=0o646),
        "a file of another user": lambda m, h, t: member(m, "etc/os-release").update(
            uid=1000
        ),
        "a file of the image's group": lambda m, h, t: member(
            m, "etc/os-release"
        ).update(gid=RUN_AS),
        "an account directory open to its group": lambda m, h, t: member(
            m, "var/mail"
        ).update(mode=0o770),
        "another directory open to others": lambda m, h, t: m.append(
            entry("var/cache", "directory", 0o777)
        ),
        "a pinned directory gone": lambda m, h, t: drop(m, "var/tmp"),
        "a pinned directory of a third user": lambda m, h, t: member(m, "tmp").update(
            uid=1000
        ),
        "a notice missing": lambda m, h, t: drop(m, DOC + "/LICENSE"),
        "an extra file beside the notices": lambda m, h, t: m.append(
            entry(DOC + "/extra.txt")
        ),
        "a source archive missing": lambda m, h, t: drop(
            m, DOC + "/source/" + CRATES[0]
        ),
        "a source replaced by a link": lambda m, h, t: member(
            m, DOC + "/source/" + CRATES[0]
        ).update(kind="link"),
        "a hard link": lambda m, h, t: m.append(entry("usr/lib/other", "other")),
        "a path listed twice": lambda m, h, t: m.append(entry("etc/os-release")),
        "another binary": lambda m, h, t: h.update({BINARY: "0" * 64}),
        "another source": lambda m, h, t: h.update(
            {DOC + "/source/" + CRATES[1]: "0" * 64}
        ),
        "another source notice": lambda m, h, t: h.update(
            {DOC + "/SOURCE.md": "0" * 64}
        ),
        "a build record of another commit": lambda m, h, t: t.update(
            {
                DOC + "/build-info.json": t[DOC + "/build-info.json"].replace(
                    INPUTS["engineSource"], "0" * 40
                )
            }
        ),
        "a build record that is not JSON": lambda m, h, t: t.update(
            {DOC + "/build-info.json": "{"}
        ),
        "no build record": lambda m, h, t: t.pop(DOC + "/build-info.json"),
        "another system": lambda m, h, t: t.update({"etc/os-release": "ID=debian\n"}),
        "no system file": lambda m, h, t: t.pop("etc/os-release"),
        "a package more": lambda m, h, t: t.update(
            {PACKAGES: t[PACKAGES] + "P:openssl\nV:3\n\n"}
        ),
        "a package at another version": lambda m, h, t: t.update(
            {
                PACKAGES: t[PACKAGES].replace(
                    "V:" + BASE["packages"][0].split(" ")[1], "V:0", 1
                )
            }
        ),
        "no package database": lambda m, h, t: t.pop(PACKAGES),
        "an SPDX file missing": lambda m, h, t: drop(
            m, SBOM + "/" + BASE["packages"][0].replace(" ", "-") + ".spdx.json"
        ),
    }
    for name, change in changes.items():
        candidate = image()
        change(*candidate)
        assert judge_filesystem(*candidate, architecture)[0], "accepted " + name
    assert FORBIDDEN >= {"sh", "bash", "busybox", "apk", "apt", "dpkg"}
    print(
        json.dumps(
            {"result": "PASS", "accepted_images": 1, "negative_cases": len(changes)}
        )
    )


if __name__ == "__main__":
    main()
