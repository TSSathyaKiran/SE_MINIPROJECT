# TC-Perf-01 — 100 Concurrent Users

## Test configuration
- Concurrent users: 100
- Ramp-up: 20 seconds
- Iterations per user: 1
- Workflow: faculty login, faculty dashboard, student search

## Results
- Total samples: 300
- Failed samples: 0
- Error percentage: 0.00%

| Request | Samples | Average (ms) | P90 (ms) | Min (ms) | Max (ms) | Errors |
|---|---:|---:|---:|---:|---:|---:|
| 01 - Faculty Login | 100 | 679.8 | 705 | 632 | 721 | 0 |
| 02 - Faculty Dashboard | 100 | 22.0 | 24 | 18 | 39 | 0 |
| 03 - Search Students | 100 | 23.5 | 26 | 19 | 31 | 0 |
