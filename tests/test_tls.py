"""TC-Sec-02 / TC-Sec-01 support: HTTPS uses TLS 1.2 minimum and debug stays off by default."""
import os
import shutil
import socket
import ssl
import subprocess
import threading

import pytest

# run.py builds the dev app on import, so give it throwaway keys first.
# (conftest imports the package before this file, so env vars would land too late.)
from cryptography.fernet import Fernet

from app.config import Config

Config.SECRET_KEY = "tls-test-secret-key"
Config.PII_KEY = Fernet.generate_key().decode()

import run  # noqa: E402  (src/run.py)


@pytest.fixture(scope="module")
def cert_pair(tmp_path_factory):
    """A real self-signed cert, made the same way scripts/make_cert.sh makes it."""
    if not shutil.which("openssl"):
        pytest.skip("openssl not available")
    d = tmp_path_factory.mktemp("cert")
    cert, key = str(d / "cert.pem"), str(d / "key.pem")
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", key, "-out", cert, "-days", "1", "-subj", "/CN=localhost"],
        check=True, capture_output=True)
    return cert, key


def test_ssl_context_requires_tls_1_2_minimum(cert_pair):
    ctx = run.make_ssl_context(*cert_pair)
    assert ctx.protocol == ssl.PROTOCOL_TLS_SERVER
    assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2


def _serve_once(ctx):
    """Accept one TLS connection on an ephemeral port; return (port, errors)."""
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    errors = []

    def accept():
        try:
            conn, _ = server.accept()
            ctx.wrap_socket(conn, server_side=True).close()
        except ssl.SSLError as exc:  # a refused old-TLS client lands here
            errors.append(exc)
        finally:
            server.close()

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    return server.getsockname()[1], errors, thread


def test_tls_1_1_client_is_refused(cert_pair):
    ctx = run.make_ssl_context(*cert_pair)
    port, errors, thread = _serve_once(ctx)
    client = ssl.create_default_context()
    client.check_hostname = False
    client.verify_mode = ssl.CERT_NONE
    client.maximum_version = ssl.TLSVersion.TLSv1_1
    with pytest.raises(ssl.SSLError):
        with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
            client.wrap_socket(sock, server_hostname="localhost")
    thread.join(timeout=5)


def test_tls_1_2_client_is_accepted(cert_pair):
    ctx = run.make_ssl_context(*cert_pair)
    port, errors, thread = _serve_once(ctx)
    client = ssl.create_default_context()
    client.check_hostname = False
    client.verify_mode = ssl.CERT_NONE
    client.minimum_version = ssl.TLSVersion.TLSv1_2
    client.maximum_version = ssl.TLSVersion.TLSv1_2
    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        with client.wrap_socket(sock, server_hostname="localhost") as tls:
            assert tls.version() == "TLSv1.2"
    thread.join(timeout=5)
    assert not errors


def test_debug_off_by_default(monkeypatch):
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    assert run.debug_enabled() is False
    monkeypatch.setenv("FLASK_DEBUG", "1")
    assert run.debug_enabled() is True
