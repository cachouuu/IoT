## ADDED Requirements

### Requirement: DOC-01 Assignment coverage
The submission SHALL contain A-F, five cores, three trade-offs, ten details, refactored Introduction and Related Work, design-to-spec traceability, and actual CLI validation evidence.

#### Scenario: Review assignment package
- **WHEN** a reviewer opens the submission
- **THEN** all five assignment requirements map to concrete files through the README and traceability table.

### Requirement: DOC-02 Evidence boundaries
The report SHALL distinguish existing observations from planned work and keep literature findings separate from prototype outcomes.

#### Scenario: Inspect outcome claims
- **WHEN** a reviewer reads performance numbers
- **THEN** the input type, metric, evidence batch and limitations are stated, including regressions.

### Requirement: DOC-03 Reproducible specification package
The package SHALL pin the CLI version, retain source hashes and provide a validation entry point.

#### Scenario: Revalidate package
- **WHEN** OpenSpec 2.0.0 is installed
- **THEN** the documented command validates main specifications and active changes without requiring hardware access.
