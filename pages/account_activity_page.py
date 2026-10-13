"""Page object for /activity.htm?id=<accountId>."""

from dataclasses import dataclass

from pages.accounts_overview_page import parse_currency
from pages.base_page import BasePage


@dataclass(frozen=True)
class Transaction:
    date: str
    description: str
    debit: float | None
    credit: float | None


class AccountActivityPage(BasePage):
    TRANSACTION_ROWS = "#transactionTable tbody tr"
    NO_TRANSACTIONS_MESSAGE = "#noTransactions"

    def open(self, account_id: str) -> None:
        self.goto(f"activity.htm?id={account_id}")
        self.page.locator(f"{self.TRANSACTION_ROWS}, {self.NO_TRANSACTIONS_MESSAGE}").first.wait_for(state="visible")

    def get_transactions(self) -> list[Transaction]:
        rows = self.page.locator(self.TRANSACTION_ROWS)
        transactions = []
        for i in range(rows.count()):
            cells = rows.nth(i).locator("td")
            debit_text = cells.nth(2).inner_text().strip()
            credit_text = cells.nth(3).inner_text().strip()
            transactions.append(
                Transaction(
                    date=cells.nth(0).inner_text().strip(),
                    description=cells.nth(1).inner_text().strip(),
                    debit=parse_currency(debit_text) if debit_text else None,
                    credit=parse_currency(credit_text) if credit_text else None,
                )
            )
        return transactions

    def count_matching_transactions(self, description: str, amount: float, date: str) -> int:
        matches = 0
        for transaction in self.get_transactions():
            amount_for_row = transaction.debit if transaction.debit is not None else transaction.credit
            if (
                transaction.description == description
                and amount_for_row is not None
                and abs(amount_for_row - amount) < 0.001
                and transaction.date == date
            ):
                matches += 1
        return matches
