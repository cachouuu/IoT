#!/usr/bin/env python3
"""Run the pinned OpenSpec CLI and retain its real output (Python standard library)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", type=Path, help="Optional path to the installed openspec.js CLI")
    parser.add_argument("--output-dir", type=Path, help="Log directory; defaults to evidence/openspec_current")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cli = args.cli.resolve() if args.cli else root / "node_modules/@fission-ai/openspec/bin/openspec.js"
    if not cli.is_file():
        parser.error("OpenSpec is not installed. Run npm ci --ignore-scripts from the project root first.")
    node = shutil.which("node")
    if node is None:
        parser.error("Node.js is required by the pinned OpenSpec CLI.")
    out = args.output_dir.resolve() if args.output_dir else root / "evidence/openspec_current"
    out.mkdir(parents=True, exist_ok=True)
    commands = [
        ("version", ["--version"]),
        ("validate_all", ["validate", "--all", "--strict", "--no-interactive", "--json"]),
        ("main_specs", ["list", "--specs", "--json"]),
        ("active_changes", ["list", "--json"]),
        ("dic4_status", ["status", "--change", "prepare-ieee-conference-draft", "--json"]),
        ("product_status", ["status", "--change", "integrate-task-workflow", "--json"]),
    ]
    records = []
    for label, argv in commands:
        proc = subprocess.run([node, str(cli), *argv], cwd=root, text=True, capture_output=True)
        (out / f"{label}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (out / f"{label}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
        if "--json" in argv and proc.stdout.strip():
            try:
                parsed = json.loads(proc.stdout)
            except json.JSONDecodeError:
                parsed = None
            if parsed is not None:
                (out / f"{label}.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        records.append({"label": label, "arguments": argv, "exit_code": proc.returncode})
        print(f"{label}: exit {proc.returncode}")
    version_text = (out / "version.stdout.txt").read_text(encoding="utf-8").strip()
    expected_version = "2.0.0"
    version_matches = version_text == expected_version
    ok = version_matches and all(record["exit_code"] == 0 for record in records)
    manifest = {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "expected_cli_version": expected_version,
        "observed_cli_version": version_text,
        "version_matches": version_matches,
        "commands": records,
        "all_commands_succeeded": ok,
        "scope": "OpenSpec document structure and workflow metadata only; no traffic, board, or publication verification.",
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Logs: {out}")
    if not version_matches:
        print(f"Expected OpenSpec {expected_version}; observed {version_text!r}.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
