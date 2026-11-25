# Paired evaluation

## Purpose
Specify reproducible comparisons and the limits of existing simplified FIFO evidence.

## Requirements

### Requirement: EVAL-01 Paired conditions
A comparison SHALL match saved input identity, initial conditions, 600-observation horizon, service assumptions and cycle timing between fixed-balanced and tree-with-rules-fallback policies.

#### Scenario: Mismatched inputs
- **WHEN** the two runs have different input hashes
- **THEN** the report rejects a paired performance claim and lists the discrepancy.

#### Scenario: Valid pair
- **WHEN** all comparison conditions match
- **THEN** both raw metrics and the relative change are reported.

### Requirement: EVAL-02 Frozen metric horizon
Metrics SHALL stop after the declared input window; later confirmation of the last submitted plan SHALL NOT add arrivals or change the performance totals.

#### Scenario: Final pending application
- **WHEN** 600 observations are consumed and the twentieth plan awaits confirmation
- **THEN** metrics remain frozen while readback confirmation continues.

### Requirement: EVAL-03 Complete outcome reporting
A report SHALL retain regressions, fallback counts, throughput and residual queues, keep evidence batches separate, and avoid road-effectiveness claims from synthetic results.

#### Scenario: Worse model case
- **WHEN** the model policy has greater queue vehicle-seconds
- **THEN** the case is included with a positive relative change and labeled a regression.

#### Scenario: Zero denominator
- **WHEN** fixed queue vehicle-seconds or the departed-vehicle count is zero
- **THEN** the corresponding percentage or average is marked undefined and the raw counts are retained.
