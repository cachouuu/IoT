## ADDED Requirements

### Requirement: DATA-01 Source qualification
The task layer SHALL verify source identity, hash, units, timestamps, observation coverage, quality and paired-axis evidence before permitting a control experiment.

#### Scenario: Single official snapshot
- **WHEN** only a one-minute official snapshot is available for a 600-second task
- **THEN** the system reports insufficient_coverage and does not repeat the snapshot.

#### Scenario: Unknown axis pairing
- **WHEN** the NS/EW relationship lacks evidence
- **THEN** the system reports unverified_pairing and does not invent a pairing.

#### Scenario: Hash mismatch
- **WHEN** the actual dataset hash differs from the manifest
- **THEN** the system rejects the data with hash_mismatch.

### Requirement: DATA-02 Missingness and capacity
The task layer SHALL preserve missingness and reject unsupported units or arrival capacity; the existing per-axis per-second interface SHALL accept only zero or one.

#### Scenario: Missing interval
- **WHEN** a required interval is absent
- **THEN** the system reports the gap and does not zero-fill it.

#### Scenario: Unsupported arrivals
- **WHEN** a per-axis per-second input exceeds one or has unknown units
- **THEN** the system rejects control use and does not silently rescale the value.

### Requirement: DATA-03 Explicit derived data
The task layer SHALL label reconstructed second-level data as derived and retain its method and source; it SHALL NOT call minute-level observations measured per-second arrivals.

#### Scenario: Reconstructed series
- **WHEN** an explicitly prepared minute-to-second derivation is provided
- **THEN** the report preserves the derivation and does not claim per-second field measurements.
