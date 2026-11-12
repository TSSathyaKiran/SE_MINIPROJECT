"""TC-UX-01 step 2: the key flows work with the keyboard only (SRS-NF-005, WCAG 2.1.1).

Every action below is a key press (Tab, Shift+Tab, Enter, Space, arrow keys, typing);
nothing is clicked. Covers what the Tab-order check in run_accessibility_audit.py does
not: activating links and buttons, going backwards, and seeing form errors. Runs on the
demo data from src/seed.py in headless Chrome, like test_login_flow.py:

    pip install selenium
    pytest -v tests/ui/test_keyboard_flows.py
"""
import threading
import time
from datetime import datetime

import pytest
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.serving import make_server

from app import create_app
from app.core import clock
from app.extensions import db
from seed import seed  # src/seed.py


@pytest.fixture(scope="module")
def live_server():
    app = create_app("test")
    with app.app_context():
        seed()
    clock.set_now(datetime(2026, 11, 11, 10, 0))   # add/drop still open
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)
    clock.set_now(None)
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")              # needed on the CI's Linux runner
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1365,900")
    # Chrome's own "save password" / "password found in a breach" bubble takes keyboard
    # focus after the demo logins; it is browser UI, not part of the app
    options.add_experimental_option("prefs", {"credentials_enable_service": False,
                                              "profile.password_manager_enabled": False,
                                              "profile.password_manager_leak_detection": False})
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def press(browser, *keys):
    ActionChains(browser).send_keys(*keys).perform()


def focused(browser):
    return browser.switch_to.active_element


def shift_tab(browser):
    ActionChains(browser).key_down(Keys.SHIFT).send_keys(Keys.TAB).key_up(Keys.SHIFT).perform()


def tab_to(browser, matches, back=False, limit=80):
    """Press Tab (Shift+Tab if back) until the focused element matches; return it."""
    for _ in range(limit):
        if back:
            shift_tab(browser)
        else:
            press(browser, Keys.TAB)
        element = focused(browser)
        if matches(element):
            return element
    raise AssertionError("never reached the element with the keyboard")


def by_id(value):
    return lambda el: el.get_attribute("id") == value


def by_label(text):
    """Links and buttons by visible text or aria-label."""
    return lambda el: text in (el.get_attribute("aria-label") or "") or el.text.strip() == text


def wait_for_message(browser, text):
    """A form result box (role=alert, so screen readers announce it) shows text."""
    def shown(driver):
        boxes = driver.find_elements(By.CSS_SELECTOR, ".form-msg.alert")
        return next((box for box in boxes if text in box.text), False)
    box = WebDriverWait(browser, 10, poll_frequency=0.1).until(shown)
    assert box.get_attribute("role") == "alert"
    return box


def wait_for_url(browser, url):
    WebDriverWait(browser, 10).until(EC.url_to_be(url))


def log_in(browser, base, username, password):
    browser.get(f"{base}/ui/login")
    tab_to(browser, by_id("username")).send_keys(username)
    press(browser, Keys.TAB)
    assert focused(browser).get_attribute("id") == "password"
    press(browser, password, Keys.ENTER)


def test_tc_ux_01_login_with_keyboard_errors_and_reverse_order(live_server, browser):
    log_in(browser, live_server, "student1", "wrong-password")
    wait_for_message(browser, "Wrong username or password")
    assert browser.current_url == f"{live_server}/ui/login"

    # Shift+Tab goes back through the same fields in reverse
    tab_to(browser, by_id("password"))
    shift_tab(browser)
    assert focused(browser).get_attribute("id") == "username"

    log_in(browser, live_server, "student1", "student123")
    wait_for_url(browser, f"{live_server}/ui/student")


def test_tc_ux_01_skip_link_and_menu_with_keyboard(live_server, browser):
    log_in(browser, live_server, "student1", "student123")
    wait_for_url(browser, f"{live_server}/ui/student")

    # the first Tab reaches "Skip to content"; Enter jumps past the menu
    press(browser, Keys.TAB)
    assert focused(browser).text.strip() == "Skip to content"
    press(browser, Keys.ENTER)
    press(browser, Keys.TAB)
    assert browser.execute_script(
        "return document.querySelector('main').contains(document.activeElement)")

    # menu links open with Enter; Shift+Tab walks back to an earlier link
    browser.get(f"{live_server}/ui/student")
    tab_to(browser, by_label("Fees"))
    tab_to(browser, by_label("Grades & transcript"), back=True)
    press(browser, Keys.ENTER)
    wait_for_url(browser, f"{live_server}/ui/student/grades")


