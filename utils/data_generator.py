"""Generates dynamic test data so runs never collide on a shared demo server."""

import random
import string
from dataclasses import dataclass


def _random_digits(length: int) -> str:
    return "".join(random.choices(string.digits, k=length))


def _random_letters(length: int) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


@dataclass(frozen=True)
class CustomerData:
    first_name: str
    last_name: str
    street: str
    city: str
    state: str
    zip_code: str
    phone_number: str
    ssn: str
    username: str
    password: str


def generate_customer() -> CustomerData:
    """Builds a unique customer registration payload for a single test run."""
    unique_suffix = _random_letters(6) + _random_digits(4)
    return CustomerData(
        first_name="Audit",
        last_name="Tester",
        street="123 Main St",
        city="Austin",
        state="TX",
        zip_code="78701",
        phone_number=f"555{_random_digits(7)}",
        ssn=_random_digits(9),
        username=f"qa_{unique_suffix}",
        password="Qa@TestPass123",
    )
