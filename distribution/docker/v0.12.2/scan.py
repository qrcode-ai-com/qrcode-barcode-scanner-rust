#!/usr/bin/env python3
"""Scan an image for known vulnerabilities with the pinned scanner and refuse any finding.

  scan.py IMAGE --receipt FILE          the image the producer just tested, from the local daemon
  scan.py --published --receipt FILE    the published image that published.json records
  scan.py --self-test

Exit 0 when the scan passes, 1 when the image is refused, 2 when no scan could be made.

The scanner is Trivy, pinned by digest in inputs.json. It gets neither the Docker socket nor a
credential. It runs as the calling user, without capabilities, on a read-only root, and in two
steps: one with the network and an empty cache, to fetch its database; one with the image and
no network. A published image is read from the registry by its digest, so that step keeps the
network and is given nothing else.

A report passes when the scanner saw exactly the packages inputs.json pins for the base, its
database is recent and it lists no finding of any severity, fixable or not. Zero findings from
a scanner that saw no package would prove nothing, so that case fails too.

A scan is of its day. A package of the base can receive a finding after publication; the
answer then is a new image, never an edit of this record.
"""

import argparse
import collections
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
VERSION = INPUTS["version"]
SCANNER = INPUTS["scanner"]
IMAGE = "ghcr.io/qrcode-ai-com/qrcode-barcode-scanner"
PUBLISHED = HERE / "published.json"
# The image's architectures, and how the packages of the base name them.
MACHINES = {"amd64": "x86_64", "arm64": "aarch64"}
SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
SCAN = [
    "--format",
    "json",
    "--output",
    "/out/report.json",
    "--scanners",
    "vuln",
    "--list-all-pkgs",
    "--skip-db-update",
    "--cache-dir",
    "/cache",
    "--no-progress",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def scanner(arguments, mounts, network):
    """One run of the pinned scanner: what it may read and write is exactly `mounts`."""
    command = [
        "docker",
        "run",
        "--rm",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--env",
        "HOME=/tmp",
    ]
    if not network:
        command += ["--network", "none"]
    for source, target, readonly in mounts:
        command += [
            "--mount",
            f"type=bind,src={source},dst={target}" + (",readonly" if readonly else ""),
        ]
    return subprocess.run(
        command + [SCANNER["image"], *arguments],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )


def database(cache):
    """Fetch the scanner's database into an empty cache, then ask the scanner what it holds."""
    for attempt in range(3):
        fetched = scanner(
            ["image", "--download-db-only", "--cache-dir", "/cache", "--no-progress"],
            [(cache, "/cache", False)],
            network=True,
        )
        if fetched.returncode == 0:
            break
        time.sleep(20 * (attempt + 1))
    require(
        fetched.returncode == 0,
        "the scanner could not fetch its database: " + fetched.stderr[-2000:],
    )
    described = scanner(
        ["version", "--format", "json", "--cache-dir", "/cache"],
        [(cache, "/cache", True)],
        network=False,
    )
    require(
        described.returncode == 0,
        "the scanner did not describe itself: " + described.stderr[-2000:],
    )
    return json.loads(described.stdout)


def read_report(result, out):
    require(result.returncode == 0, "the scanner failed: " + result.stderr[-2000:])
    return json.loads((out / "report.json").read_text())


def scan_local(image, cache, work, out):
    """Scan the image the daemon holds, saved to a tarball, with no network."""
    archive = work / "image.tar"
    subprocess.run(
        ["docker", "save", "--output", str(archive), image], check=True, timeout=600
    )
    archive.chmod(0o644)
    try:
        return read_report(
            scanner(
                ["image", "--input", "/work/image.tar", "--offline-scan", *SCAN],
                [(cache, "/cache", False), (work, "/work", True), (out, "/out", False)],
                network=False,
            ),
            out,
        )
    finally:
        archive.unlink()


def scan_remote(reference, architecture, cache, out):
    """Scan one platform of a published image, read from its registry by digest."""
    return read_report(
        scanner(
            [
                "image",
                "--image-src",
                "remote",
                "--platform",
                "linux/" + architecture,
                *SCAN,
                reference,
            ],
            [(cache, "/cache", False), (out, "/out", False)],
            network=True,
        ),
        out,
    )


def moment(text):
    match = re.match(r"(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)", text or "")
    require(match, "the scanner's database carries no date")
    return datetime.datetime(*map(int, match.groups()), tzinfo=datetime.timezone.utc)


def judge(report, described, now, architecture):
    """The problems of one report, and what it says, as the receipt records it."""
    problems = []
    if described.get("Version") != SCANNER["version"]:
        problems.append(
            f"the scanner is {described.get('Version')}, not the pinned {SCANNER['version']}"
        )
    updated = (described.get("VulnerabilityDB") or {}).get("UpdatedAt")
    try:
        age = (now - moment(updated)).total_seconds() / 3600
    except ValueError as error:
        age = None
        problems.append(str(error))
    if age is not None and not -1 <= age <= SCANNER["maxDatabaseAgeHours"]:
        problems.append(f"the scanner's database is {age:.0f} hours old ({updated})")
    if report.get("SchemaVersion") != 2:
        problems.append(f"unknown report schema {report.get('SchemaVersion')}")
    system = (report.get("Metadata") or {}).get("OS") or {}
    if system.get("Family") != INPUTS["base"]["os"]:
        problems.append(
            f"the scanner read the system as {system.get('Family')}, not {INPUTS['base']['os']}"
        )
    results = report.get("Results") or []
    packages = sorted(
        f"{package['Name']} {package['Version']}"
        for result in results
        if result.get("Class") == "os-pkgs"
        for package in result.get("Packages") or []
    )
    if packages != INPUTS["base"]["packages"]:
        problems.append(
            f"the scanner saw other packages than the pinned base: {packages}"
        )
    machines = sorted(
        {
            str(package.get("Arch"))
            for result in results
            if result.get("Class") == "os-pkgs"
            for package in result.get("Packages") or []
        }
    )
    # A package without machine code names no architecture; every other one names the image's.
    if sorted(set(machines) - {"all", "noarch"}) != [MACHINES[architecture]]:
        problems.append(
            f"the scanner read packages built for {machines}, not for {architecture}"
        )
    findings = sorted(
        (
            {
                "id": finding.get("VulnerabilityID"),
                "package": finding.get("PkgName"),
                "installed": finding.get("InstalledVersion"),
                "fixed": finding.get("FixedVersion") or None,
                "severity": finding.get("Severity") or "UNKNOWN",
            }
            for result in results
            for finding in result.get("Vulnerabilities") or []
        ),
        key=lambda item: (
            SEVERITIES.index(item["severity"]) if item["severity"] in SEVERITIES else 9,
            str(item["id"]),
        ),
    )
    counts = collections.Counter(item["severity"] for item in findings)
    if findings:
        problems.append(
            f"{len(findings)} known finding(s): "
            + ", ".join(f"{counts[name]} {name}" for name in SEVERITIES if counts[name])
        )
    return problems, {
        "system": system,
        "packages": packages,
        "package_architecture": machines,
        "findings": {
            "total": len(findings),
            "by_severity": {name: counts[name] for name in SEVERITIES},
            "fixable": sum(1 for item in findings if item["fixed"]),
            "list": findings,
        },
    }


def reference(record):
    """The address of the published image a record names, or a refusal."""
    require(
        isinstance(record, dict)
        and set(record) == {"schema", "version", "image", "index"}
        and record["schema"] == "qrscan-oci-published/1",
        "published.json is not a record of the published image",
    )
    require(record["version"] == VERSION, "published.json records another version")
    require(record["image"] == IMAGE, "published.json names another image")
    require(
        isinstance(record["index"], str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", record["index"]),
        "published.json does not name an index digest",
    )
    return IMAGE + "@" + record["index"]


def receipt_of(subject, described, summary, problems, now):
    database_record = described.get("VulnerabilityDB") or {}
    return {
        "schema": "qrscan-oci-scan/1",
        "result": "FAIL" if problems else "PASS",
        "problems": problems,
        "version": VERSION,
        **subject,
        "scanner": {
            "image": SCANNER["image"],
            "version": described.get("Version"),
            "database_updated_at": database_record.get("UpdatedAt"),
            "database_downloaded_at": database_record.get("DownloadedAt"),
        },
        "scanned_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        **summary,
    }


def run(args):
    if args.published:
        if not PUBLISHED.exists():
            print(
                "::notice title=published image scan::no published "
                + VERSION
                + " image is recorded yet (distribution/docker/v0.12.2/published.json); nothing was scanned"
            )
            return 0
        address = reference(json.loads(PUBLISHED.read_text()))
    else:
        inspected = json.loads(
            subprocess.check_output(
                ["docker", "image", "inspect", args.image], text=True
            )
        )[0]
        require(
            inspected["Os"] == "linux" and inspected["Architecture"] in MACHINES,
            "the image is not one of the published platforms",
        )
    receipts = []
    with tempfile.TemporaryDirectory(prefix="qrscan-scan-") as directory:
        root = Path(directory)
        cache, work = root / "cache", root / "work"
        cache.mkdir()
        work.mkdir()
        described = database(cache)
        now = datetime.datetime.now(datetime.timezone.utc)
        if args.published:
            for architecture in MACHINES:
                out = root / ("out-" + architecture)
                out.mkdir()
                problems, summary = judge(
                    scan_remote(address, architecture, cache, out),
                    described,
                    now,
                    architecture,
                )
                subject = {"image": address, "platform": "linux/" + architecture}
                receipts.append(receipt_of(subject, described, summary, problems, now))
        else:
            out = root / "out"
            out.mkdir()
            problems, summary = judge(
                scan_local(args.image, cache, work, out),
                described,
                now,
                inspected["Architecture"],
            )
            subject = {
                "image": args.image,
                "image_id": inspected["Id"],
                "platform": inspected["Os"] + "/" + inspected["Architecture"],
            }
            receipts.append(receipt_of(subject, described, summary, problems, now))
    record = (
        receipts[0]
        if not args.published
        else {
            "schema": "qrscan-oci-published-scan/1",
            "result": "PASS"
            if all(item["result"] == "PASS" for item in receipts)
            else "FAIL",
            "platforms": receipts,
        }
    )
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    # One line per refused platform, where a workflow run shows it first.
    for item in receipts:
        for problem in item["problems"]:
            print(f"::error title=image scan · {item['platform']}::{problem[:300]}")
    return 0 if record["result"] == "PASS" else 1


def self_test():
    now = datetime.datetime(2026, 11, 27, 12, 0, tzinfo=datetime.timezone.utc)
    described = {
        "Version": SCANNER["version"],
        "VulnerabilityDB": {
            "UpdatedAt": "2026-11-27T07:06:44.674751291Z",
            "DownloadedAt": "2026-11-27T11:00:00Z",
        },
    }
    packages = [
        {"Name": name, "Version": version, "Arch": "aarch64"}
        for name, version in (item.split(" ") for item in INPUTS["base"]["packages"])
    ]

    def report(**changes):
        base = {
            "SchemaVersion": 2,
            "Metadata": {"OS": {"Family": INPUTS["base"]["os"], "Name": "test"}},
            "Results": [
                {
                    "Target": "test",
                    "Class": "os-pkgs",
                    "Type": INPUTS["base"]["os"],
                    "Packages": packages,
                }
            ],
        }
        return base | changes

    finding = {
        "VulnerabilityID": "CVE-0000-0001",
        "PkgName": packages[0]["Name"],
        "InstalledVersion": "1",
        "Severity": "LOW",
    }
    problems, summary = judge(report(), described, now, "arm64")
    assert problems == [] and summary["findings"]["total"] == 0, problems
    assert judge(report(), described, now, "amd64")[0], (
        "accepted packages of another platform"
    )
    mixed = report(
        Results=[
            report()["Results"][0]
            | {"Packages": [packages[0] | {"Arch": "noarch"}, *packages[1:]]}
        ]
    )
    assert judge(mixed, described, now, "arm64")[0] == [], (
        "refused a package without machine code"
    )
    assert summary["packages"] == INPUTS["base"]["packages"]
    refused = 0
    for name, candidate, version in [
        (
            "one low finding",
            report(Results=[report()["Results"][0] | {"Vulnerabilities": [finding]}]),
            described,
        ),
        (
            "a finding without a severity",
            report(
                Results=[
                    report()["Results"][0]
                    | {"Vulnerabilities": [finding | {"Severity": ""}]}
                ]
            ),
            described,
        ),
        (
            "a finding in a language package",
            report(
                Results=[
                    *report()["Results"],
                    {
                        "Target": "bin",
                        "Class": "lang-pkgs",
                        "Vulnerabilities": [finding],
                    },
                ]
            ),
            described,
        ),
        ("no package seen", report(Results=[]), described),
        (
            "a package missing",
            report(Results=[report()["Results"][0] | {"Packages": packages[1:]}]),
            described,
        ),
        (
            "a package at another version",
            report(
                Results=[
                    report()["Results"][0]
                    | {"Packages": [packages[0] | {"Version": "0"}, *packages[1:]]}
                ]
            ),
            described,
        ),
        (
            "packages of two platforms",
            report(
                Results=[
                    report()["Results"][0]
                    | {"Packages": [packages[0] | {"Arch": "x86_64"}, *packages[1:]]}
                ]
            ),
            described,
        ),
        (
            "only packages without machine code",
            report(
                Results=[
                    report()["Results"][0]
                    | {"Packages": [item | {"Arch": "noarch"} for item in packages]}
                ]
            ),
            described,
        ),
        (
            "another system",
            report(Metadata={"OS": {"Family": "debian", "Name": "12"}}),
            described,
        ),
        ("no system read", report(Metadata={}), described),
        ("another report schema", report(SchemaVersion=3), described),
        ("another scanner version", report(), described | {"Version": "0.0.0"}),
        (
            "a stale database",
            report(),
            described | {"VulnerabilityDB": {"UpdatedAt": "2026-11-20T07:00:00Z"}},
        ),
        (
            "a database from the future",
            report(),
            described | {"VulnerabilityDB": {"UpdatedAt": "2026-11-29T07:00:00Z"}},
        ),
        ("a database without a date", report(), described | {"VulnerabilityDB": {}}),
    ]:
        problems, _ = judge(candidate, version, now, "arm64")
        assert problems, "accepted " + name
        refused += 1
    failing = judge(
        report(
            Results=[
                report()["Results"][0]
                | {"Vulnerabilities": [finding | {"Severity": "CRITICAL"}, finding]}
            ]
        ),
        described,
        now,
        "arm64",
    )
    assert (
        failing[1]["findings"]["by_severity"]["CRITICAL"] == 1
        and failing[1]["findings"]["total"] == 2
    )
    assert failing[1]["findings"]["list"][0]["severity"] == "CRITICAL"
    record = {
        "schema": "qrscan-oci-published/1",
        "version": VERSION,
        "image": IMAGE,
        "index": "sha256:" + "a" * 64,
    }
    assert reference(record) == IMAGE + "@sha256:" + "a" * 64
    for name, bad in [
        ("another image", record | {"image": "ghcr.io/other/image"}),
        ("a tag", record | {"index": "0.12.2"}),
        ("a short digest", record | {"index": "sha256:abc"}),
        ("another version", record | {"version": "0.0.0"}),
        ("another schema", record | {"schema": "other/1"}),
        ("an extra key", record | {"extra": True}),
        ("a list", [record]),
    ]:
        try:
            reference(bad)
        except ValueError:
            refused += 1
        else:
            raise AssertionError("accepted " + name)
    assert re.fullmatch(
        r"ghcr\.io/aquasecurity/trivy@sha256:[0-9a-f]{64}", SCANNER["image"]
    )
    print(
        json.dumps({"result": "PASS", "accepted_reports": 1, "negative_cases": refused})
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?")
    parser.add_argument("--published", action="store_true")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if bool(args.image) == args.published:
        parser.error("give an image or --published")
    try:
        return run(args)
    except ValueError as error:
        # Not a finding: the scan could not be made or read. It is no pass either.
        print(f"::error title=image scan::{error}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
