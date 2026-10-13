"""Central configuration for the ParaBank test suite."""

import os

BASE_URL = os.getenv("PARABANK_BASE_URL", "https://parabank.parasoft.com/parabank")

DEFAULT_TIMEOUT_MS = 15_000

TRANSFER_AMOUNT = 250.00
NEGATIVE_PATH_OVERDRAFT_BUFFER = 1_000_000.00
