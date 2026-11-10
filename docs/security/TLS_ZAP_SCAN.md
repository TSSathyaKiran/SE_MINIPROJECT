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
