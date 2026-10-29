from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """raise ApiError(409, "duplicate_term", "Term 2026-ODD already exists")

    Becomes JSON {"error": {"code", "message"}} for the API, or an error page under /ui.
    Never put passwords, tokens or PII in the message.
    """

    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def get_json():
    """The request body as a dict ({} if there is none)."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def required(data, *fields):
    """Raise 400 if any field is missing or blank. Returns data."""
    missing = [f for f in fields if str(data.get(f, "")).strip() == ""]
    if missing:
        raise ApiError(400, "missing_field", "Missing required field: " + ", ".join(missing))
    return data


def as_int(value, field):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ApiError(400, "invalid_field", f"{field} must be a whole number")


def as_float(value, field):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ApiError(400, "invalid_field", f"{field} must be a number")


def _respond(status, code, message):
    if request.path.startswith("/ui"):
        return render_template("error.html", status=status, message=message), status
    return jsonify(error={"code": code, "message": message}), status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(e):
        return _respond(e.status, e.code, e.message)

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return _respond(e.code, e.name.lower().replace(" ", "_"), e.description)
