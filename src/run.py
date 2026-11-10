"""Start the app:  python src/run.py          ->  http://localhost:8000
HTTPS mode:     HTTPS=1 python src/run.py   ->  https://localhost:8000
(Not 5000: macOS uses that port for AirPlay.)"""
import os
import ssl

from app import create_app

app = create_app("dev")


def make_ssl_context(cert="cert.pem", key="key.pem"):
    """TLS 1.2 minimum (SRS-SR-001). Get the cert files from scripts/make_cert.sh."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(cert, key)
    return ctx


def debug_enabled():
    """Debug stays off unless explicitly requested: the debugger leaks tracebacks (TC-Sec-01)."""
    return os.getenv("FLASK_DEBUG") == "1"


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    if os.getenv("HTTPS") == "1":
        app.run(debug=debug_enabled(), port=port, ssl_context=make_ssl_context())
    else:
        app.run(debug=debug_enabled(), port=port)
