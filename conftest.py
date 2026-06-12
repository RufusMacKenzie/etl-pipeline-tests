# Standard library
import datetime
from pathlib import Path
import sqlite3

# Third party
import pytest

# Local
from src.extractor import read_csv
from src.transformer import transform
from src.loader import create_schema, load
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


@pytest.fixture(scope="session")
def db_connection():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    sqlite3.register_adapter(datetime.date, lambda d: d.strftime("%Y-%m-%d"))
    sqlite3.register_adapter(
        datetime.datetime, lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")
    )
    yield conn  # TEST RUNS HERE
    conn.close()  # TEARDOWN — runs after the test


@pytest.fixture(scope="session")
def loaded_db(db_connection, transformed_data):
    create_schema(db_connection)
    load(transformed_data["valid"], db_connection)
    db_connection.commit()
    return db_connection
