## Context

The retained DIC3 package describes a single-intersection, two-axis educational prototype. The ARM side uses four integer features and an existing decision tree with firmware rule fallback to select three timing plans. The FPGA uses a 30-second cycle and adopts pending plans at complete cycle boundaries. Existing results were generated under synthetic input and a simplified FIFO model. Only source snapshots and archived result records are available for this writing task; any new check must identify exactly what it executed.

## Goals / Non-Goals

**Goals:** produce a readable IEEE conference draft; connect each numerical claim to its retained source; make the manuscript reproducible; preserve historical and current verification separately; make the OpenSpec work reviewable; and record actual MCP use and publication state.

**Non-goals:** new traffic experiments, reconstructed road measurements, tree retraining, RTL or firmware modification, task-layer implementation, safety certification, or a claim of accepted conference publication.

## Decisions

1. **Preserve the prototype contract.** The source design, model header, firmware snapshot, and recorded experiments ground the technical description. Inherited requirements are not silently rewritten during a document task.
2. **Treat experiment batches separately.** The 18-pair host batch, separate 6-pair batch, and archived board validation retain their identities. Recomputing a percentage from recorded totals is an arithmetic audit, not a repeat experiment.
3. **Show counterexamples.** Queue vehicle-seconds are accompanied by the available regressions, completed-vehicle waiting metrics, throughput, and residual queues. Missing fields remain explicitly unavailable.
4. **Keep diagram status visible.** Existing control components and proposed workflow integration have distinguishable labels; a diagram does not imply unimplemented features are operational.
5. **Use an actual IEEE conference class.** The manuscript uses the IEEE conference format and documents its compiler and dependencies. A rendered PDF is reviewed visually in addition to compiling successfully.
6. **Make references auditable.** Primary papers and official documentation support external claims. Findings from unrelated platforms are not presented as this prototype's results.
7. **Keep MCP evidence factual.** The record identifies real tool calls, their purposes, and outcome summaries. A real source-retrieval call is useful evidence, but is not relabeled as direct Overleaf editing or GitHub publication.
8. **Separate local completion from online availability.** A ready-to-import ZIP is a local artifact; an Overleaf project exists only after a successful upload/import. A GitHub-ready source folder is distinct from an accessible repository.

## Risks / Trade-offs

- Archival records may lack complete original run inputs or the full build environment. State this limit instead of implying end-to-end reproducibility of historical experiments.
- A compact draft has less space than DIC3. The paper contains the central contracts and findings; supporting provenance remains in the accompanying package.
- OpenSpec validation checks document structure. It does not prove traffic-control behavior, model superiority, hardware correctness, or online publication.
- Pending task integration remains in `integrate-task-workflow`; completing the paper must not check off those implementation tasks.

## Migration Plan

Read the retained material; prepare and verify the manuscript and references; audit available result arithmetic; validate the OpenSpec tree; compile and inspect the PDF; package source and delivery instructions; then record Overleaf/GitHub publication only if the actual operation succeeds. Keep this change active while required online actions remain pending.

## Open Questions

The assignment screenshot specifies neither page count nor language, target conference, exact MCP server, nor upload format. The chosen English IEEE draft and supporting source package are reasoned defaults. Any later classroom instruction can refine those choices without rewriting the underlying evidence.
