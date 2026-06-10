# Standard library
from pathlib import Path
import sqlite3

# Third party
import pytest

# Local
from src.extractor import read_csv
from src.transformer import transform
from src.constants import ORDERS_PATH, PROMOTIONS_PATH


@pytest.fixture(scope="session")
def raw_orders() -> list[dict]:
    if not Path(ORDERS_PATH).is_file():
        raise FileNotFoundError(f"Orders file not found: {ORDERS_PATH}")
    return read_csv(ORDERS_PATH)


@pytest.fixture(scope="session")
def raw_promotions() -> list[dict]:
    if not Path(PROMOTIONS_PATH).is_file():
        raise FileNotFoundError(f"Promotions file not found: {PROMOTIONS_PATH}")
    return read_csv(PROMOTIONS_PATH)


@pytest.fixture(scope="session")
def transformed_data(raw_orders, raw_promotions) -> dict:
    return transform(raw_orders, raw_promotions)


@pytest.fixture(scope="function")
def db_connection():
    conn = sqlite3.connect(":memory:")
    yield conn  # TEST RUNS HERE
    conn.close()  # TEARDOWN — runs after the test
