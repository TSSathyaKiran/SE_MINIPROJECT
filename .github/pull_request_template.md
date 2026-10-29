Closes #<n>

## What changed
- 

## Requirements / test cases covered
- SRS IDs: 
- Test cases: 

## How to test
1. `pytest -q`
2. `python src/seed.py && python src/run.py`, log in as <role> at http://localhost:8000, go to <page>, do <action> → expect <result>

## Checklist
- [ ] Branch name and commits include the issue number
- [ ] Tests added/updated, `pytest -q` passes locally
- [ ] RBAC checked server-side for every new route
- [ ] Every create / update / deactivate / grade / attendance change calls `audit(...)`
- [ ] No passwords / tokens / PII in logs or error messages
- [ ] Any deviation from SRS/SAD noted in `docs/DEVIATIONS.md`
