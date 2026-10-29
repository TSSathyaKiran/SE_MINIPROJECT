"""Academic settings (Tanuj): issue #6. Details in docs/TEAM_GUIDE.md.

  GET /admin/config           admin   all settings (see core/settings.py)
  PUT /admin/config           admin   {gradingScale?, addDropDeadline?, gradeLockDate?, feeThreshold?}  400 invalid
  GET /ui/admin/config        admin page
"""
from flask import Blueprint, jsonify

from ..core.security import require_role
from ..core.settings import get_setting

bp = Blueprint("admin", __name__)


def _config_json():
    return jsonify(
        gradingScale=get_setting("grading_scale"),
        addDropDeadline=get_setting("add_drop_deadline"),
        gradeLockDate=get_setting("grade_lock_date"),
        feeThreshold=get_setting("fee_threshold"),
    )


@bp.get("/admin/config")
@require_role("admin")
def get_config():
    return _config_json()
