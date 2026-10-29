"""Login and logout (SRS-F-001). Lockout after 5 failures is issue #2."""
from flask import Blueprint, current_app, jsonify, render_template, request

from ..core.errors import ApiError, get_json, required
from ..core.security import (COOKIE, check_password, end_session, request_token,
                             start_session)
from ..extensions import db
from ..models import User

bp = Blueprint("auth", __name__)


def record_failed_login(user):
    user.failed_logins = (user.failed_logins or 0) + 1
    db.session.commit()


@bp.post("/auth/login")
def login():
    data = required(get_json(), "username", "password")
    user = User.query.filter_by(username=data["username"].strip()).first()
    # TODO #2: if user.locked_until is in the future, raise 423. Lock for
    # 15 minutes on the 5th failure, audit the lock, and reset the count on a
    # successful login.
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
