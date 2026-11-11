import json
import os
import subprocess
import threading
import time
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from app import create_app

RESULTS = ROOT / "docs" / "Test_Plan" / "results"
AXE_FILE = ROOT / "node_modules" / "axe-core" / "axe.min.js"
BASE_URL = "http://127.0.0.1:8766"

ACCOUNTS = [
    ("admin", "admin123", "/ui/admin"),
    ("faculty1", "faculty123", "/ui/faculty"),
    ("student1", "student123", "/ui/student"),
]

TAGS = [
    "wcag2a", "wcag2aa",
    "wcag21a", "wcag21aa",
    "wcag22aa",
]


def save_json(name, data):
    (RESULTS / name).write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def run_axe(driver, name, axe_source):
    driver.execute_script(axe_source)

    result = driver.execute_async_script("""
        const done = arguments[0];
        axe.run(document, {
          runOnly: {
            type: "tag",
            values: ["wcag2a", "wcag2aa", "wcag21a",
                     "wcag21aa", "wcag22aa"]
          }
        }).then(results => done({
          violations: results.violations.map(v => ({
            id: v.id,
            impact: v.impact,
            description: v.description,
            help: v.help,
            helpUrl: v.helpUrl,
            nodes: v.nodes.map(n => ({
              target: n.target,
              summary: n.failureSummary
            }))
          })),
          passes: results.passes.length,
          incomplete: results.incomplete.length,
          inapplicable: results.inapplicable.length
        })).catch(error => done({error: String(error)}));
    """)

    save_json(f"axe-{name}.json", result)
    print(
        f"[axe] {name}: "
        f"{len(result.get('violations', []))} violations",
        flush=True
    )
    return result


def keyboard_check(driver, name):
    # Run keyboard navigation in an isolated browser.
    page_url = driver.current_url
    cookies = driver.get_cookies()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1365,900")

    keyboard_driver = webdriver.Chrome(options=options)

    try:
        keyboard_driver.get(BASE_URL + "/ui/login")

        for cookie in cookies:
            transferable = {
                key: cookie[key]
                for key in (
                    "name", "value", "path", "domain",
                    "secure", "httpOnly", "sameSite", "expiry"
                )
                if key in cookie
            }
            keyboard_driver.add_cookie(transferable)

        keyboard_driver.get(page_url)
        WebDriverWait(keyboard_driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        keyboard_driver.find_element(By.TAG_NAME, "body").click()

        observations = []
        seen = set()
        repeated = False

        for _ in range(100):
            ActionChains(keyboard_driver).send_keys(Keys.TAB).perform()

            item = keyboard_driver.execute_script("""
                const e = document.activeElement;
                const style = getComputedStyle(e);
                const rect = e.getBoundingClientRect();

                return {
                  tag: e.tagName,
                  id: e.id || "",
                  name: e.getAttribute("name") || "",
                  role: e.getAttribute("role") || "",
                  text: (e.innerText || e.value || "").trim().slice(0, 80),
                  href: e.getAttribute("href") || "",
                  tabindex: e.getAttribute("tabindex"),
                  disabled: !!e.disabled,
                  focusVisible: e.matches(":focus-visible"),
                  outlineStyle: style.outlineStyle,
                  outlineWidth: style.outlineWidth,
                  outlineColor: style.outlineColor,
                  boxShadow: style.boxShadow,
                  visible: !!(rect.width && rect.height)
                };
            """)

            signature = (
                item["tag"], item["id"], item["name"],
                item["href"], item["text"]
            )

            if signature in seen:
                repeated = True
                break

            seen.add(signature)

            # BODY is not an interactive control and should not be
            # counted as a missing focus indicator.
            observations.append(item)

        result = {
            "page": name,
            "focus_stops": observations,
            "focus_stop_count": len(observations),
            "completed_cycle": repeated,
            "body_received_focus": any(
                item["tag"] == "BODY" for item in observations
            ),
            "missing_visible_focus_indicator": [
                item for item in observations
                if item["tag"] != "BODY"
                and not item["focusVisible"]
                and item["outlineStyle"] in ("none", "hidden")
                and item["boxShadow"] == "none"
            ]
        }

        save_json(f"keyboard-{name}.json", result)

        print(
            f"[keyboard] {name}: "
            f"{result['focus_stop_count']} focus stops; "
            f"cycle detected={repeated}; "
            f"body focus={result['body_received_focus']}",
            flush=True
        )

        return result

    finally:
        keyboard_driver.quit()


def lighthouse(name, url, cookie_header=None):
    base = RESULTS / f"lighthouse-{name}"
    header_file = RESULTS / f"lighthouse-headers-{name}.json"

    command = [
        "npx.cmd", "lighthouse", url,
        "--only-categories=accessibility",
        "--output=json",
        "--output=html",
        f"--output-path={base}",
        "--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage",
        "--quiet",
    ]

    try:
        if cookie_header:
            header_file.write_text(
                json.dumps({"Cookie": cookie_header}),
                encoding="utf-8"
            )
            command.append(f"--extra-headers={header_file}")

        print(f"\n[Lighthouse] Auditing {name}", flush=True)

        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            shell=True,
        )

        log = (
            f"Exit code: {completed.returncode}\n\n"
            f"STDOUT:\n{completed.stdout}\n\n"
            f"STDERR:\n{completed.stderr}\n"
        )

        (RESULTS / f"lighthouse-{name}-run.txt").write_text(
            log, encoding="utf-8"
        )

        json_report = Path(str(base) + ".report.json")

        if completed.returncode != 0 or not json_report.exists():
            print(f"[Lighthouse] FAILED: {name}", flush=True)
            return {"status": "failed"}

        report = json.loads(
            json_report.read_text(encoding="utf-8")
        )
        category = report.get("categories", {}).get(
            "accessibility", {}
        )
        score = category.get("score")

        result = {
            "status": "completed",
            "score": score,
            "score_percent": round(score * 100) if score is not None else None,
            "html_report": base.name + ".report.html",
            "json_report": json_report.name,
        }

        print(
            f"[Lighthouse] {name}: "
            f"{result['score_percent']}%",
            flush=True
        )
        return result

    finally:
        if header_file.exists():
            header_file.unlink()


