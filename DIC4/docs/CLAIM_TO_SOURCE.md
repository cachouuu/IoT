# Claim-to-source map

All paths below are relative to the repository root. `archive` identifies retained input; `current` identifies work actually performed for DIC4.

| Claim in the manuscript | Source | Evidence boundary |
|---|---|---|
| Three NS/EW plans, 30 s total, fixed phase order | `evidence/archive/dic3/source/traffic_agent.c`, `ta_phase_seconds`; preserved design section 2 | Source inspection, not new RTL simulation |
| Four features and trained domain | `evidence/archive/dic3/source/traffic_model.h`; preserved design section 5 | Header/domain contract; no new model training |
| 513 nodes / depth 10 | Model header | Declared model structure; full `traffic_model.c` is unavailable |
| 4,104-byte model | `evidence/archive/dic3/evidence/firmware_validation_original.json` and archived report | Historical reported size, not a fresh binary-size measurement |
| Scaled-by-30 fluid scoring recurrence and tie-breaking | Engine C, `ta_rule_plan` | Exact inspection of preserved function |
| All candidate rule scores computed before tree branch | Engine C, `engine_poll` | No measured tree speedup claim |
| 399,954 vs 326,830; 13 better / 5 worse | Archived firmware JSON; `evidence/current/audit_results.json` | Current arithmetic audit of saved summaries |
| 137,493 vs 110,395 detailed subset | `comparison_6pairs_original.json`; current audit | Same seed subset, not independent replication |
| Rules total 326,533; model 297 QVS higher | Original third-policy records; current audit | Reanalysis only; no new third-policy experiment |
| 329 tree decisions / 31 fallbacks | Original summaries; current audit | Entire tree-plus-fallback policy evaluated |
| 19 applied decisions in 600 observations, final unused decision separately checked | Original firmware JSON / comparison JSON | Host window contract; final board confirmation is a separate report-level claim |
| Historical board pair and 20/20 confirmation | `evidence/archive/dic3/evidence/EXPERIMENT_REPORT_original.md` | Archived narrative/table only; linked raw traces absent |
| Current 164/164 checks | `evidence/current/audit_results.json` and `scripts/audit_evidence.py` | Current consistency, arithmetic and source checks; not hardware validation |
| Current MCP 14/14 checks | `evidence/current/mcp_run.json` | Actual SDK session and tool responses, independent total comparison |
| OpenSpec validation | `evidence/current/openspec/` | Actual CLI validation; task statuses remain separate |
| PDF compile and visual review | `evidence/current/pdf_qa.json` | Current PDF only; Overleaf online compilation recorded separately |

The source JSON explicitly identifies the 54 historical records as host validation, not physical-board validation or real-traffic evidence. Hash agreement preserves version identity; it cannot by itself establish a past experiment's execution.

