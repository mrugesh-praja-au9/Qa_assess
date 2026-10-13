"""Page object for /openaccount.htm."""

from pages.base_page import BasePage


class AccountType:
    CHECKING = "0"
    SAVINGS = "1"


class OpenAccountPage(BasePage):
    URL_PATH = "openaccount.htm"
    TYPE_SELECT = "#type"
    FROM_ACCOUNT_SELECT = "#fromAccountId"
    OPEN_BUTTON = "#openAccountForm input[value='Open New Account']"
    RESULT_PANEL = "#openAccountResult"
    NEW_ACCOUNT_ID = "#newAccountId"

    def open(self) -> None:
        self.goto(self.URL_PATH)
        # The "fund from" dropdown is populated by an async call; wait for it
        # before interacting so we never select a stale/empty option.
        self.page.locator(f"{self.FROM_ACCOUNT_SELECT} option").first.wait_for(state="attached")

    def open_new_account(self, account_type: str, fund_from_account_id: str) -> str:
        self.page.select_option(self.TYPE_SELECT, account_type)
        self.page.select_option(self.FROM_ACCOUNT_SELECT, fund_from_account_id)
        self.page.click(self.OPEN_BUTTON)
        self.page.wait_for_selector(self.RESULT_PANEL, state="visible")
        return self.page.locator(self.NEW_ACCOUNT_ID).inner_text()
