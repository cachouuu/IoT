## ADDED Requirements

### Requirement: REP-01 Unified task report
The report SHALL link the request, qualified source, decisions, execution states and limitations by task_id and preserve all rejected and failed outcomes.

#### Scenario: Task ends
- **WHEN** a task completes, is rejected, or times out
- **THEN** one report records the outcome and available evidence, with missing evidence explicitly identified.

### Requirement: REP-02 Qualified comparison
The report SHALL apply the paired-evaluation contract and distinguish existing stored results, new measurements, and planned acceptance tests.

#### Scenario: Stored experiment
- **WHEN** historical results are included
- **THEN** the report labels them as existing evidence and does not claim the current documentation run executed them.

#### Scenario: Regression or residual queue
- **WHEN** a model case regresses or leaves unserved vehicles
- **THEN** the report retains the regression and per-axis residual queue alongside throughput and waiting time.
