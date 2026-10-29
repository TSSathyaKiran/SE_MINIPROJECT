"""Every database table (SRS Appendix B plus sessions, terms, prerequisites,
settings and notifications). Tables are created automatically on startup.

If you add a column, delete src/instance/srs.db and run `python src/seed.py`.
"""
from .core import clock
from .extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)          # student | faculty | admin
    status = db.Column(db.String(20), default="active")      # active | inactive
    failed_logins = db.Column(db.Integer, default=0)         # issue #2 (lockout)
    locked_until = db.Column(db.DateTime)                    # issue #2 (lockout)


class AuthSession(db.Model):
    __tablename__ = "sessions"
    token_hash = db.Column(db.String(64), primary_key=True)  # sha256 of the token
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False, default=clock.now)
    user = db.relationship("User")


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_no = db.Column(db.String(20), unique=True, nullable=False)  # e.g. S1001
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)     # PII, encrypted in issue #5
    phone = db.Column(db.String(255))                     # PII, encrypted in issue #5
    address = db.Column(db.String(500))                   # PII, encrypted in issue #5
    program = db.Column(db.String(80), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="active")   # active | inactive (soft delete)
    user = db.relationship("User", backref=db.backref("student", uselist=False))


class Term(db.Model):
    __tablename__ = "terms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)  # e.g. 2026-ODD


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g. CS101
    name = db.Column(db.String(120), nullable=False)
    credits = db.Column(db.Integer, nullable=False)


class Prerequisite(db.Model):
    __tablename__ = "prerequisites"
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), primary_key=True)
    requires_course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), primary_key=True)


class Section(db.Model):
    __tablename__ = "sections"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=False)
    name = db.Column(db.String(10), nullable=False)           # e.g. A
    faculty_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    capacity = db.Column(db.Integer, nullable=False)
    course = db.relationship("Course")
    term = db.relationship("Term")
    faculty = db.relationship("User")
    __table_args__ = (db.UniqueConstraint("course_id", "term_id", "name"),)


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False)
    status = db.Column(db.String(20), default="enrolled")     # enrolled | dropped
    student = db.relationship("Student")
    section = db.relationship("Section")


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)          # present | absent | late
    enrollment = db.relationship("Enrollment")
    __table_args__ = (db.UniqueConstraint("enrollment_id", "date"),)


class Assessment(db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)            # e.g. Midterm
    max_marks = db.Column(db.Float, nullable=False)
    section = db.relationship("Section")


class Mark(db.Model):
    __tablename__ = "marks"
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    __table_args__ = (db.UniqueConstraint("assessment_id", "student_id"),)


class Grade(db.Model):
    __tablename__ = "grades"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False)
    grade = db.Column(db.String(4), nullable=False)            # e.g. A+
    grade_point = db.Column(db.Float, nullable=False)          # e.g. 9
    finalized_at = db.Column(db.DateTime, default=clock.now)
    student = db.relationship("Student")
    section = db.relationship("Section")
    __table_args__ = (db.UniqueConstraint("student_id", "section_id"),)


class Fee(db.Model):
    __tablename__ = "fees"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    description = db.Column(db.String(120), nullable=False)    # e.g. Tuition 2026-ODD
    amount_due = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)          # paid | due | overdue


class Setting(db.Model):
    __tablename__ = "settings"
    key = db.Column(db.String(40), primary_key=True)
    value = db.Column(db.Text, nullable=False)                  # JSON


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # who did it (None = system)
    action = db.Column(db.String(40), nullable=False)           # create | update | deactivate | ...
    record_type = db.Column(db.String(40), nullable=False)      # student | grade | attendance | ...
    record_id = db.Column(db.String(40), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=clock.now)


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=clock.now)
    read = db.Column(db.Boolean, default=False)
