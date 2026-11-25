## Why

DIC4 asks for an IEEE conference draft in Overleaf and OpenSpec on GitHub, using MCP. The existing DIC3 material already defines the Traffic Timing Assistant, its bounded ARM/FPGA prototype, and historical synthetic FIFO results. These materials need a coherent conference manuscript, inspectable source provenance, a portable build, and an accurate record of what has and has not been published online.

## What Changes

- Prepare an English IEEE conference-style draft with abstract, related work, architecture, timing contracts, evaluation, limitations, and references.
- Preserve historical source snapshots and distinguish arithmetic rechecks from new traffic experiments or board measurements.
- Package the LaTeX manuscript for an independently reproducible PDF build and Overleaf import.
- Document actual MCP tool use and retain a concise record without credentials or private connection metadata.
- Package the OpenSpec documents for GitHub and track online publication separately from local artifact completion.

## Capabilities

### New Capabilities

- `conference-draft`: Traceable manuscript, qualified evidence, references, reproducible rendering, source packaging, MCP use record, and publication status.

### Modified Capabilities

None. The existing `traffic-control-core`, `paired-evaluation`, and DIC3 `proposal-documentation` specifications are preserved. The separate `integrate-task-workflow` change remains pending.

## Impact

Documentation, build instructions, evidence audit, and deliverable packaging. This change does not implement the pending task layer, retrain the decision tree, modify firmware or RTL, or establish real-road effectiveness. Overleaf and GitHub publication require observed successful operations and valid resulting links before being marked complete.
