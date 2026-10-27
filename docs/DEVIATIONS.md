# Deviations from SRS / SAD / Test Plan

Write one line per change, with the date and the PR. Explain these at the final demo.

| Date | What | Doc + section | Why | PR |
| --- | --- | --- | --- | --- |
| | 'Late' does not count as present in attendance % (assumption from SAD 4.6, confirm with team) | SRS-F-031 / SAD 4.6 | Open issue in SAD | |
| | UI pages served under `/ui/...`; API keeps the exact SAD paths | SAD 4.3 | Avoid route clashes between HTML pages and JSON API | |
| | pytest/CI run on SQLite in-memory; MySQL used for the demo | Test Plan 6 | CI needs no database server | |
| 2026-10-27 | Jira replaced by GitHub Issues + Projects board + milestones | Process / Test Plan (defect tracking) | Mentor said Jira isn't required; keeps code, issues and PRs in one place | |
