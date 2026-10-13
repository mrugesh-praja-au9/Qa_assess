"""Page object for /overview.htm.

The balances table is populated asynchronously (an AJAX call fills
#accountTable after the page loads), so every lookup here waits for the
specific account row to appear rather than assuming the table is ready.
"""

from pages.base_page import BasePage


def parse_currency(text: str) -> float:
    """Converts strings like '-$1,000.00' or '$250.00' into a float."""
    cleaned = text.strip().replace("$", "").replace(",", "")
    return float(cleaned)


class AccountsOverviewPage(BasePage):
    URL_PATH = "overview.htm"
    ACCOUNT_TABLE = "#accountTable"

    def open(self) -> None:
        self.goto(self.URL_PATH)

    def _row_for_account(self, account_id: str):
        row = self.page.locator(f"{self.ACCOUNT_TABLE} tbody tr", has=self.page.locator(f"a[href='activity.htm?id={account_id}']"))
        row.first.wait_for(state="visible")
        return row.first

    def get_balance(self, account_id: str) -> float:
        row = self._row_for_account(account_id)
        balance_text = row.locator("td").nth(1).inner_text()
        return parse_currency(balance_text)

    def get_account_ids(self) -> list[str]:
        self.page.locator(f"{self.ACCOUNT_TABLE} tbody tr").first.wait_for(state="visible")
        links = self.page.locator(f"{self.ACCOUNT_TABLE} tbody tr td a")
        return [links.nth(i).inner_text() for i in range(links.count())]
