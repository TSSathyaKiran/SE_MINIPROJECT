# Tests

- `test_<module>.py`: pytest unit and API tests, one file per module. Run with `pytest`; CI runs them on every PR. Name tests after the test case, e.g. `test_tc_stu_01_admin_creates_student`.
- `conftest.py`: shared fixtures (`client`, `login_as`, `add_user`).
- `test_system.py`: system test. Starts the app on a local port with the demo data from `src/seed.py` and runs one pass through the SRS 7.3 acceptance suites over real HTTP. CI runs it too.
- `ui/`: Selenium flows in headless Chrome: `test_login_flow.py`, and `test_keyboard_flows.py` (TC-UX-01, key flows with the keyboard only). CI runs them in its `ui` job; locally they need `pip install selenium` and Chrome, and `pytest` skips them without Selenium.
- `test_headers.py`: security headers and the CSP rules every template must follow.
- `performance/`: JMeter plans (TC-Perf-01, TC-Perf-02).
- `postman/`: Postman collection for API and RBAC checks.

Test case specifications: `docs/Test_Plan/Test_Cases.md`.
