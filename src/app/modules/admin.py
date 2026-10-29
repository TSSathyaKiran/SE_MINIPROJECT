"""Academic settings (Tanuj): issue #6. Details in docs/TEAM_GUIDE.md.

  GET /admin/config           admin   all settings (see core/settings.py)
  PUT /admin/config           admin   {gradingScale?, addDropDeadline?, gradeLockDate?, feeThreshold?}  400 invalid
  GET /ui/admin/config        admin page
"""
from flask import Blueprint

bp = Blueprint("admin", __name__)
