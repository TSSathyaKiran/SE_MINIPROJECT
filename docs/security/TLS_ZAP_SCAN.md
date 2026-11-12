# TLS and baseline security scan (TC-Sec-02)

Date: 2026-11-10 · Target: the app serving HTTPS on `https://localhost:8000` (self-signed
certificate from `scripts/make_cert.sh`, `HTTPS=1 python src/run.py`) · Branch: `feature/10-tls-and-final`

## testssl.sh 3.2 (28 s scan)

Protocol support:

| Protocol | Result |
| --- | --- |
| SSLv2 | not offered (OK) |
| SSLv3 | not offered (OK) |
| TLS 1.0 | not offered |
| TLS 1.1 | not offered |
| TLS 1.2 | offered (OK) |
| TLS 1.3 | offered (OK) |

Vulnerability checks: not vulnerable to Heartbleed, CCS, Ticketbleed, ROBOT, POODLE (SSL),
SWEET32, FREAK, DROWN, LOGJAM, BEAST, BREACH; Secure Renegotiation supported.

Findings:

- LUCKY13 (CVE-2013-0169, experimental): **potentially vulnerable** - the server offers CBC
  cipher suites from Python's default OpenSSL cipher list. Open item; mitigations are cipher-list
  changes in `src/run.py`, not done in this PR.
- Overall grade capped to **T** because the certificate is self-signed. Expected for localhost
  (TC-Sec-02 exempts the localhost demo); a real deployment needs a CA-issued certificate.

Raw log: `testssl.log` kept locally; the run took 28 seconds against `127.0.0.1:8000`.

## OWASP ZAP 2.17.0 baseline scan

Ran the baseline flow (traditional spider + passive scan, no active scan) against
`https://localhost:8000` through the ZAP daemon API, self-hosted on Java 17 (the official
baseline ships as a Docker image; no Docker was available, so the same spider and passive
rules ran without it).

**Scope: unauthenticated.** The app redirects every page to `/ui/login`, so the spider saw the
public login page and static assets only (10 URLs). Logged-in pages were not scanned.

Alerts (10 types, 32 instances):

| Risk | Alert | Instances |
| --- | --- | --- |
| Medium | Content Security Policy (CSP) Header Not Set | 3 |
| Medium | Missing Anti-clickjacking Header | 2 |
| Medium | Sub Resource Integrity Attribute Missing | 5 |
| Low | Strict-Transport-Security Header Not Set | 5 |
| Low | X-Content-Type-Options Header Missing | 4 |
| Low | Server Leaks Version Information via "Server" Header | 5 |
| Low | Cross-Domain JavaScript Source File Inclusion | 3 |
| Informational | Authentication Request Identified | 1 |
| Informational | Information Disclosure - Sensitive Information in URL | 2 |
| Informational | Re-examine Cache-control Directives | 2 |

No High or Critical alerts on the scanned surface. This does not cover the logged-in app.

Notes:

- "Sensitive Information in URL" flags the scanner's own probe of the login form
  (`/ui/login?username=ZAP&password=ZAP`). The real login is a JSON `POST /auth/login`;
  the app never puts credentials in URLs.
- Open findings (not fixed in this PR): missing CSP, anti-clickjacking, HSTS and
  X-Content-Type-Options headers, missing Subresource Integrity on third-party scripts,
  and the `Server` version header. Tracked in the Test Summary Report's open items.

Full reports: `zap-baseline-report.html` and `zap-baseline.json` kept locally.

## Fixes (2026-11-12)

Every finding above that the app can fix is fixed. The checks below ran against
`HTTPS=1 python src/run.py` with the demo data. ZAP and testssl.sh were not installed on the
machine used for this, so neither scanner was re-run. The fixes are checked by automated
tests instead, plus curl and openssl.

| Finding | Fix | Checked by |
| --- | --- | --- |
| CSP header not set | `Content-Security-Policy` on every response (`src/app/core/headers.py`): files from this app only, inline scripts need the request's nonce, no `unsafe-inline`, `frame-ancestors 'none'` | `tests/test_headers.py` (also checks every template for inline styles, `on...=` handlers and scripts without the nonce) |
| Missing anti-clickjacking header | `X-Frame-Options: DENY` and CSP `frame-ancestors 'none'` | `tests/test_headers.py` |
| Sub Resource Integrity missing; cross-domain JavaScript | Bootstrap 5.3.3 is served by the app from `src/app/static/vendor/` instead of a CDN. The files match the official SRI hashes, so no third-party file is loaded. The pages also work offline | `tests/test_headers.py` |
| HSTS not set | `Strict-Transport-Security: max-age=31536000; includeSubDomains` on HTTPS responses | `tests/test_headers.py` |
| X-Content-Type-Options missing | `X-Content-Type-Options: nosniff` | `tests/test_headers.py` |
| `Server` header leaks versions | `src/run.py` sends `Server: SRS-App` | `tests/test_tls.py` |
| Re-examine Cache-control | `Cache-Control: no-store` on pages and API responses (they hold personal data); static files can still be cached | `tests/test_headers.py` |
| testssl LUCKY13 (CBC suites) | TLS 1.2 offers only ECDHE suites with AES-GCM or ChaCha20 (`TLS12_CIPHERS` in `src/run.py`); TLS 1.3 is unchanged | `tests/test_tls.py`: no CBC suite offered, and a CBC-only client is refused |

Not changed: the self-signed certificate (expected for the localhost demo), and the two
informational alerts. Those alerts are the scanner's own login probe and the
login request itself.

```
$ curl -skI https://localhost:8443/ui/login
HTTP/1.1 200 OK
Server: SRS-App
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-...'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains
Cache-Control: no-store

$ openssl s_client -connect localhost:8443 -tls1_2 -cipher 'ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:AES128-SHA'
...:SSL routines:ssl3_read_bytes:tls alert handshake failure:...:SSL alert number 40
New, (NONE), Cipher is (NONE)

$ openssl s_client -connect localhost:8443 -tls1_2
New, TLSv1.2, Cipher is ECDHE-RSA-AES256-GCM-SHA384
```

Every page was also opened as each role in Chrome with this policy, and the console showed
no CSP errors. The browser tests in `tests/ui/` pass with these headers, and CI now runs them
in its `ui` job.
