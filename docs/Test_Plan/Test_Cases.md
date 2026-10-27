# Test Case Specifications: Student Record System

One test case per SRS requirement (33 requirements, 33 test cases). The same content appears in Appendix A of the Test Plan.

## TC-Auth-01: Login with valid and invalid credentials

- **Requirement:** SRS-F-001
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Open the login page.
  2. Enter a registered username/email and the correct password; submit.
  3. Repeat with a wrong password, and with an unregistered username.
- **Expected result:** Valid credentials create a session and open the role's dashboard. Invalid attempts show an error message and create no session.
- **Status:** Not tested

## TC-Auth-02: Role-based access for each role

- **Requirement:** SRS-F-002
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Log in as Student, Faculty, Admin (and Parent/Guardian if enabled) in turn.
  2. For each role, try every menu function and also open other roles' pages by direct URL.
- **Expected result:** Each role can use only its permitted functions; all other pages/actions are denied.
- **Status:** Not tested

## TC-Auth-03: Account lockout after 5 failed logins

- **Requirement:** SRS-F-003
- **Priority:** Medium
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Enter a wrong password 5 times for one account.
  2. On the 6th attempt, enter the correct password.
  3. Check the audit log.
- **Expected result:** 6th attempt is blocked with a locked-account message, and a lockout event is recorded in the audit log.
- **Status:** Not tested

## TC-Stu-01: Admin creates a student record

- **Requirement:** SRS-F-010
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. As Admin, create a student with all mandatory personal and academic-program fields.
  2. Try again with one mandatory field missing.
  3. Try again with a duplicate Student ID.
- **Expected result:** Valid record is saved with a unique Student ID. Missing-field and duplicate submissions are rejected with clear validation messages.
- **Status:** Not tested

## TC-Stu-02: Update and deactivate a student record

- **Requirement:** SRS-F-011
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. As Admin, update a student's details.
  2. Deactivate a student who has enrollment and grade history.
  3. Try to log in as the deactivated student.
  4. View the student's historical academic data as Admin.
- **Expected result:** Update is saved. Deactivated student cannot log in, and all historical data is preserved (soft delete / status flag).
- **Status:** Not tested

## TC-Stu-03: Student edits only whitelisted profile fields

- **Requirement:** SRS-F-012
- **Priority:** Medium
- **Type / Method:** Functional / Security / Automated
- **Steps:**
  1. As Student, edit phone and address; save.
  2. Try to edit name, program, and Student ID in the UI.
  3. Send a tampered request that includes a locked field.
- **Expected result:** Phone and address are saved. Core academic fields are locked in the UI and rejected server-side.
- **Status:** Not tested

## TC-Stu-04: Search students by ID or name

- **Requirement:** SRS-F-013
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. As Faculty/Admin, search by full Student ID, by partial name, and by a non-existent value.
  2. As Student, try to search other students.
- **Expected result:** Matching records are displayed; 'no results' is shown for no match; Student role cannot search other students.
- **Status:** Not tested

## TC-Enr-01: Create courses, sections, and terms

- **Requirement:** SRS-F-020
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. As Admin, create an academic term, a course, and a section for that term.
  2. Open the section list as a Student.
  3. Try to create a course with an existing course code.
- **Expected result:** Course and section appear under the correct term. Duplicate course code is rejected.
- **Status:** Not tested

## TC-Enr-02: Enrollment rules: seats and prerequisites

- **Requirement:** SRS-F-021
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Enroll a student in a section with free seats and prerequisites met.
  2. Attempt enrollment in a full section.
  3. Attempt enrollment with an unmet prerequisite.
  4. Attempt to enroll in the same section twice.
- **Expected result:** Only the first attempt succeeds. Full section, unmet prerequisite, and duplicate enrollment are rejected with an explanation.
- **Status:** Not tested

## TC-Enr-03: Course drop within add/drop period

- **Requirement:** SRS-F-022
- **Priority:** Medium
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Drop an enrolled course before the configured deadline.
  2. Set the system date (or deadline) so the period has ended; try to drop another course.
- **Expected result:** Drop before deadline succeeds and the seat is freed. Drop after the deadline is rejected.
- **Status:** Not tested

## TC-Att-01: Faculty marks attendance

- **Requirement:** SRS-F-030
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. As Faculty, open a session for an assigned section and date.
  2. Mark students Present, Absent, and Late; save.
  3. Check that non-enrolled students are not listed.
  4. Try to open a section assigned to another faculty.
- **Expected result:** Attendance is saved against the correct date and section for each enrolled student. Other faculty's sections are not accessible.
- **Status:** Not tested

## TC-Att-02: Student views attendance percentage

