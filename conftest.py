"""Shared fixtures for the ParaBank fund-transfer audit suite."""

import os
import platform
import shutil
import sys
from dataclasses import dataclass

import allure
import pytest
from playwright.sync_api import Page

from config.settings import BASE_URL
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

    with allure.step(f"Register new customer '{customer.username}'"):
        logger.info("Registering new customer username=%s", customer.username)
        registration_page = RegistrationPage(page)
        registration_page.open()
        registration_page.register(customer)
        assert registration_page.is_registration_successful(), "Registration did not confirm success"

    with allure.step("Discover the customer's default account"):
        overview_page = AccountsOverviewPage(page)
        overview_page.open()
        default_account_id = overview_page.get_account_ids()[0]
        logger.info("Default account for %s is %s", customer.username, default_account_id)
        allure.attach(default_account_id, name="Default account ID", attachment_type=allure.attachment_type.TEXT)

    open_account_page = OpenAccountPage(page)

    with allure.step("Open a new CHECKING account (Account A)"):
        open_account_page.open()
        account_a = open_account_page.open_new_account(AccountType.CHECKING, default_account_id)
        logger.info("Opened checking account A=%s", account_a)
        allure.attach(account_a, name="Account A (checking)", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Open a new SAVINGS account (Account B)"):
        open_account_page.open()
        account_b = open_account_page.open_new_account(AccountType.SAVINGS, default_account_id)
        logger.info("Opened savings account B=%s", account_b)
        allure.attach(account_b, name="Account B (savings)", attachment_type=allure.attachment_type.TEXT)

    return BankAccounts(page=page, customer=customer, account_a=account_a, account_b=account_b)


@pytest.fixture(scope="session", autouse=True)
def allure_environment():
    """Writes environment.properties so the Allure report's Overview tab shows
    what this run actually targeted (server, browser, Python/OS versions)."""
    results_dir = "reports/allure-results"
    os.makedirs(results_dir, exist_ok=True)
    properties = {
        "Target.URL": BASE_URL,
        "Browser": "chromium",
        "Python": sys.version.split()[0],
        "OS": f"{platform.system()} {platform.release()}",
    }
    with open(os.path.join(results_dir, "environment.properties"), "w", encoding="utf-8") as f:
        f.writelines(f"{key}={value}\n" for key, value in properties.items())

    shutil.copyfile("config/allure_categories.json", os.path.join(results_dir, "categories.json"))
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attaches a screenshot to the Allure report whenever a test fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page is not None:
            allure.attach(
                page.screenshot(full_page=True),
                name="Failure screenshot",
                attachment_type=allure.attachment_type.PNG,
            )
