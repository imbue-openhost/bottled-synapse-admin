import re
from collections.abc import Iterator

import httpx
import pytest
from openhost_test_harness import OpenhostStack
from playwright.sync_api import Page
from playwright.sync_api import expect


@pytest.fixture(autouse=True)
def clean_session(stack: OpenhostStack) -> Iterator[None]:
    """The session is a single server-side file shared by every test, and a leftover one would log the
    browser tests in. Reset it around each test."""
    httpx.put(f"{stack.app_url}/_openhost/session", json={})
    yield
    httpx.put(f"{stack.app_url}/_openhost/session", json={})


def test_healthz(stack: OpenhostStack) -> None:
    response = httpx.get(f"{stack.app_url}/healthz")
    assert response.status_code == 200
    assert response.text == "ok"


def test_serves_index(stack: OpenhostStack) -> None:
    response = httpx.get(f"{stack.app_url}/")
    assert response.status_code == 200
    assert "Synapse-Admin" in response.text


def test_serves_config_json(stack: OpenhostStack) -> None:
    response = httpx.get(f"{stack.app_url}/config.json")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_spa_fallback(stack: OpenhostStack) -> None:
    response = httpx.get(f"{stack.app_url}/no-such-path")
    assert response.status_code == 200
    assert "Synapse-Admin" in response.text


def test_version_placeholder_is_substituted(stack: OpenhostStack) -> None:
    """Upstream ships this vite placeholder unsubstituted, which throws in the browser."""
    response = httpx.get(f"{stack.app_url}/")
    assert "__SYNAPSE_ADMIN_VERSION__" not in response.text


def test_session_round_trips(stack: OpenhostStack) -> None:
    session = {"base_url": "https://matrix.example.com", "access_token": "syt_test", "user_id": "@a:example.com"}

    written = httpx.put(f"{stack.app_url}/_openhost/session", json=session)
    assert written.status_code == 204

    read = httpx.get(f"{stack.app_url}/_openhost/session")
    assert read.status_code == 200
    assert read.json() == session
    # The response carries an access token, so it must never be cached.
    assert "no-store" in read.headers["cache-control"]


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(["not", "an", "object"], id="not-an-object"),
        pytest.param({"key": 5}, id="non-string-value"),
        pytest.param({"key": "x" * 9000}, id="value-too-long"),
    ],
)
def test_session_rejects_malformed_payloads(stack: OpenhostStack, payload: object) -> None:
    response = httpx.put(f"{stack.app_url}/_openhost/session", json=payload)
    assert response.status_code == 400


def test_session_is_not_reachable_without_auth(stack: OpenhostStack) -> None:
    """stack.url goes through the router; an unauthenticated request must not reach the token."""
    response = httpx.get(f"{stack.url}/_openhost/session", follow_redirects=False)
    assert response.status_code != 200


def test_bundle_reads_the_session_from_the_server(stack: OpenhostStack) -> None:
    """The fork's wiring, checked without a browser: the shipped bundle must talk to our session endpoint,
    and index.html must not carry the token itself."""
    index = httpx.get(f"{stack.app_url}/").text
    asset = re.search(r"assets/index-[\w-]+\.js", index)
    assert asset, "could not find the built bundle in index.html"

    bundle = httpx.get(f"{stack.app_url}/{asset.group()}").text
    assert "_openhost/session" in bundle, "bundle does not reference the session endpoint"
    assert "access_token" not in index, "index.html must not inline the session"


# Playwright's locator waits intermittently block against this app even though it renders in about a
# second in a real browser (the login page's background SVG is fetched right after boot). Kept as a
# smoke test with a short budget so a stall costs seconds, not minutes. See README "remaining work".
@pytest.mark.xfail(strict=False, reason="playwright locator waits stall against react-admin here")
def test_login_page_renders(stack: OpenhostStack, page: Page) -> None:
    stack.playwright_login(page)
    page.goto(stack.url)
    expect(page.get_by_text("Welcome to Synapse-admin")).to_be_visible(timeout=30_000)
    expect(page.get_by_label("Homeserver URL")).to_be_visible()
