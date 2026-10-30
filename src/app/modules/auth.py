"""Login and logout (SRS-F-001), and lockout after 5 failed logins (SRS-F-003)."""
from datetime import timedelta

from flask import Blueprint, current_app, jsonify, render_template, request

from ..core import clock
from ..core.audit import audit
from ..core.errors import ApiError, get_json, required
from ..core.security import (COOKIE, check_password, end_session, request_token,
                             start_session)
from ..extensions import db
from ..models import User

bp = Blueprint("auth", __name__)

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15


def is_locked(user):
    return user.locked_until is not None and user.locked_until > clock.now()


def record_failed_login(user):
    """Count a wrong password; the 5th in a row locks the account for 15 minutes."""
    user.failed_logins = (user.failed_logins or 0) + 1
    if user.failed_logins >= MAX_FAILED_LOGINS:
        user.failed_logins = 0
        user.locked_until = clock.now() + timedelta(minutes=LOCK_MINUTES)
        audit("lock", "user", user.id, actor_id=user.id)
    db.session.commit()


@bp.post("/auth/login")
def login():
    data = required(get_json(), "username", "password")
    user = User.query.filter_by(username=data["username"].strip()).first()
    if user is not None and is_locked(user):
        raise ApiError(423, "account_locked", "Account locked. Try again in 15 minutes")
    if user is None or not check_password(data["password"], user.password_hash):
        if user is not None:
            record_failed_login(user)
        raise ApiError(401, "invalid_credentials", "Wrong username or password")
    if user.status != "active":
        raise ApiError(403, "account_inactive", "This account has been deactivated")

    token = start_session(user)
    db.session.commit()
    minutes = current_app.config["SESSION_IDLE_MINUTES"]
    response = jsonify(token=token, role=user.role, expiresIn=minutes * 60)
    response.set_cookie(COOKIE, token, httponly=True, samesite="Lax", secure=request.is_secure)
    return response


@bp.post("/auth/logout")
def logout():
    if not end_session(request_token()):
        raise ApiError(401, "not_logged_in", "No active session")
    db.session.commit()
    response = jsonify(status="ok")
    response.delete_cookie(COOKIE)
    return response


@bp.get("/ui/login")
def login_page():
    return render_template("login.html")
