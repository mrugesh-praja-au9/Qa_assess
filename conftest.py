"""Shared fixtures for the ParaBank fund-transfer audit suite."""

from dataclasses import dataclass

import pytest
from playwright.sync_api import Page

from pages.accounts_overview_page import AccountsOverviewPage
from pages.open_account_page import AccountType, OpenAccountPage
from pages.registration_page import RegistrationPage
from utils.data_generator import CustomerData, generate_customer
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class BankAccounts:
    """Two freshly opened accounts belonging to one freshly registered customer."""

    page: Page
    customer: CustomerData
    account_a: str
    account_b: str


@pytest.fixture
def bank_accounts(page: Page) -> BankAccounts:
    """Registers a unique customer and opens two accounts (checking + savings).

    Scoped per-test on purpose: each test gets its own customer and accounts,
    so tests stay independent of each other's state and execution order.
    """
    customer = generate_customer()
    logger.info("Registering new customer username=%s", customer.username)

    registration_page = RegistrationPage(page)
    registration_page.open()
    registration_page.register(customer)
    assert registration_page.is_registration_successful(), "Registration did not confirm success"

    overview_page = AccountsOverviewPage(page)
    overview_page.open()
    default_account_id = overview_page.get_account_ids()[0]
    logger.info("Default account for %s is %s", customer.username, default_account_id)

    open_account_page = OpenAccountPage(page)

    open_account_page.open()
    account_a = open_account_page.open_new_account(AccountType.CHECKING, default_account_id)
    logger.info("Opened checking account A=%s", account_a)

    open_account_page.open()
    account_b = open_account_page.open_new_account(AccountType.SAVINGS, default_account_id)
    logger.info("Opened savings account B=%s", account_b)

    return BankAccounts(page=page, customer=customer, account_a=account_a, account_b=account_b)
