## ADDED Requirements

### Requirement: PAPER-01 Conference manuscript coverage
The DIC4 submission SHALL provide a substantive IEEE conference-style draft describing the actual Traffic Timing Assistant scope, relevant prior work, architecture, timing behavior, evaluation evidence, limitations, and references.

#### Scenario: Review manuscript content
- **WHEN** a reviewer opens the compiled draft
- **THEN** the manuscript explains the four causal features, three legal timing plans, firmware rule fallback, cycle-boundary application, and the distinction between existing core components and pending integration.

#### Scenario: Unimplemented integration
- **WHEN** a diagram or paragraph describes the unified task and evidence workflow
- **THEN** components without implementation evidence are identified as proposed or pending.

### Requirement: PAPER-02 Result provenance and arithmetic
Every quantitative prototype claim SHALL identify its source record and experiment batch, distinguish stored results from current checks, and preserve available regressions and metric definitions.

#### Scenario: Recompute an archived summary
- **WHEN** current tooling recomputes totals or percentages from retained records
- **THEN** the outcome is labeled an arithmetic audit of historical records and is not described as a new traffic, hardware, or simulator experiment.

#### Scenario: Historical batches differ
- **WHEN** results from the 18-pair host batch, separate 6-pair batch, and board records are reported
- **THEN** each retains its own scope and denominator rather than being pooled into a new combined effect.

#### Scenario: Incomplete original evidence
- **WHEN** a claim lacks the original trace, dataset, complete source, or run environment needed to reproduce it
- **THEN** the limitation is stated and missing observations or successful runs are not fabricated.

### Requirement: PAPER-03 Build and visual verification
The draft SHALL use an IEEE conference LaTeX class, have a documented build entry point, and retain an actually compiled PDF whose latest rendered pages have been checked for layout errors.

#### Scenario: Build the delivered source
- **WHEN** the stated compiler and dependencies are available and the documented build command is run
- **THEN** the source produces the manuscript PDF without unresolved references or fatal compilation errors.

#### Scenario: Rendering defect
- **WHEN** visual review reveals clipped text, overlapping figures, missing glyphs, or illegible tables
- **THEN** the source is corrected and the resulting PDF is re-rendered before delivery.

### Requirement: PAPER-04 Verifiable external references
External technical claims SHALL cite identifiable primary research or official documentation with bibliographic information and stable URLs or identifiers where available.

#### Scenario: Literature result
- **WHEN** the manuscript describes a published method or result
- **THEN** its citation supports that claim and its experimental setting is not presented as this prototype's setting.

#### Scenario: Unsupported reference detail
- **WHEN** an author, year, title, venue, DOI, or quantitative literature claim cannot be verified
- **THEN** the unsupported detail is corrected or omitted rather than completed by guessing.

### Requirement: PAPER-05 Portable source package
The submission SHALL include a complete Overleaf-importable LaTeX bundle and GitHub-ready OpenSpec source with concise instructions, pinned OpenSpec tooling, and current validation evidence.

#### Scenario: Import the source bundle
- **WHEN** the source ZIP is imported into an Overleaf project
- **THEN** its documented main file, bibliography, figures, and required project-local assets are present without dependencies on scratch-workspace absolute paths.

#### Scenario: Revalidate the specifications
- **WHEN** the pinned OpenSpec version is installed and the documented validation entry point is executed
- **THEN** the existing main specifications and active changes are checked, while pending product tasks remain visibly pending.

### Requirement: PAPER-06 MCP workflow record
The submission SHALL describe actual MCP use in preparing the work with tool purpose, outcome, and traceable artifacts, without exposing credentials or inventing calls.

#### Scenario: Tool-assisted source retrieval
- **WHEN** MCP tools retrieve source documents or inspect an available external service
- **THEN** the workflow record states what was retrieved or observed and does not imply an unrelated write operation succeeded.

#### Scenario: Unsupported direct integration
- **WHEN** direct Overleaf editing or GitHub publication was not performed
- **THEN** the record does not claim that such an operation was performed through MCP.

### Requirement: PAPER-07 Truthful publication status
The delivery record SHALL separately track local artifact readiness, Overleaf publication, GitHub publication, and learning-platform submission, and SHALL mark each online action complete only after observing its successful outcome.

#### Scenario: Local package only
- **WHEN** a source ZIP and validated local files exist but there is no verified online project or repository
- **THEN** local readiness is recorded and the corresponding publication action remains pending with the next required step.

#### Scenario: Published project
- **WHEN** a successful online import or repository write is observed
- **THEN** the record includes the resulting verified URL and the actual published content or revision identity where available.

#### Scenario: Pending product integration
- **WHEN** the DIC4 documentation is complete
- **THEN** tasks in `integrate-task-workflow` remain unchecked unless independent implementation and acceptance evidence establishes their completion.
