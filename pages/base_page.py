"""Common behaviour shared by every page object."""

from playwright.sync_api import Page

from config.settings import BASE_URL, DEFAULT_TIMEOUT_MS


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.page.set_default_timeout(DEFAULT_TIMEOUT_MS)

    def goto(self, path: str) -> None:
        self.page.goto(f"{BASE_URL}/{path.lstrip('/')}")
        self.page.wait_for_load_state("networkidle")
