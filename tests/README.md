# Tests

Place test scripts here, named after the test case IDs in `docs/Test_Plan/Test_Cases.md`.

Suggested layout:

```
tests/
├── unit/          pytest: GPA/CGPA, attendance %, lockout, validation
├── api/           pytest + Postman collection: RBAC, security, integration
├── ui/            Selenium: end-to-end flows per role
├── performance/   JMeter plans (TC-Perf-01, TC-Perf-02)
├── security/      ZAP / TLS scan configs and reports
└── data/          SQL seed scripts and CSV test data
```
