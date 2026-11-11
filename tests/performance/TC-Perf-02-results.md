# TC-Perf-02 — 1,000 Concurrent Users

## Configuration
- Concurrent users: 1,000
- Ramp-up: 100 seconds
- Iterations per user: 1
- Workflow: faculty login, faculty dashboard, student search

## Overall results
- Total samples: 3000
- Failed samples: 0
- Error percentage: 0.00%

| Request | Samples | Average (ms) | P90 (ms) | Min (ms) | Max (ms) | Errors |
|---|---:|---:|---:|---:|---:|---:|
| 01 - Faculty Login | 1000 | 640.8 | 661 | 549 | 856 | 0 |
| 02 - Faculty Dashboard | 1000 | 21.8 | 23 | 15 | 171 | 0 |
| 03 - Search Students | 1000 | 23.2 | 25 | 17 | 94 | 0 |
