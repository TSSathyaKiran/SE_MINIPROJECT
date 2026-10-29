# Tests

- `test_<module>.py`: pytest unit and API tests, one file per module. Run with `pytest`; CI runs them on every PR. Name tests after the test case, e.g. `test_tc_stu_01_admin_creates_student`.
- `conftest.py`: shared fixtures (`client`, `login_as`, `add_user`).
- `ui/`: Selenium flows (run by hand).
- `performance/`: JMeter plans (TC-Perf-01, TC-Perf-02).
- `postman/`: Postman collection for API and RBAC checks.

Test case specifications: `docs/Test_Plan/Test_Cases.md`.