def login_as(driver, username, password, dashboard):
    driver.get(BASE_URL + "/ui/login")

    wait = WebDriverWait(driver, 20)
    username_field = wait.until(
        EC.visibility_of_element_located((By.ID, "username"))
    )
    password_field = wait.until(
        EC.visibility_of_element_located((By.ID, "password"))
    )

    username_field.clear()
    username_field.send_keys(username)
    password_field.clear()
    password_field.send_keys(password)

    driver.find_element(
        By.CSS_SELECTOR, "form[data-api] button"
    ).click()

    def login_outcome(d):
        if d.current_url.rstrip("/") == (BASE_URL + dashboard).rstrip("/"):
            return "success"
        message = d.find_element(By.CSS_SELECTOR, ".form-msg").text.strip()
        return ("error", message) if message else False

    outcome = WebDriverWait(driver, 20).until(login_outcome)

    if outcome != "success":
        raise RuntimeError(
            f"Login rejected for {username}: {outcome[1]}; "
            f"current URL: {driver.current_url}"
        )

    print(
        f"[Login] {username} successfully reached {dashboard}",
        flush=True
    )


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)

    if not AXE_FILE.exists():
        raise FileNotFoundError(
            f"axe-core not found: {AXE_FILE}. "
            "Run npm install first."
        )

    axe_source = AXE_FILE.read_text(encoding="utf-8")

    existing_db = (ROOT / "src" / "instance" / "srs.db").resolve()
    os.environ["DATABASE_URL"] = existing_db.as_uri().replace(
        "file:///", "sqlite:///"
    )

    app = create_app("dev")
    server = make_server(
        "127.0.0.1", 8766, app, threaded=True
    )
    thread = threading.Thread(
        target=server.serve_forever, daemon=True
    )
    thread.start()
    time.sleep(1)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1365,900")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = None

    summary = {
        "audit_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_url": BASE_URL,
        "axe_tags": TAGS,
        "axe": {},
        "keyboard": {},
        "lighthouse": {},
        "errors": [],
    }

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1365, 900)

        # Public login page.
        print("\n=== LOGIN PAGE ===", flush=True)
        driver.get(BASE_URL + "/ui/login")

        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "username"))
        )

        summary["axe"]["login"] = run_axe(
            driver, "login", axe_source
        )
        summary["keyboard"]["login"] = keyboard_check(
            driver, "login"
        )
        summary["lighthouse"]["login"] = lighthouse(
            "login", BASE_URL + "/ui/login"
        )

        # Authenticated dashboards.
        for username, password, dashboard in ACCOUNTS:
            role = dashboard.rsplit("/", 1)[-1]

            print(f"\n=== {role.upper()} DASHBOARD ===", flush=True)

            # Give every role a completely fresh browser session.
            if driver:
                driver.quit()

            driver = webdriver.Chrome(options=options)
            driver.set_window_size(1365, 900)

            try:
                login_as(
                    driver, username, password, dashboard
                )

                summary["axe"][role] = run_axe(
                    driver, role, axe_source
                )
                summary["keyboard"][role] = keyboard_check(
                    driver, role
                )

                cookies = driver.get_cookies()
                cookie_header = "; ".join(
                    f"{cookie['name']}={cookie['value']}"
                    for cookie in cookies
                )

                summary["lighthouse"][role] = lighthouse(
                    role,
                    BASE_URL + dashboard,
                    cookie_header
                )

                # Log out before testing the next account.
                driver.get(BASE_URL + "/ui/login")

            except Exception as error:
                message = f"{role}: {type(error).__name__}: {error}"
                summary["errors"].append(message)
                print(f"[ERROR] {message}", flush=True)

                try:
                    for entry in driver.get_log("browser"):
                        print(
                            f"[BROWSER {role}] {entry['level']}: "
                            f"{entry['message']}",
                            flush=True
                        )
                except Exception as log_error:
                    print(f"[BROWSER LOG UNAVAILABLE] {log_error}", flush=True)

                try:
                    driver.save_screenshot(
                        str(RESULTS / f"debug-{role}.png")
                    )
                    (RESULTS / f"debug-{role}.txt").write_text(
                        f"URL: {driver.current_url}\n"
                        f"Page source:\n{driver.page_source[:12000]}",
                        encoding="utf-8"
                    )
                except Exception:
                    pass

                continue

    finally:
        if driver:
            driver.quit()

        server.shutdown()

        save_json("accessibility-summary.json", summary)

        print("\n=== ACCESSIBILITY AUDIT SUMMARY ===")
        print(json.dumps(summary, indent=2))
        print("\nResults saved in docs/Test_Plan/results/")


if __name__ == "__main__":
    main()
