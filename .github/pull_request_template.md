Closes #<n>

## What changed
- 

## Requirements / test cases covered
- SRS IDs: 
- Test cases: 

## How to test
1. `pytest -q`
2. Run the app, log in as <role>, go to <page>, do <action> → expect <result>

## Checklist
- [ ] Branch name and commits include the issue number
- [ ] Tests added/updated, `pytest -q` passes locally
- [ ] RBAC checked server-side for every new route
- [ ] Mutations call `audit(...)` (once the audit service exists)
- [ ] No passwords / tokens / PII in logs or error messages
- [ ] Any deviation from SRS/SAD noted in `docs/DEVIATIONS.md`
