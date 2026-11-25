## ADDED Requirements

### Requirement: TASK-01 Structured requests
The task layer SHALL require task_id, dataset_id, dataset_sha256, mode, policy, objective, observation_count and manifest_path; mode SHALL be review or execute and objective SHALL be queue_vehicle_seconds.

#### Scenario: Missing fields
- **WHEN** any required field is missing
- **THEN** the request is rejected with missing_fields and no device write is issued.

#### Scenario: Unsupported mode
- **WHEN** mode is neither review nor execute
- **THEN** the request is rejected with unsupported_mode.

### Requirement: TASK-02 Read-only review
The task layer SHALL produce recommendations without device writes when mode is review.

#### Scenario: Review a valid dataset
- **WHEN** a qualified request uses review mode
- **THEN** the task produces decisions and evidence with zero device writes.
