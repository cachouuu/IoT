#!/usr/bin/env python3
"""Read-only MCP tools for this manuscript's fixed, retained evidence files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "current_arithmetic_audit": "evidence/current/audit_results.json",
    "archived_architecture": "evidence/archive/dic3/source/DESIGN_original.md",
    "archived_host_records": "evidence/archive/dic3/evidence/firmware_validation_original.json",
}
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
server = FastMCP(
    "traffic-assistant-evidence",
    instructions=(
        "Read the fixed manuscript evidence files. These tools support authoring and "
        "provenance; they do not control traffic hardware, modify files, or publish "
        "to Overleaf or GitHub. Historical results remain historical."
    ),
    log_level="WARNING",
)


def file_info(key: str) -> dict:
    relative = FILES[key]
    path = ROOT / relative
    data = path.read_bytes()
    return {
        "evidence_id": key,
        "path": relative,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


@server.tool(annotations=READ_ONLY, structured_output=True)
def list_evidence() -> dict[str, Any]:
    """List three fixed retained evidence files and their actual byte hashes."""
    return {
        "scope": "fixed project artifacts only",
        "files": [file_info(key) for key in FILES],
    }


@server.tool(annotations=READ_ONLY, structured_output=True)
def summarize_archived_results() -> dict[str, Any]:
    """Read audited historical summaries; this call does not rerun traffic experiments."""
    audit = json.loads((ROOT / FILES["current_arithmetic_audit"]).read_text(encoding="utf-8"))
    return {
        "source": file_info("current_arithmetic_audit"),
        "kind": audit["kind"],
        "audit_status": audit["status"],
        "checks_passed": audit["checks_passed"],
        "checks_total": audit["checks_total"],
        "host_18_pair_summary": audit["host_18_pair_summary"],
        "host_6_pair_summary": audit["host_6_pair_summary"],
        "six_pairs_match_a_one_seed_subset": audit["batch_overlap"]["six_pair_records_are_matching_one_seed_subset"],
        "independent_sample_counts_must_not_be_added": audit["batch_overlap"]["independent_sample_counts_must_not_be_added"],
        "board_evidence_level": audit["archived_board_narrative"]["evidence_level"],
        "new_training": audit["new_training"],
        "new_firmware_simulation": audit["new_firmware_simulation"],
        "new_model_inference": audit["new_model_inference"],
        "new_hardware_run": audit["new_hardware_run"],
        "raw_hardware_trace_revalidation": audit["raw_hardware_trace_revalidation"],
        "interpretation": "Archived synthetic FIFO evidence; current arithmetic checks are not new traffic or board experiments.",
    }


@server.tool(annotations=READ_ONLY, structured_output=True)
def read_architecture_excerpt() -> dict[str, Any]:
    """Return exact retained design sections 2 and 5, with source line ranges."""
    lines = (ROOT / FILES["archived_architecture"]).read_text(encoding="utf-8").splitlines()
    sections = []
    for prefix in ("## 2 ", "## 5 "):
        start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        sections.append({
            "heading": lines[start],
            "start_line": start + 1,
            "end_line": end,
            "text": "\n".join(lines[start:end]).rstrip(),
        })
    return {
        "source": file_info("archived_architecture"),
        "kind": "verbatim archived design excerpts; original temporal wording is preserved",
        "sections": sections,
    }


if __name__ == "__main__":
    server.run(transport="stdio")