def test_tc_ux_01_student_enrolls_and_drops_with_keyboard(live_server, browser):
    log_in(browser, live_server, "student3", "student123")
    wait_for_url(browser, f"{live_server}/ui/student")
    tab_to(browser, by_label("Courses & enrollment"))
    press(browser, Keys.ENTER)
    wait_for_url(browser, f"{live_server}/ui/student/courses")

    # an error is shown next to the button that caused it
    tab_to(browser, by_label("Enroll in CS102 section A"))
    press(browser, Keys.ENTER)
    wait_for_message(browser, "Prerequisite not met: CS101")

    tab_to(browser, by_label("Enroll in EC101 section A"))
    press(browser, Keys.SPACE)                      # Space works on buttons too
    wait_for_message(browser, "Enrolled.")
    WebDriverWait(browser, 10).until(            # the page reloads with a Drop button
        EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Drop EC101 section A']")))

    tab_to(browser, by_label("Drop EC101 section A"))
    press(browser, Keys.ENTER)
    wait_for_message(browser, "Course dropped.")


def test_tc_ux_01_faculty_marks_attendance_with_keyboard(live_server, browser):
    log_in(browser, live_server, "faculty1", "faculty123")
    wait_for_url(browser, f"{live_server}/ui/faculty")
    tab_to(browser, by_label("Attendance"))
    press(browser, Keys.ENTER)
    wait_for_url(browser, f"{live_server}/ui/faculty/attendance")

    # pick the CS102 section by typing its code on the focused list, then Load
    # (typing works on every platform; arrow keys open the list on macOS)
    select = tab_to(browser, by_id("sectionId"))
    press(browser, "CS102")
    assert "CS102" in select.find_element(By.CSS_SELECTOR, "option:checked").text
    tab_to(browser, by_label("Load"))
    press(browser, Keys.ENTER)
    WebDriverWait(browser, 10).until(EC.url_contains("sectionId="))
    WebDriverWait(browser, 10).until(EC.text_to_be_present_in_element((By.TAG_NAME, "h2"), "CS102"))

    # radio buttons: Tab into the group, arrow key moves the choice to Absent
    radio = tab_to(browser, lambda el: (el.get_attribute("type") == "radio"
                                        and el.get_attribute("value") == "present"))
    press(browser, Keys.ARROW_RIGHT)
    absent = focused(browser)
    assert absent.get_attribute("value") == "absent" and absent.is_selected()
    assert absent.get_attribute("name") == radio.get_attribute("name")

    tab_to(browser, by_label("Save attendance"))
    press(browser, Keys.ENTER)
    wait_for_message(browser, "Saved attendance for 2 student(s).")


def test_tc_ux_01_admin_form_errors_and_logout_with_keyboard(live_server, browser):
    log_in(browser, live_server, "admin", "admin123")
    wait_for_url(browser, f"{live_server}/ui/admin")
    tab_to(browser, by_label("Terms"))
    press(browser, Keys.ENTER)
    wait_for_url(browser, f"{live_server}/ui/admin/terms")

    # an empty required field is caught before anything is sent
    name = tab_to(browser, by_id("name"))
    press(browser, Keys.ENTER)
    time.sleep(0.5)                                  # time for a request, if one were sent
    assert browser.execute_script("return arguments[0].validity.valueMissing", name)
    assert not browser.find_elements(By.CSS_SELECTOR, ".form-msg.alert")

    press(browser, "2026-ODD", Keys.ENTER)
    wait_for_message(browser, "Term 2026-ODD already exists")
    press(browser, *[Keys.BACKSPACE] * 8, "2027-EVEN", Keys.ENTER)
    wait_for_message(browser, "Term created.")

    browser.get(f"{live_server}/ui/admin")
    tab_to(browser, by_label("Log out"))
    press(browser, Keys.ENTER)
    wait_for_url(browser, f"{live_server}/ui/login")
