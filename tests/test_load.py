import datetime
import random
import pytest_check as check
from src.transformer import VALID_FIELDS

DB_EXPECTED_TYPES = {  # any column not in this list is expected to be str
    "order_id": int,
    "customer_id": int,
    "quantity": int,
    "unit_price": float,
    "discount_amount": float,
    "order_total": float,
}


def test_expected_record_count(transformed_data, loaded_db):
    expected_count = len(transformed_data["valid"])
    cursor = loaded_db.cursor()
    actual_count = cursor.execute("SELECT COUNT(*) FROM orders;").fetchone()[0]
    assert actual_count == expected_count


def test_db_has_expected_columns(loaded_db):
    cursor = loaded_db.cursor()
    db_columns = {
        row[0]
        for row in cursor.execute("SELECT name FROM pragma_table_info('orders');")
    }
    assert db_columns == VALID_FIELDS


def test_expected_values_for_known_order(transformed_data, loaded_db):
    known_order = next(r for r in transformed_data["valid"] if r["order_id"] == 1001)
    order_id = known_order.get("order_id")

    cursor = loaded_db.cursor()
    order_record = cursor.execute(
        "SELECT * FROM orders WHERE order_id = ?;", (order_id,)
    ).fetchone()
    for key, expected_value in known_order.items():
        if isinstance(expected_value, datetime.datetime):
            expected_value = expected_value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(expected_value, datetime.date):
            expected_value = expected_value.strftime("%Y-%m-%d")
        check.equal(order_record[key], expected_value, msg=f"{key} mismatch")


def test_db_values_are_expected_type(transformed_data, loaded_db):
    known_order = next(r for r in transformed_data["valid"] if r["order_id"] == 1001)
    order_id = known_order.get("order_id")

    cursor = loaded_db.cursor()
    order_record = cursor.execute(
        "SELECT * FROM orders WHERE order_id = ?;", (order_id,)
    ).fetchone()

    for key, db_value in dict(order_record).items():
        if key in DB_EXPECTED_TYPES:
            check.equal(
                DB_EXPECTED_TYPES[key],
                type(order_record[key]),
                msg=f"type mismatch for {key}: expected {DB_EXPECTED_TYPES[key]}, got {type(order_record[key])}",
            )
        else:
            check.equal(
                str,
                type(order_record[key]),
                msg=f"type mismatch for {key}: expected str, got {type(order_record[key])}",
            )
