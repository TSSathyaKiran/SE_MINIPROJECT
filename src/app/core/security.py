"""Passwords, login sessions and role checks (SRS-F-001/002, SR-002/003/005).

    @bp.post("/students")
    @require_role("admin")        # 401 if not logged in, 403 if wrong role
    def create_student(): ...

    @bp.get("/fees/<int:student_id>")
    @require_login                # any logged-in user; check ownership yourself
    def get_fees(student_id): ...

Inside a handler, current_user() is the logged-in User.
Pages under /ui redirect to the login page instead of returning 401.
"""
import hashlib
import secrets
from datetime import timedelta
from functools import wraps

import bcrypt
from flask import current_app, g, redirect, request

from ..extensions import db
from ..models import AuthSession
from . import clock
from .errors import ApiError

COOKIE = "srs_token"


def hash_password(password):
    rounds = current_app.config["BCRYPT_ROUNDS"]
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def start_session(user):
    """Create a session and return its token. Only a hash of it is stored."""
    token = secrets.token_urlsafe(32)
    db.session.add(AuthSession(token_hash=_hash_token(token), user_id=user.id,
                               last_seen=clock.now()))
    return token


def request_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return request.cookies.get(COOKIE)


def end_session(token):
    session = db.session.get(AuthSession, _hash_token(token)) if token else None
    if session:
        db.session.delete(session)
    return session is not None


def _load_user():
    token = request_token()
    session = db.session.get(AuthSession, _hash_token(token)) if token else None
    if session is None:
        return None
    idle_limit = timedelta(minutes=current_app.config["SESSION_IDLE_MINUTES"])
    if clock.now() - session.last_seen > idle_limit or session.user.status != "active":
        db.session.delete(session)
        db.session.commit()
        return None
    session.last_seen = clock.now()
    db.session.commit()
    return session.user


def current_user():
    return g.get("user")


def require_role(*roles):
    """Allow only these roles. With no roles, any logged-in user is allowed."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _load_user()
            if user is None:
                if request.path.startswith("/ui"):
                    return redirect("/ui/login")
                raise ApiError(401, "not_logged_in", "Please log in")
            if roles and user.role not in roles:
                raise ApiError(403, "forbidden", "You are not allowed to do this")
            g.user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator


require_login = require_role()
