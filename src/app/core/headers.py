"""Security headers on every response (fixes the OWASP ZAP baseline findings, TC-Sec-01).

The Content-Security-Policy only lets pages load files from this app and run an inline
<script> that carries this request's nonce. When you write a template:
  - inline script:  <script nonce="{{ csp_nonce }}"> ... </script>
  - no style="..." or onclick="..." attributes: add a class to static/css/app.css, and use
    data-confirm="Question?" on a data-api form instead of onclick="return confirm(...)"
tests/test_headers.py checks every template for these rules.
"""
import secrets

from flask import g, request

STATIC = "static"


def content_security_policy(nonce):
    return "; ".join([
        "default-src 'self'",
        f"script-src 'self' 'nonce-{nonce}'",
        "style-src 'self'",
        "img-src 'self' data:",          # Bootstrap draws some icons as data: SVGs
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ])


def register_security_headers(app):
    @app.before_request
    def make_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    @app.context_processor
    def nonce_for_templates():
        return {"csp_nonce": g.get("csp_nonce", "")}

    @app.after_request
    def add_security_headers(response):
        nonce = g.get("csp_nonce") or secrets.token_urlsafe(16)
        headers = response.headers
        headers["Content-Security-Policy"] = content_security_policy(nonce)
        headers["X-Frame-Options"] = "DENY"
        headers["X-Content-Type-Options"] = "nosniff"
        headers["Referrer-Policy"] = "same-origin"
        if request.is_secure:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.endpoint != STATIC and "Cache-Control" not in headers:
            headers["Cache-Control"] = "no-store"   # pages and API hold personal data
        return response
