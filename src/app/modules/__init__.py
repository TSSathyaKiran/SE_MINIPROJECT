from . import (admin, attendance, auditlog, auth, courses, enrollment, fees, grading,
               home, notifications, reports, students)
from .home import register_menu

BLUEPRINTS = [m.bp for m in (admin, attendance, auditlog, auth, courses, enrollment,
                             fees, grading, home, notifications, reports, students)]

__all__ = ["BLUEPRINTS", "register_menu"]
