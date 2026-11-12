"""Start the app:  python src/run.py          ->  http://localhost:8000
HTTPS mode:     HTTPS=1 python src/run.py   ->  https://localhost:8000
(Not 5000: macOS uses that port for AirPlay.)"""
import os
import ssl

from werkzeug.serving import WSGIRequestHandler

from app import create_app

app = create_app("dev")

# TLS 1.2 suites with forward secrecy and AEAD only: no CBC suites (testssl LUCKY13 note).
# TLS 1.3 suites are AEAD already and are not affected by this list.
TLS12_CIPHERS = "ECDHE+AESGCM:ECDHE+CHACHA20"


def make_ssl_context(cert="cert.pem", key="key.pem"):
    """TLS 1.2 minimum (SRS-SR-001). Get the cert files from scripts/make_cert.sh."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.set_ciphers(TLS12_CIPHERS)
    ctx.load_cert_chain(cert, key)
    return ctx


class RequestHandler(WSGIRequestHandler):
    """Sends "Server: SRS-App" instead of the Werkzeug and Python versions (ZAP finding)."""

    def version_string(self):
        return "SRS-App"


def debug_enabled():
    """Debug stays off unless explicitly requested: the debugger leaks tracebacks (TC-Sec-01)."""
    return os.getenv("FLASK_DEBUG") == "1"


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    if os.getenv("HTTPS") == "1":
        app.run(debug=debug_enabled(), port=port, ssl_context=make_ssl_context(),
                request_handler=RequestHandler)
    else:
        app.run(debug=debug_enabled(), port=port, request_handler=RequestHandler)
