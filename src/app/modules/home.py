"""Health check, the three role dashboards, and each role's menu."""
from flask import Blueprint, redirect, render_template
from sqlalchemy import text

from ..core.security import current_user, require_login, require_role
from ..extensions import db

bp = Blueprint("home", __name__)

# Every page in the app, per role. A link is shown as "coming soon" until a
# route with exactly that path exists, so you never need to edit this list.
MENU = {
    "admin": [
        ("Students", "/ui/admin/students"),             # 11, 12, 13
        ("Terms", "/ui/admin/terms"),                   # 1 (example)
        ("Courses & sections", "/ui/admin/courses"),    # 16
        ("Academic settings", "/ui/admin/config"),      # 6
        ("Report cards", "/ui/admin/report-cards"),     # 14
        ("Audit log", "/ui/admin/audit"),               # 3
    ],
    "faculty": [
        ("Attendance", "/ui/faculty/attendance"),       # 7
        ("Marks & grades", "/ui/faculty/marks"),        # 18, 19
        ("Student search", "/ui/faculty/search"),       # 13
    ],
    "student": [
        ("My profile", "/ui/student/profile"),          # 12
        ("Courses & enrollment", "/ui/student/courses"),  # 17
        ("Attendance", "/ui/student/attendance"),       # 8
        ("Grades & transcript", "/ui/student/grades"),  # 14, 19
        ("Fees", "/ui/student/fees"),                   # 4
        ("Notifications", "/ui/student/notifications"),  # 19
    ],
}


def register_menu(app):
    @app.context_processor
    def inject_menu():
        user = current_user()
        built = {rule.rule for rule in app.url_map.iter_rules()}
        items = [(label, path, path in built)
                 for label, path in MENU.get(user.role, [])] if user else []
        return {"user": user, "menu": items}


@bp.get("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@bp.get("/")
def index():
    return redirect("/ui/home")


@bp.get("/ui/home")
@require_login
def home():
    return redirect(f"/ui/{current_user().role}")


@bp.get("/ui/admin")
@require_role("admin")
def admin_dashboard():
    return render_template("dashboard.html")


@bp.get("/ui/faculty")
@require_role("faculty")
def faculty_dashboard():
    return render_template("dashboard.html")


@bp.get("/ui/student")
@require_role("student")
def student_dashboard():
    return render_template("dashboard.html")
