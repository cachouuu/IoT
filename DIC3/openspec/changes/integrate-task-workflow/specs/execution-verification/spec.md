## ADDED Requirements

### Requirement: EXEC-01 Submission guard
Execution SHALL reject illegal plans, invalid device state or expired submission deadlines before issuing a command.

#### Scenario: Invalid plan
- **WHEN** plan_id is not zero, one or two
- **THEN** execution records invalid_plan and issues no command.

#### Scenario: Expired decision
- **WHEN** the intended submission deadline has passed
- **THEN** execution records expired and does not relabel a later application as on-time.

### Requirement: EXEC-02 Application evidence
Execution SHALL confirm applied only when active_plan and the expected cycle match the submitted command record; receipt alone SHALL NOT count as application.

#### Scenario: Receipt only
- **WHEN** the command has been acknowledged but the expected cycle has not been observed
- **THEN** status remains submitted.

#### Scenario: Matching readback
- **WHEN** the expected cycle is observed with matching active_plan and command correlation
- **THEN** status becomes applied and the evidence is retained.

#### Scenario: Wrong plan
- **WHEN** readback at the expected cycle shows a different active_plan
- **THEN** status becomes mismatch and both submission and readback are preserved.

#### Scenario: Readback timeout
- **WHEN** confirmation does not arrive within the configured deadline
- **THEN** status becomes timeout without a success claim.
