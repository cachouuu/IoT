## 1 Task intake and data
- [ ] 1.1 Implement the required request fields and enumerated modes/policies.
- [ ] 1.2 Validate dataset hashes, units, timestamps, coverage and axis pairing.
- [ ] 1.3 Reject missing intervals and unsupported capacity without synthetic repair.
## 2 Existing decision integration
- [ ] 2.1 Connect the existing FIFO/causal feature engine without future-input access.
- [ ] 2.2 Record actual model identity, features, plan and firmware fallback source.
- [ ] 2.3 Ensure review mode issues no device writes.
## 3 Execution and reporting
- [ ] 3.1 Verify available command-correlation and device-health fields before integration.
- [ ] 3.2 Implement submission guards and submitted/applied/timeout/mismatch states.
- [ ] 3.3 Link outcomes and limitations into one task report.
## 4 Acceptance
- [ ] 4.1 Run AT01-AT12 from the report against the new integration.
- [ ] 4.2 Revalidate causal windows, fixed metric horizons, zero denominators and regressions.
- [ ] 4.3 Perform necessary board readback checks and retain logs before claiming execution success.
