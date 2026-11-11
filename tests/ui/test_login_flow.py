import os
import threading
import time

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from werkzeug.serving import make_server

from app import create_app
from app.extensions import db
from app.core.security import hash_password
from app.models import User


BASE_URL = "http://127.0.0.1:8765"

ACCOUNTS = [
    ("test_admin", "admin", "/ui/admin"),
    ("test_faculty", "faculty", "/ui/faculty"),
    ("test_student", "student", "/ui/student"),
]


@pytest.fixture(scope="module")
def live_server():
    app = create_app("test")

    with app.app_context():
        db.create_all()

        for username, role, _ in ACCOUNTS:
            user = User(
                username=username,
                password_hash=hash_password("TestPass123!"),
                name=f"Test {role.title()}",
                role=role,
            )
            db.session.add(user)

        db.session.commit()

    server = make_server("127.0.0.1", 8765, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    time.sleep(1)

    yield BASE_URL

    server.shutdown()
    thread.join(timeout=5)

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1365,900")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(3)

    yield driver

    driver.quit()


@pytest.mark.parametrize(
    "username,role,expected_url",
    ACCOUNTS,
    ids=["admin-login", "faculty-login", "student-login"],
)
def test_role_login_flow(live_server, browser, username, role, expected_url):
    browser.get(f"{live_server}/ui/login")

    browser.find_element(By.ID, "username").send_keys(username)
    browser.find_element(By.ID, "password").send_keys("TestPass123!")
    browser.find_element(
        By.CSS_SELECTOR, "form[data-api='/auth/login'] button"
    ).click()

    WebDriverWait(browser, 10).until(
        EC.url_to_be(f"{live_server}{expected_url}")
    )

    heading = WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((By.TAG_NAME, "h1"))
    )

    assert "Welcome" in heading.text
    assert role in browser.find_element(
        By.CLASS_NAME, "navbar-text"
    ).text.lower()

    assert browser.find_elements(
        By.CSS_SELECTOR, "nav a.nav-link"
    ), "Expected role-specific navigation links"


def test_invalid_login_displays_error(live_server, browser):
    browser.get(f"{live_server}/ui/login")

    browser.find_element(By.ID, "username").send_keys("unknown_user")
    browser.find_element(By.ID, "password").send_keys("WrongPassword123!")
    browser.find_element(
        By.CSS_SELECTOR, "form[data-api='/auth/login'] button"
    ).click()

    error = WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".form-msg.alert-danger")
        )
    )

    assert "Wrong username or password" in error.text
    assert "/ui/login" in browser.current_url
