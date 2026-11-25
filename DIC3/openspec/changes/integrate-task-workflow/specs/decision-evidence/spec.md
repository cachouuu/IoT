## ADDED Requirements

### Requirement: DEC-01 Decision provenance
Each decision SHALL record task_id, observation index, four causal features, policy, plan_id, model identity and model-or-rule source.

#### Scenario: Model decision
- **WHEN** an in-domain tree decision is made
- **THEN** the record includes the actual features and model identifier, without inventing cost optimality.

#### Scenario: Fallback decision
- **WHEN** the existing firmware chooses reference-rule fallback
- **THEN** the record states the triggering domain condition and counts it as fallback.

### Requirement: DEC-02 Faithful explanations
The report SHALL distinguish observed features and actual decision source from any future verified tree-path explanation.

#### Scenario: Path unavailable
- **WHEN** the implementation has not recorded the actual tree traversal
- **THEN** the explanation states that the path is unavailable and does not invent branch conditions.
