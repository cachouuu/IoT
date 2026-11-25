## Why
The current prototype has numerical decision and execution components, but structured task intake, cross-source qualification and a unified decision/execution report remain incompletely integrated.
## What Changes
- Add structured requests and explicit review/execute behavior.
- Add data qualification with rejection reasons and causal evidence records.
- Integrate submitted/applied/timeout/mismatch states and a unified report.
- Reuse the existing tree, firmware fallback, AXI path and timing contracts.
## Capabilities
### New Capabilities
- `task-intake`: Request fields and read-only review.
- `data-qualification`: Provenance, coverage, pairing, missingness and interface capacity.
- `decision-evidence`: Actual features, model identity and faithful explanations.
- `execution-verification`: Submission guards and matching application evidence.
- `task-reporting`: Unified outcome reports and qualified comparisons.
### Modified Capabilities
None. traffic-control-core and paired-evaluation are preserved baseline contracts.
## Impact
Future host/task integration and tests. Product implementation is NOT performed by the DIC3 document task. No new model, LLM, road deployment, or firmware/RTL changes are implied.
