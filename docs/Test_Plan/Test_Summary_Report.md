# Test Summary Report (interim)

Date: 2026-11-10 · Prepared by: Tanuj (QA Lead) · Issue: #10 · Branch: `feature/10-tls-and-final`

This is the **interim** report. The final full-project regression runs after the remaining
team work (#15 performance, accessibility and UI tests) is merged; this report will be
updated then.

## 1. What was tested

- Full automated suite on `feature/10-tls-and-final` (includes the new TLS tests):
  **245 tests, all passing** (`pytest`, SQLite in-memory, ~8 s).
- HTTPS mode: real server run with a self-signed certificate; TLS handshake checks below.
- Security scans: `testssl.sh` and an OWASP ZAP baseline scan; details in
  `docs/security/TLS_ZAP_SCAN.md`.

## 2. Test case status

33 test cases in `docs/Test_Plan/Test_Cases.md`:

| Status | Count | Which |
| --- | --- | --- |
| Passed | 5 | TC-Ops-01, TC-Ops-02, TC-Sec-01, TC-Sec-02, TC-Sec-05 |
| Not tested | 28 | see Test_Cases.md |

Newly passed in this round:

- **TC-Sec-02 (TLS 1.2+ enforced): Passed (2026-11-10).** testssl.sh: TLS 1.0 and 1.1 not
  offered, TLS 1.2 and 1.3 offered. `tests/test_tls.py` adds 4 automated checks (TLS 1.2
  minimum, TLS 1.1 refused, TLS 1.2 accepted, debug default).
- **TC-Sec-01 (PII protection checklist): Passed (2026-11-10).** All 12 checklist items now
  pass: items 1 (encryption in transit) and 12 (debug mode off) were closed by #10.

The other 28 cases keep their current status. Executing every case is part of the final
regression after #15 merges.

## 3. Requirement coverage (RTM)

`SRS-SR-001` (TLS 1.2+ mandatory) moved from N to **P**. Other rows are unchanged.

## 4. Open items

1. **#15 not merged** - final full regression and this report's final version wait for it.
2. **ZAP findings, not fixed:** missing CSP, anti-clickjacking, HSTS and
   X-Content-Type-Options headers; missing Subresource Integrity; `Server` version header
   exposed. See `docs/security/TLS_ZAP_SCAN.md`.
3. **testssl LUCKY13 note:** CBC ciphers offered (potentially vulnerable, experimental
   check). Cipher hardening not done here.
4. **ZAP scope:** unauthenticated scan of the public login surface only.
5. **Demo video links:** to be added by the team (placeholders below).

## 5. Demo videos

- Feature demo: _link to be added by the team_
- Test run demo: _link to be added by the team_

## 6. Deviations

See `docs/DEVIATIONS.md`; dates and PRs filled in this round.
