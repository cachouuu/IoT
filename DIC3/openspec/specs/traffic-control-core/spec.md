# Traffic control core

## Purpose
Consolidate the existing prototype contract from the original design and firmware; this document does not certify road safety.

## Requirements

### Requirement: CORE-01 Causal features
The core SHALL use current estimated queues and arrival counts from the preceding complete 30-second window; it SHALL NOT use future input records.

#### Scenario: Incomplete first window
- **WHEN** fewer than 30 observations have been consumed
- **THEN** no model decision is made and the initial balanced cycle remains in effect.

#### Scenario: Complete window
- **WHEN** the decision boundary is reached
- **THEN** the four recorded features are computed only from consumed observations.

### Requirement: CORE-02 Finite plans and explicit fallback
The firmware SHALL select plan 0, 1, or 2, mapping to NS/EW green durations 12/12, 16/8, or 8/16 seconds; out-of-domain model inputs SHALL use the existing firmware reference rules.

#### Scenario: Domain boundary
- **WHEN** both queues are at most 120 and both arrival counts at most 30, with nonnegative integer values
- **THEN** the existing tree may infer a plan and its source is recorded as model.

#### Scenario: Outside domain
- **WHEN** a queue is 121 or a 30-second arrival count is 31
- **THEN** the firmware uses reference-rule fallback and increments the fallback count, not the model count.

### Requirement: CORE-03 Deterministic phase execution
The FPGA SHALL retain a 30-second cycle with NS green, NS yellow, all-red, EW green, EW yellow, all-red; a new plan SHALL be latched only at a complete cycle boundary.

#### Scenario: Pending plan during green
- **WHEN** a new legal plan is submitted during a green phase
- **THEN** current phase duration and countdown remain unchanged until the complete cycle boundary.

#### Scenario: Boundary adoption
- **WHEN** a legal pending plan is available at the complete cycle boundary
- **THEN** the FPGA adopts that plan for the new cycle.