- **Requirement:** SRS-F-031
- **Priority:** Medium
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Seed a section with 10 sessions: 8 Present, 2 Absent for one student.
  2. Log in as that student and open attendance.
  3. Compare with the attendance table.
- **Expected result:** Displayed percentage (80%) matches the stored session records. (Treatment of 'Late' in the percentage to be confirmed; see Assumptions.)
- **Status:** Not tested

## TC-Grd-01: Marks entry before and after grade-lock date

- **Requirement:** SRS-F-040
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. As Faculty, enter and then update scores before the lock date.
  2. Enter a score above the assessment's maximum marks.
  3. After the lock date, try to edit a score.
- **Expected result:** Scores save and update before lock. Over-maximum score is rejected. After lock, scores are read-only.
- **Status:** Not tested

## TC-Grd-02: GPA and CGPA calculation

- **Requirement:** SRS-F-041
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Use the sample 10-point grading scale and this term: 4 credits @ 9, 3 credits @ 8, 4 credits @ 10, 3 credits @ 7.
  2. Finalise grades.
  3. Add a second term and check CGPA.
- **Expected result:** Term GPA = 121 / 14 = 8.64. CGPA equals the credit-weighted average across both terms and matches the hand-calculated value.
- **Status:** Not tested

## TC-Grd-03: Grade-posted notification

- **Requirement:** SRS-F-042
- **Priority:** Medium
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Confirm no notification exists before finalisation.
  2. Finalise grades for a section.
  3. Log in as an affected student.
- **Expected result:** An in-app notification is recorded for each affected student only after finalisation.
- **Status:** Not tested

## TC-Rep-01: Unofficial transcript PDF

- **Requirement:** SRS-F-050
- **Priority:** High
- **Type / Method:** Functional / Manual + Automated
- **Steps:**
  1. As Student with two completed terms and one in-progress term, generate the transcript.
  2. Open the PDF and compare against stored records.
  3. Try to fetch another student's transcript by changing the ID in the URL.
- **Expected result:** PDF lists all completed terms, subjects, grades, GPA/CGPA correctly. Another student's transcript is denied.
- **Status:** Not tested

## TC-Rep-02: Official report card

- **Requirement:** SRS-F-051
- **Priority:** Medium
- **Type / Method:** Functional / Manual + Automated
- **Steps:**
  1. As Admin, select a student and term; generate the report card.
  2. Try the same as Student and as Faculty.
- **Expected result:** Report card contains institution details, student details, and term grades. Non-Admin roles cannot generate it.
- **Status:** Not tested

## TC-Fee-01: Fee balance and payment-status history

- **Requirement:** SRS-F-060
- **Priority:** Medium
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Seed fee records for a student (amount due, amount paid, status).
  2. Log in as that student and open the fee page.
  3. Look for any edit or pay controls.
- **Expected result:** Displayed balance and history match stored records. Page is read-only with no payment processing.
- **Status:** Not tested

## TC-Fee-02: Enrollment restriction for overdue fees

- **Requirement:** SRS-F-061
- **Priority:** Medium
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Configure an overdue threshold as Admin.
  2. Give a student an overdue balance above the threshold; try to enroll.
  3. Reduce the balance below the threshold; try again.
  4. Change the threshold as Admin and retry.
- **Expected result:** Enrollment is blocked with an explanation above the threshold, allowed below it, and a changed threshold takes effect.
- **Status:** Not tested

## TC-Adm-01: Academic configuration is applied

- **Requirement:** SRS-F-070
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. As Admin, set a new grading scale, a term, and an add/drop deadline.
  2. Run a GPA calculation and a drop attempt around the new deadline.
- **Expected result:** New configuration is used by the affected transactions (GPA uses new scale; drop follows new deadline).
- **Status:** Not tested

## TC-Adm-02: Audit log entries for mutations

- **Requirement:** SRS-F-071
- **Priority:** High
- **Type / Method:** Functional / Automated
- **Steps:**
  1. Perform create, update, deactivate, grade change, and attendance change actions.
  2. View the audit log as Admin.
- **Expected result:** Each action has an entry with actor, timestamp, action, and record ID.
- **Status:** Not tested

## TC-Perf-01: Response time under normal load

- **Requirement:** SRS-NF-001
- **Priority:** High
- **Type / Method:** Performance / Automated (JMeter)
- **Steps:**
  1. Configure 100 virtual users (assumed 'normal load') running login, page load, and student search for 10 minutes.
  2. Collect response-time statistics.
- **Expected result:** 90th percentile response time is 3 seconds or less.
- **Status:** Not tested

## TC-Perf-02: 1,000 concurrent users

- **Requirement:** SRS-NF-006
- **Priority:** Medium
- **Type / Method:** Performance / Automated (JMeter)
- **Steps:**
  1. Ramp up to 1,000 concurrent virtual users and hold for 10 minutes on key operations.
  2. Monitor response time, error rate, and server resources.
