#!/usr/bin/env python3
"""Run a real stdio MCP session and check the returned totals against archived records."""
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Implementation


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence/current/mcp_run.json"
EXPECTED_TOOLS = {"list_evidence", "summarize_archived_results", "read_architecture_excerpt"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def serialize(model) -> dict:
    return model.model_dump(mode="json", by_alias=True, exclude_none=True)


async def main() -> int:
    observed_version = importlib.metadata.version("mcp")
    record = {
        "status": "RUNNING",
        "started_at_utc": now(),
        "scope": "Actual local stdio MCP authoring/provenance session; no traffic-controller or online-publication operation.",
        "sdk": {"package": "mcp", "version": observed_version, "required_version": "1.29.0"},
        "python_version": sys.version.split()[0],
        "server_entry_point": "mcp/evidence_server.py",
        "client_entry_point": "mcp/demo_client.py",
        "source_sha256": {
            "mcp/evidence_server.py": digest(ROOT / "mcp/evidence_server.py"),
            "mcp/demo_client.py": digest(ROOT / "mcp/demo_client.py"),
        },
        "events": [],
        "checks": [],
        "remote_writes": False,
        "overleaf_publication_verified": False,
        "github_publication_verified": False,
        "learning_platform_submission_verified": False,
    }
    def check(name: str, passed: bool, details) -> None:
        record["checks"].append({"name": name, "passed": bool(passed), "details": details})

    async def event(method: str, request: dict, awaitable):
        started = now()
        response = await awaitable
        record["events"].append({
            "method": method,
            "request": request,
            "started_at_utc": started,
            "completed_at_utc": now(),
            "response": serialize(response),
        })
        return response

    try:
        check("pinned_sdk_version", observed_version == "1.29.0", observed_version)
        if observed_version != "1.29.0":
            raise RuntimeError("Install the pinned mcp/requirements.txt before running this demonstration.")
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(ROOT / "mcp/evidence_server.py")],
            cwd=ROOT,
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(
                read_stream, write_stream,
                client_info=Implementation(name="traffic-assistant-evidence-demo", version="1.0.0"),
            ) as session:
                initialized = await event("initialize", {"clientInfo": {"name": "traffic-assistant-evidence-demo", "version": "1.0.0"}}, session.initialize())
                record["negotiated_protocol_version"] = initialized.protocolVersion
                record["server_info"] = serialize(initialized.serverInfo)
                tools = await event("tools/list", {}, session.list_tools())
                advertised = {tool.name for tool in tools.tools}
                check("exact_tool_allowlist", advertised == EXPECTED_TOOLS, sorted(advertised))
                check("read_only_tool_annotations", all(tool.annotations and tool.annotations.readOnlyHint is True and tool.annotations.destructiveHint is False for tool in tools.tools), sorted(advertised))
                responses = {}
                for name in ("list_evidence", "summarize_archived_results", "read_architecture_excerpt"):
                    result = await event("tools/call", {"name": name, "arguments": {}}, session.call_tool(name, {}))
                    if result.isError or result.structuredContent is None:
                        raise RuntimeError(f"MCP tool did not return successful structured content: {name}")
                    responses[name] = result.structuredContent

        # Independent local arithmetic checks use the preserved original 54 records,
        # not the current audit's precomputed pair totals.
        original_path = ROOT / "evidence/archive/dic3/evidence/firmware_validation_original.json"
        original = json.loads(original_path.read_text(encoding="utf-8"))
        rows = original["scenarios"]
        fixed = {(row["scenario"], row["seed"]): row for row in rows if row["policy"] == "fixed_balanced"}
        model = {(row["scenario"], row["seed"]): row for row in rows if row["policy"] == "tiny_tree_rules_fallback"}
        check("archived_pair_keys_match", set(fixed) == set(model), {"fixed_pairs": len(fixed), "model_pairs": len(model)})
        fixed_total = sum(row["queue_vehicle_seconds"] for row in fixed.values())
        model_total = sum(row["queue_vehicle_seconds"] for row in model.values())
        regressed = sum(model[key]["queue_vehicle_seconds"] > fixed[key]["queue_vehicle_seconds"] for key in fixed)
        relative_change = (model_total - fixed_total) / fixed_total * 100.0
        summary = responses["summarize_archived_results"]["host_18_pair_summary"]
        for field, expected in (("pairs", len(fixed)), ("fixed_qvs", fixed_total), ("model_qvs", model_total), ("regressed", regressed)):
            check(f"mcp_summary_matches_original_{field}", summary[field] == expected, {"returned": summary[field], "recomputed_from_archive": expected})
        check("mcp_relative_change_matches_archive", math.isclose(summary["qvs_relative_change_percent"], relative_change, rel_tol=1e-12, abs_tol=1e-12), {"returned": summary["qvs_relative_change_percent"], "recomputed_from_archive": relative_change})
        for item in responses["list_evidence"]["files"]:
            check(f"source_hash_{item['evidence_id']}", digest(ROOT / item["path"]) == item["sha256"], {"path": item["path"], "sha256": item["sha256"]})
        excerpts = responses["read_architecture_excerpt"]
        architecture_lines = (ROOT / excerpts["source"]["path"]).read_text(encoding="utf-8").splitlines()
        check("architecture_excerpt_matches_retained_source", all(section["text"] == "\n".join(architecture_lines[section["start_line"] - 1:section["end_line"]]).rstrip() for section in excerpts["sections"]), [section["heading"] for section in excerpts["sections"]])
        check("historical_status_preserved", all(responses["summarize_archived_results"][key] is False for key in ("new_training", "new_firmware_simulation", "new_model_inference", "new_hardware_run", "raw_hardware_trace_revalidation")), "No new training, traffic simulation, inference, hardware run, or raw hardware trace revalidation is claimed.")
        record["independent_archive_check"] = {
            "path": str(original_path.relative_to(ROOT)),
            "sha256": digest(original_path),
            "original_records": len(rows),
            "paired_fixed_and_model_records": len(fixed),
            "fixed_qvs": fixed_total,
            "model_qvs": model_total,
            "regressions": regressed,
            "qvs_relative_change_percent": relative_change,
            "kind": "arithmetic over preserved historical records; not re-execution of the traffic model",
        }
        record["status"] = "PASS" if all(item["passed"] for item in record["checks"]) else "FAIL"
    except Exception as exc:
        record["status"] = "FAIL"
        record["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        record["completed_at_utc"] = now()
        record["checks_passed"] = sum(item["passed"] for item in record["checks"])
        record["checks_total"] = len(record["checks"])
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MCP session: {record['status']} ({record['checks_passed']}/{record['checks_total']} checks)")
    print(f"Actual request methods: {', '.join(item['method'] for item in record['events'])}")
    print("Saved: evidence/current/mcp_run.json")
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
