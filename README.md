# Student Record System (SRS-App)

Problem Statement No. 12: a web-based system to manage student profiles, courses, enrollment, attendance, marks, GPA/CGPA, transcripts, fee visibility, and audit logs.

## Team

| USN | Name | Role | GitHub username |
| --- | --- | --- | --- |
| PES2UG24CS553 | Tanuj N | Scrum Master / QA Lead / Repo Owner |  |
| PES2UG24CS547 | T S Sathya Kiran | Test Engineer + Developer (Auth, Audit, Fees) | TSSathyaKiran |
| PES2UG24CS517 | Sri Vaishnavi Peri | Test Engineer + Developer (Students, Reports) |  |
| PES2UG24CS527 | Srujan Yalla | Developer (Courses, Enrollment, Grading) |  |

## How we work

- New here? Read [`docs/TEAM_WORKFLOW.md`](docs/TEAM_WORKFLOW.md) first.
- Backlog: [`docs/BACKLOG.md`](docs/BACKLOG.md), one GitHub Issue per row, tracked on the GitHub Projects board.
- Branch `feature/<n>-name` → small commits `type(module): message (#<n>)` → PR with `Closes #<n>` → review → merge. `scripts/g.sh` does the naming for you.

## Repository structure

```
Student-Record-System/
├── README.md
├── .gitignore
├── docs/
│   ├── SAD/
│   │   └── Student_Record_System_SAD.docx              Architecture & Design Spec
│   ├── SRS/
│   │   └── Student_Record_System_Final_SRS.docx      Software Requirements Specification v1.0
│   ├── Test_Plan/
│   │   ├── Student_Record_System_Test_Plan.docx      Software Test Plan v1.0
│   │   ├── Test_Cases.md                             33 test case specifications
│   │   └── RTM.csv                                   Requirements Traceability Matrix
│   └── GITHUB_SETUP.md                               How to add collaborators and push
├── src/                                              Application source code (Flask + MySQL)
└── tests/                                            Test scripts (pytest, Selenium, Postman, JMeter)
```

## Documents

- **SRS:** `docs/SRS/`
- **Test Plan:** `docs/Test_Plan/Student_Record_System_Test_Plan.docx`
- **Test cases:** `docs/Test_Plan/Test_Cases.md`
- **Traceability:** `docs/Test_Plan/RTM.csv` (every requirement maps to a test case)

## Tech stack (from SRS Appendix A)

HTML, CSS, Bootstrap, JavaScript front end; Python Flask back end; MySQL database; bcrypt/Argon2 for passwords; ReportLab or HTML-to-PDF for reports; localhost deployment for demonstration.

## Testing

Test tools: pytest, Selenium, Postman, Apache JMeter, OWASP ZAP, testssl.sh, axe / Lighthouse. Defects are tracked in GitHub Issues. See the Test Plan for strategy, schedule, and exit criteria.