- **Expected result:** Key operations stay within 3 seconds for the target load, with an error rate of 1% or less (test-plan threshold).
- **Status:** Not tested

## TC-Ops-01: Availability monitoring

- **Requirement:** SRS-NF-002
- **Priority:** High
- **Type / Method:** Reliability / Automated
- **Steps:**
  1. Run a health-check script every minute against the deployed instance for the observation window.
  2. Exclude declared maintenance periods; calculate availability.
- **Expected result:** Measured availability is at least 99.5% for the observation window.
- **Status:** Not tested

## TC-Ops-02: Record and audit-log retention

- **Requirement:** SRS-NF-004
- **Priority:** High
- **Type / Method:** Reliability / Manual
- **Steps:**
  1. Take a database backup and archive the audit log.
  2. Restore into a clean environment and retrieve old records and log entries.
  3. Review any purge/cleanup job configuration.
- **Expected result:** Archived data can be restored and retrieved. No job removes academic or audit records younger than 7 years.
- **Status:** Not tested

## TC-Sec-01: PII protection checklist

- **Requirement:** SRS-NF-003
- **Priority:** High
- **Type / Method:** Security / Manual
- **Steps:**
  1. Run the security checklist covering encryption in transit and at rest, RBAC, and log content.
  2. Search logs, URLs, and error messages for PII.
- **Expected result:** All checklist items pass; no PII appears in logs, URLs, or error messages.
- **Status:** Not tested

## TC-Sec-02: TLS 1.2+ enforced

- **Requirement:** SRS-SR-001
- **Priority:** High
- **Type / Method:** Security / Automated (testssl.sh / sslyze)
- **Steps:**
  1. Scan the deployed HTTPS endpoint.
  2. Attempt connections using TLS 1.0 and 1.1.
- **Expected result:** TLS 1.0/1.1 connections are refused; TLS 1.2+ is accepted. (Localhost demo is exempt.)
- **Status:** Not tested

## TC-Sec-03: RBAC enforced at the API layer

- **Requirement:** SRS-SR-002
- **Priority:** High
- **Type / Method:** Security / Automated (Postman)
- **Steps:**
  1. Call Admin and Faculty API endpoints with a Student token.
  2. Request another student's records with a Student token.
  3. Call endpoints with no token.
- **Expected result:** Unauthorised calls return 403 (or 401 without token). No data is returned.
- **Status:** Not tested

## TC-Sec-04: Password hashing

- **Requirement:** SRS-SR-003
- **Priority:** High
- **Type / Method:** Security / Manual
- **Steps:**
  1. Create two users with the same password.
  2. Inspect the users table in the database.
- **Expected result:** Only salted bcrypt/Argon2 hashes are stored; no plaintext; the two hashes differ.
- **Status:** Not tested

## TC-Sec-05: PII encrypted at rest

- **Requirement:** SRS-SR-004
- **Priority:** High
- **Type / Method:** Security / Manual
- **Steps:**
  1. Identify sensitive PII fields.
  2. Inspect the raw database files/backup and the database encryption configuration.
- **Expected result:** Sensitive PII is encrypted at field level or covered by database/storage encryption; not readable in a raw dump.
- **Status:** Not tested

## TC-Sec-06: Session timeout after 15 minutes

- **Requirement:** SRS-SR-005
- **Priority:** Medium
- **Type / Method:** Security / Automated
- **Steps:**
  1. Log in and stay idle for 15 minutes (or use a test hook to advance the clock).
  2. Perform any action; also replay the old session token against the API.
  3. Repeat with activity at 14 minutes.
- **Expected result:** After 15 idle minutes the session is invalid and re-authentication is required. Activity within the window keeps the session alive.
- **Status:** Not tested

## TC-Sec-07: Audit log is tamper-protected

- **Requirement:** SRS-SR-006
- **Priority:** High
- **Type / Method:** Security / Manual + Automated
- **Steps:**
  1. Try to edit or delete audit records from the UI, the API, and with the application's database account.
- **Expected result:** All attempts are denied; audit records remain unchanged.
- **Status:** Not tested

## TC-UX-01: WCAG 2.1 AA accessibility

- **Requirement:** SRS-NF-005
- **Priority:** Medium
- **Type / Method:** Usability / Manual + Automated (axe / Lighthouse)
- **Steps:**
  1. Run axe/Lighthouse on the login page and each dashboard.
  2. Navigate key flows using only the keyboard.
  3. Check contrast, form labels, and error messages.
- **Expected result:** No critical WCAG 2.1 AA violations; key flows are fully keyboard-operable.
- **Status:** Not tested

