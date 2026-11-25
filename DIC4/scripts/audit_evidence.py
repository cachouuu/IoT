#!/usr/bin/env python3
"""Recalculate archived DIC3 evidence without running firmware or hardware.

Usage:
  python audit_dic3_evidence.py --source-root /path/to/DIC3_2026-11-13 --output-dir /path/to/audit

All source files are read-only. This script checks arithmetic, reported internal
consistency, overlap between batches, and snapshot hashes. It cannot establish
the truth of past executions without the missing raw traces and executable source.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percent_change(fixed: int, model: int) -> float:
    return 100.0 * (model - fixed) / fixed


def load_json(root: Path, name: str):
    return json.loads((root / name).read_text(encoding="utf-8"))


def pair(scenario: str, seed: int, fixed: dict, model: dict) -> dict:
    return {
        "scenario": scenario,
        "seed": seed,
        "arrived_vehicles": fixed["arrived_vehicles"],
        "fixed_qvs": fixed["queue_vehicle_seconds"],
        "model_qvs": model["queue_vehicle_seconds"],
        "qvs_delta": model["queue_vehicle_seconds"] - fixed["queue_vehicle_seconds"],
        "qvs_relative_change_percent": percent_change(fixed["queue_vehicle_seconds"], model["queue_vehicle_seconds"]),
        "fixed_departed": fixed["departed_vehicles"],
        "model_departed": model["departed_vehicles"],
        "fixed_total_wait_departed_seconds": fixed["total_wait_departed_seconds"],
        "model_total_wait_departed_seconds": model["total_wait_departed_seconds"],
        "fixed_mean_wait_departed_seconds": fixed["total_wait_departed_seconds"] / fixed["departed_vehicles"],
        "model_mean_wait_departed_seconds": model["total_wait_departed_seconds"] / model["departed_vehicles"],
        "fixed_end_queue_ns": fixed["end_queue_ns"],
        "fixed_end_queue_ew": fixed["end_queue_ew"],
        "model_end_queue_ns": model["end_queue_ns"],
        "model_end_queue_ew": model["end_queue_ew"],
        "model_decisions": model["model_decisions"],
        "model_fallbacks": model["fallbacks"],
    }


def summarize(pairs: list[dict]) -> dict:
    fields = ["arrived_vehicles", "fixed_qvs", "model_qvs", "fixed_departed", "model_departed",
              "fixed_total_wait_departed_seconds", "model_total_wait_departed_seconds",
              "fixed_end_queue_ns", "fixed_end_queue_ew", "model_end_queue_ns", "model_end_queue_ew",
              "model_decisions", "model_fallbacks"]
    out = {k: sum(row[k] for row in pairs) for k in fields}
    out.update({
        "pairs": len(pairs),
        "qvs_delta": out["model_qvs"] - out["fixed_qvs"],
        "qvs_relative_change_percent": percent_change(out["fixed_qvs"], out["model_qvs"]),
        "improved": sum(p["model_qvs"] < p["fixed_qvs"] for p in pairs),
        "regressed": sum(p["model_qvs"] > p["fixed_qvs"] for p in pairs),
        "unchanged": sum(p["model_qvs"] == p["fixed_qvs"] for p in pairs),
        "worst_relative_change_case": max(pairs, key=lambda p: p["qvs_relative_change_percent"]),
        "best_relative_change_case": min(pairs, key=lambda p: p["qvs_relative_change_percent"]),
        "weighted_mean_wait_departed_fixed_seconds": out["fixed_total_wait_departed_seconds"] / out["fixed_departed"],
        "weighted_mean_wait_departed_model_seconds": out["model_total_wait_departed_seconds"] / out["model_departed"],
    })
    return out


def markdown_numeric_table(section: str) -> dict:
    rows = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and re.fullmatch(r"[\d.,]+", cells[1]) and re.fullmatch(r"[\d.,]+", cells[2]):
            rows[cells[0]] = [float(c.replace(",", "")) if "." in c else int(c.replace(",", "")) for c in cells[1:]]
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.source_root.resolve()
    outdir = args.output_dir.resolve()
    if outdir == root or root in outdir.parents:
        raise SystemExit("Output must be outside the original evidence package.")
    outdir.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name: str, ok: bool, details=None):
        item = {"name": name, "passed": bool(ok)}
        if details is not None:
            item["details"] = details
        checks.append(item)

    raw = load_json(root, "evidence/firmware_validation_original.json")
    six = load_json(root, "evidence/comparison_6pairs_original.json")
    oldaudit = load_json(root, "evidence/data_audit.json")
    manifest = load_json(root, "source_manifest.json")
    report_text = (root / "evidence/EXPERIMENT_REPORT_original.md").read_text(encoding="utf-8")
    header = (root / "source/traffic_model.h").read_text(encoding="utf-8")
    agent_source = (root / "source/traffic_agent.c").read_text(encoding="utf-8")
    rows = raw["scenarios"]
    check("54 archived policy records", len(rows) == raw["cases"] == 54)
    check("archived report identifies host-only validation", raw["is_physical_board_validation"] is False and raw["is_real_traffic_evidence"] is False)
    check("all archived records reported passed", raw["passed"] is True and all(r["passed"] for r in rows) and not raw["failures"])
    check("all archived records have 600 observations", all(r["seconds"] == 600 for r in rows))
    check("all archived records conserve vehicles", all(r["arrived_vehicles"] == r["departed_vehicles"] + r["end_queue_ns"] + r["end_queue_ew"] for r in rows))
    check("all archived records have 20 decisions and consistent plan counts", all(r["decisions"] == 20 and sum(r["plan_counts"]) == r["decisions"] for r in rows))
    check("all archived error flags zero", all(r["error_flags"] == 0 for r in rows))
    check("historical compared application count", sum(r["applied_decisions_compared"] for r in rows) == raw["applied_decisions_compared"] == 1026)
    check("historical unused final decision count", len([r for r in rows if "unused_final_decision_checked" in r]) == raw["unused_final_decisions_checked"] == 54)
    check("historical final decision row is 599", all(r["unused_final_decision_checked"]["observed_second"] == 599 for r in rows))

    grouped = defaultdict(dict)
    for r in rows:
        key = (r["scenario"], r["seed"])
        check(f"unique archived policy {key}/{r['policy']}", r["policy"] not in grouped[key])
        grouped[key][r["policy"]] = r
    pairs18 = []
    rules_comparison = []
    for (scenario, seed), policies in grouped.items():
        check(f"three policies for {scenario}/{seed}", set(policies) == {"fixed_balanced", "reference_rules", "tiny_tree_rules_fallback"})
        f, m, ref = policies["fixed_balanced"], policies["tiny_tree_rules_fallback"], policies["reference_rules"]
        check(f"same aggregate arrivals for {scenario}/{seed}", f["arrived_vehicles"] == m["arrived_vehicles"] == ref["arrived_vehicles"])
        check(f"tree plus fallback decisions for {scenario}/{seed}", m["model_decisions"] + m["fallbacks"] == m["decisions"])
        pairs18.append(pair(scenario, seed, f, m))
        rules_comparison.append({"scenario": scenario, "seed": seed, "rule_qvs": ref["queue_vehicle_seconds"], "model_qvs": m["queue_vehicle_seconds"], "model_minus_rule_qvs": m["queue_vehicle_seconds"] - ref["queue_vehicle_seconds"]})
    summary18 = summarize(pairs18)
    check("18 historical pairs", len(pairs18) == 18)
    computed_policy_totals = {policy: sum(r["queue_vehicle_seconds"] for r in rows if r["policy"] == policy) for policy in raw["queue_vehicle_seconds_totals_18_scenarios"]}
    check("historical stored policy totals match", computed_policy_totals == raw["queue_vehicle_seconds_totals_18_scenarios"])

    pairs6 = []
    overlap = []
    common_fields = ["seconds", "arrived_vehicles", "departed_vehicles", "queue_vehicle_seconds", "total_wait_departed_seconds", "end_queue_ns", "end_queue_ew", "decisions", "model_decisions", "fallbacks", "plan_counts", "error_flags", "engine_bytes"]
    for p in six["pairs"]:
        f, m = p["fixed"], p["model"]
        key = (p["scenario"], p["seed"])
        item = pair(*key, f, m)
        pairs6.append(item)
        check(f"six-pair percent for {key}", math.isclose(item["qvs_relative_change_percent"], p["queue_change_percent"], abs_tol=1e-10))
        check(f"six-pair conservation {key}", all(r["arrived_vehicles"] == r["departed_vehicles"] + r["end_queue_ns"] + r["end_queue_ew"] for r in (f, m)))
        check(f"six-pair reporting window {key}", f["seconds"] == m["seconds"] == 600 and f["decisions"] == m["decisions"] == 20 and f["applied_confirmations"] == m["applied_confirmations"] == 19)
        check(f"six-pair model storage {key}", f["model_bytes"] == m["model_bytes"] == 4104 and f["engine_bytes"] == m["engine_bytes"] == 2264)
        field_matches = {policy: all(record[k] == grouped[key][hist_policy][k] for k in common_fields) for policy, record, hist_policy in (("fixed", f, "fixed_balanced"), ("model", m, "tiny_tree_rules_fallback"))}
        overlap.append({"scenario": key[0], "seed": key[1], "matches_historical_fields": field_matches, "compared_fields": common_fields})
    summary6 = summarize(pairs6)
    check("six-pair summary matches", summary6["pairs"] == six["pair_count"] == 6 and summary6["fixed_qvs"] == six["fixed_queue_vehicle_seconds"] and summary6["model_qvs"] == six["model_queue_vehicle_seconds"] and summary6["improved"] == six["better"] and summary6["regressed"] == six["worse"] and math.isclose(summary6["qvs_relative_change_percent"], six["queue_change_percent"], abs_tol=1e-10))
    check("six-pair records match one historical seed subset", all(all(x["matches_historical_fields"].values()) for x in overlap) and {p["seed"] for p in pairs6} == {2779054081})
    for key, computed in (("host_18_pairs", summary18), ("host_6_pairs", summary6)):
        saved = oldaudit[key]
        check(f"previous data audit {key} agrees", all(saved[k] == computed[k] for k in ("pairs", "fixed_qvs", "model_qvs", "improved", "regressed", "unchanged")) and math.isclose(saved["relative_change_percent"], computed["qvs_relative_change_percent"], abs_tol=1e-10))

    by_scenario = defaultdict(list)
    for p in pairs18:
        by_scenario[p["scenario"]].append(p)
    scenario_summaries = [{"scenario": k, **summarize(v)} for k, v in by_scenario.items()]

    board_section = report_text.split("## 4. 本次實板兩輪：全部通過", 1)[1].split("### 4.1", 1)[0]
    board = markdown_numeric_table(board_section)
    board_capture_section = report_text.split("### 4.1 完整採集及核對", 1)[1].split("### 4.2", 1)[0]
    board_capture = markdown_numeric_table(board_capture_section)
    board_qvs_change = percent_change(*board["排隊車秒"])
    board_means = [w / n for w, n in zip(board["已放行等待總秒數"], board["放行數"])]
    check("narrative board pair conserves vehicles", all(board["到車數"][i] == board["放行數"][i] + board["期末南北佇列"][i] + board["期末東西佇列"][i] for i in (0, 1)))
    check("narrative board average waits round correctly", all(abs(v - stated) <= 0.0005 for v, stated in zip(board_means, board["已放行平均等待（秒）"])))
    check("narrative board reduction rounds to 70.21 percent", round(-board_qvs_change, 2) == 70.21)
    check("narrative accepted and discarded sample sums", all(board_capture["原始樣本數"][i] == board_capture["接受的執行樣本"][i] + board_capture["丟棄跨更新樣本"][i] for i in (0, 1)))
    ds = next(p for p in pairs6 if p["scenario"] == "direction_switch")
    check("narrative board QVS matches archived host pair", board["排隊車秒"] == [ds["fixed_qvs"], ds["model_qvs"]])

    snapshot_integrity = []
    for item in manifest["files"]:
        path = root / item["snapshot"]
        actual_sha = sha256(path)
        actual_bytes = path.stat().st_size
        result = {"snapshot": item["snapshot"], "sha256": actual_sha, "bytes": actual_bytes, "matches_manifest_sha256": actual_sha == item["sha256"], "matches_manifest_bytes": actual_bytes == item["bytes"]}
        snapshot_integrity.append(result)
        check(f"snapshot integrity {item['snapshot']}", result["matches_manifest_sha256"] and result["matches_manifest_bytes"])
    check("firmware record C source hash matches snapshot", sha256(root / "source/traffic_agent.c") == raw["source_sha256"]["embedded/firmware/traffic_agent.c"])
    check("firmware record model header hash matches snapshot", sha256(root / "source/traffic_model.h") == raw["source_sha256"]["embedded/model/traffic_model.h"])
    macros = dict(re.findall(r"#define\s+(TA_MODEL_\w+)\s+([^\n]+)", header))
    check("model identifier matches recorded validation", macros["TA_MODEL_SHA256"].strip('"') == raw["model_sha256"])
    check("rule call precedes policy branch in recovered source", agent_source.index("best=ta_rule_plan(d->queue_ns") < agent_source.index("if(s->policy==TA_POLICY_FIXED)"))

    missing = [
        "source/traffic_model.c (tree node arrays and inference implementation)",
        "source/traffic_agent.h (engine types, queue capacity, flag constants)",
        "synthetic_test_vectors.csv (per-second saved arrivals)",
        "traffic_core.py / host runner / build files",
        "FPGA RTL / bitstream / ARM ELF / platform source",
        "raw board JSONL and per-second/decision traces",
        "board validation JSON, input/build manifests, preservation and recovery records",
        "training dataset/generator, hyperparameters, and training run records",
    ]
    rules_total = computed_policy_totals["reference_rules"]
    model_total = computed_policy_totals["tiny_tree_rules_fallback"]
    rules_summary = {
        "scope": "Contextual check of archived third policy, not a newly run comparator",
        "rule_qvs": rules_total, "model_qvs": model_total,
        "model_minus_rule_qvs": model_total - rules_total,
        "model_vs_rule_relative_change_percent": percent_change(rules_total, model_total),
        "model_better_cases": sum(p["model_minus_rule_qvs"] < 0 for p in rules_comparison),
        "model_worse_cases": sum(p["model_minus_rule_qvs"] > 0 for p in rules_comparison),
        "equal_cases": sum(p["model_minus_rule_qvs"] == 0 for p in rules_comparison),
        "cases": rules_comparison,
    }
    result = {
        "status": "PASS" if all(c["passed"] for c in checks) else "FAIL",
        "kind": "independent_recalculation_of_archived_DIC3_records",
        "new_training": False, "new_firmware_simulation": False, "new_model_inference": False,
        "new_hardware_run": False, "raw_hardware_trace_revalidation": False,
        "checked_record_count": len(rows), "checks_passed": sum(c["passed"] for c in checks), "checks_total": len(checks),
        "host_18_pair_summary": summary18, "host_18_pairs": pairs18,
        "host_18_pair_scenario_aggregates": scenario_summaries,
        "host_6_pair_summary": summary6, "host_6_pairs": pairs6,
        "batch_overlap": {"six_pair_records_are_matching_one_seed_subset": True, "independent_sample_counts_must_not_be_added": True, "details": overlap},
        "archived_reference_rules_context": rules_summary,
        "archived_board_narrative": {"source": "evidence/EXPERIMENT_REPORT_original.md section 4", "evidence_level": "narrative_report_only; arithmetic_checked; raw_traces_unavailable", "table": board, "qvs_relative_change_percent": board_qvs_change, "recomputed_mean_wait_departed_seconds": board_means, "sample_table": board_capture, "input_array_sha256_reported_not_rechecked": "d44f4d405d50bae28cda6ecc4652e7e15e10e2055177ee1eba5ac2c554a7fde1", "input_array_crc32_reported_not_rechecked": "98eb45b4"},
        "model_header_macros": macros,
        "snapshot_integrity": snapshot_integrity,
        "limits": {"original_external_files_accessed": False, "snapshot_hashes_do_not_independently_authenticate_historical_execution": True, "missing_to_rerun_original_experiments": missing,
                   "model_size_and_engine_size": "4104 and 2264 bytes are corroborated archived record values; not newly compiled sizeof measurements",
                   "speedup": "No timing/energy/area measurement supplied; recovered engine computes three-plan rule costs before invoking tree policy."},
        "checks": checks,
    }
    (outdir / "audit_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for filename, records in (("host_18_pairs_recalculated.csv", pairs18), ("host_6_pairs_recalculated.csv", pairs6)):
        with (outdir / filename).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    print(json.dumps({k: result[k] for k in ("status", "kind", "checks_passed", "checks_total")}, ensure_ascii=False))
    for label, summary in (("historical_18_pairs", summary18), ("saved_6_pairs", summary6)):
        print(json.dumps({"batch": label, **{k: summary[k] for k in ("pairs", "fixed_qvs", "model_qvs", "qvs_relative_change_percent", "improved", "regressed", "model_decisions", "model_fallbacks")}}, ensure_ascii=False))
    print(json.dumps({"archived_rules_context": {k: v for k, v in rules_summary.items() if k != "cases"}}, ensure_ascii=False))
    print(json.dumps({"archived_board_narrative_percent": board_qvs_change, "raw_board_traces_available": False}))
    if not all(c["passed"] for c in checks):
        for c in checks:
            if not c["passed"]:
                print("FAILED", c)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
