# JIRA-Ready Defect Drafts - SC-1

## Draft Summary

| Metric | Value |
| --- | --- |
| Ticket | SC-1 |
| Runtime Failures | 0 |
| Quality Defects Drafted | 4 |
| Severity Mix | 4 HIGH |

---

## 1) [BUG] SC-1 Automation Does Not Enforce AC-10 Performance SLA (2s)

### Description
- Feature: SC-1 Shopper UI scenarios (AC-10)
- Failed Scenario: Performance conformance validation for catalog/core desktop flows
- Actual Result: Automation assertion allows page load/performance threshold up to 10.0 seconds.
- Expected Result: Automation must enforce AC-10 threshold of 2.0 seconds maximum.
- Root Cause Analysis: Assertion logic in test suite uses non-conformant threshold (code review finding R-02).
- Defect Type: Automation Script Issue

### Severity / Priority
- Severity: HIGH
- Priority: P1
- Justification: Can produce false PASS for performance regressions violating acceptance criteria.

### Environment
- OS: Windows 11
- Python: 3.13.0
- pytest: 9.1.0
- Playwright: Chromium headless

### Test Data Used
- Source: `artifacts/test/SC-1/testdata/sc_1_data.json`

### Attachments / References
- `artifacts/verify/SC-1-verification-report.md`
- `artifacts/code-review/SC-1-code-review.md`
- `artifacts/test/SC-1/EXECUTION_SUMMARY_SC-1.md`
- `artifacts/test/SC-1/logs/execution_SC-1.log`

---

## 2) [BUG] SC-1 Catalog Validation Is Visibility-Only and Misses Content Quality Checks

### Description
- Feature: SC-1 Catalog details validation (AC-04)
- Failed Scenario: Catalog item content validation depth in SC1-TC-005
- Actual Result: Automation primarily verifies visibility; content-depth checks are insufficient for robust validation.
- Expected Result: Automation must assert meaningful content (for example non-empty title/description and valid price format) to ensure AC-04 conformance.
- Root Cause Analysis: Assertion strategy is shallow (code review finding A-01), allowing content regressions to pass.
- Defect Type: Automation Script Issue

### Severity / Priority
- Severity: HIGH
- Priority: P1
- Justification: Business-critical product content defects can escape despite green execution.

### Environment
- OS: Windows 11
- Python: 3.13.0
- pytest: 9.1.0
- Playwright: Chromium headless

### Test Data Used
- Source: `artifacts/test/SC-1/testdata/sc_1_data.json`

### Attachments / References
- `artifacts/verify/SC-1-verification-report.md`
- `artifacts/code-review/SC-1-code-review.md`
- `artifacts/test/SC-1/EXECUTION_SUMMARY_SC-1.md`

---

## 3) [BUG] Hardcoded Credential Fallbacks Present in SC-1 Automation Utilities

### Description
- Feature: SC-1 automation framework security/compliance
- Failed Scenario: Secure credential handling in test framework
- Actual Result: Credential literals are available as fallback values in automation utility code.
- Expected Result: Credentials must come only from secure runtime configuration (environment or secret manager), with no hardcoded fallback secrets.
- Root Cause Analysis: Test data utility includes embedded fallback credentials (code review finding B-01).
- Defect Type: Automation Script Issue

### Severity / Priority
- Severity: HIGH
- Priority: P1
- Justification: Security/compliance risk; likely to trigger enterprise secret scanning and policy violations.

### Environment
- OS: Windows 11
- Python: 3.13.0
- pytest: 9.1.0
- Playwright: Chromium headless

### Test Data Used
- Source: `artifacts/test/SC-1/testdata/sc_1_data.json`

### Attachments / References
- `artifacts/code-review/SC-1-code-review.md`
- `artifacts/verify/SC-1-verification-report.md`

---

## 4) [BUG] SC-1 Release Gate Blocked by Unresolved HIGH Automation Code Review Findings

### Description
- Feature: SC-1 automation quality gate governance
- Failed Scenario: Promotion of SC-1 suite to authoritative regression gate
- Actual Result: HIGH findings remain open (including locator ambiguity, deprecated wait strategy, missing logging), but execution pass alone may be interpreted as release-ready.
- Expected Result: All HIGH review findings must be resolved and re-reviewed before release gate promotion.
- Root Cause Analysis: Quality-gate controls are not yet fully enforced against open HIGH findings (verification verdict remains CONDITIONAL).
- Defect Type: Automation Script Issue

### Severity / Priority
- Severity: HIGH
- Priority: P1
- Justification: Reliability and diagnosability risks remain unmitigated; governance non-compliance.

### Environment
- OS: Windows 11
- Python: 3.13.0
- pytest: 9.1.0
- Playwright: Chromium headless

### Test Data Used
- Source: `artifacts/test/SC-1/testdata/sc_1_data.json`

### Attachments / References
- `artifacts/code-review/SC-1-code-review.md`
- `artifacts/verify/SC-1-verification-report.md`
- `artifacts/test/SC-1/DEFECT_ANALYSIS_SC-1.md`

---

## Rerun Guidance (Post-Fix)

1. Targeted rerun for AC-04 and AC-10-related tests after assertion and SLA fixes.
2. Security sanity rerun after credential handling remediation.
3. Full SC-1 regression rerun after all HIGH findings are closed and re-reviewed.
