"""Page object for /transfer.htm."""

from pages.base_page import BasePage


class TransferFundsPage(BasePage):
    URL_PATH = "transfer.htm"
    AMOUNT_INPUT = "#amount"
    FROM_ACCOUNT_SELECT = "#fromAccountId"
    TO_ACCOUNT_SELECT = "#toAccountId"
    TRANSFER_BUTTON = "input[value='Transfer']"
    RESULT_PANEL = "#showResult"
    ERROR_PANEL = "#showError"
    OUTCOME_SELECTOR = f"{RESULT_PANEL}, {ERROR_PANEL}"

    def open(self) -> None:
        self.goto(self.URL_PATH)
        # from/to dropdowns are populated by an async call after load.
        self.page.locator(f"{self.FROM_ACCOUNT_SELECT} option").first.wait_for(state="attached")

    def submit_transfer(self, amount: float, from_account_id: str, to_account_id: str) -> None:
        self.page.fill(self.AMOUNT_INPUT, f"{amount:.2f}")
        self.page.select_option(self.FROM_ACCOUNT_SELECT, from_account_id)
        self.page.select_option(self.TO_ACCOUNT_SELECT, to_account_id)
        self.page.click(self.TRANSFER_BUTTON)
        self.page.wait_for_selector(self.OUTCOME_SELECTOR, state="visible")

    def is_transfer_successful(self) -> bool:
        return self.page.locator(self.RESULT_PANEL).is_visible()

    def is_transfer_errored(self) -> bool:
        return self.page.locator(self.ERROR_PANEL).is_visible()
