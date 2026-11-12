"""TC-Sec-01 support: security headers on every response (core/headers.py).

These keep the OWASP ZAP baseline findings in docs/security/TLS_ZAP_SCAN.md fixed:
CSP, anti-clickjacking, X-Content-Type-Options, HSTS, third-party files, caching.
"""
import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "src" / "app" / "templates"


def csp(res):
    """The Content-Security-Policy header as {directive: sources}."""
    parts = res.headers["Content-Security-Policy"].split(";")
    return dict(part.strip().split(" ", 1) for part in parts)


def test_tc_sec_01_pages_api_and_files_carry_security_headers(client, login_as):
    _, admin = login_as("admin")
    for res in [client.get("/ui/login"), client.get("/terms", headers=admin),
                client.get("/static/css/app.css"), client.get("/no-such-path")]:
        assert res.headers["X-Frame-Options"] == "DENY"
        assert res.headers["X-Content-Type-Options"] == "nosniff"
        assert res.headers["Referrer-Policy"] == "same-origin"
        policy = csp(res)
        assert policy["default-src"] == "'self'" and policy["style-src"] == "'self'"
        assert policy["frame-ancestors"] == "'none'" and policy["object-src"] == "'none'"
        assert "unsafe-inline" not in res.headers["Content-Security-Policy"]


def test_tc_sec_01_inline_scripts_need_this_requests_nonce(client, login_as):
    _, faculty = login_as("faculty")
    nonces = []
    for _ in range(2):
        res = client.get("/ui/faculty/search", headers=faculty)   # page with an inline script
        nonce = re.fullmatch(r"'self' 'nonce-([\w-]+)'", csp(res)["script-src"]).group(1)
        assert f'<script nonce="{nonce}">' in res.get_data(as_text=True)
        nonces.append(nonce)
    assert nonces[0] != nonces[1]


def test_tc_sec_01_hsts_only_over_https(client):
    assert "Strict-Transport-Security" not in client.get("/health").headers
    res = client.get("/health", base_url="https://localhost")
    assert res.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"


def test_tc_sec_01_personal_data_is_not_cached(client, login_as):
    _, admin = login_as("admin")
    assert client.get("/students/search?q=S", headers=admin).headers["Cache-Control"] == "no-store"
    assert client.get("/ui/login").headers["Cache-Control"] == "no-store"
    assert "no-store" not in client.get("/static/js/api.js").headers.get("Cache-Control", "")


def test_tc_sec_01_bootstrap_is_served_by_the_app(client):
    html = client.get("/ui/login").get_data(as_text=True)
    for path in re.findall(r'(?:src|href)="(/static/vendor/[^"]+)"', html):
        assert client.get(path).status_code == 200, path
    assert "/static/vendor/bootstrap-5.3.3/bootstrap.min.css" in html


def test_tc_sec_01_templates_follow_the_csp_rules():
    """No files from other sites, style="...", on...= handlers or inline scripts without the nonce."""
    for path in sorted(TEMPLATES.rglob("*.html")):
        html, name = path.read_text(), path.relative_to(TEMPLATES)
        assert not re.search(r'<(script|link|img)\b[^>]*\b(src|href)="(https?:)?//', html), name
        assert not re.search(r"\sstyle=", html), name
        assert not re.search(r"\son[a-z]+=", html), name
        for tag in re.findall(r"<script\b[^>]*>", html):
            assert "src=" in tag or 'nonce="{{ csp_nonce }}"' in tag, (name, tag)
