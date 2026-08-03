import httpx
import pytest
from openhost_test_harness import OpenhostStack
from playwright.sync_api import Page
from playwright.sync_api import expect


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


# Flaky: react-admin sometimes stalls after its initial checkAuth/logout and
# never mounts the login form (all assets load, no JS errors; reproducible with
# upstream's own docker image). Cause not yet found; see README "remaining work".
@pytest.mark.xfail(strict=False, reason="react-admin login page mount race under playwright")
def test_login_page_renders(stack: OpenhostStack, page: Page) -> None:
    stack.playwright_login(page)
    page.goto(stack.url)
    # The JS bundle is ~2MB; give the SPA time to load and mount.
    expect(page.get_by_text("Welcome to Synapse-admin")).to_be_visible(timeout=30_000)
    expect(page.get_by_label("Homeserver URL")).to_be_visible()
