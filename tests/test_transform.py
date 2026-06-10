import datetime

import pytest_check as check

from src.transformer import VALID_FIELDS

EXPECTED_TYPES = {
    "order_id": int,
    "customer_id": int,
    "order_date": datetime.date,
    "quantity": int,
    "unit_price": float,
    "discount_amount": float,
    "order_total": float,
    "last_updated": datetime.datetime,
}


# Structural Tests
def test_transform_completes_without_exception(transformed_data):
    assert transformed_data is not None


def test_transform_returns_expected_results(transformed_data):
    assert transformed_data.keys() == {"valid", "invalid"}


def test_transform_returns_two_lists(transformed_data):
    assert all(isinstance(transformed_data[k], list) for k in ("valid", "invalid"))


def test_each_valid_record_has_only_expected_keys(transformed_data):
    valid_records = transformed_data.get("valid")
    assert all(record.keys() <= VALID_FIELDS for record in valid_records)


def test_each_valid_record_has_fields_with_expected_types(transformed_data):
    for record in transformed_data.get("valid"):
        for field, expected_type in EXPECTED_TYPES.items():
            if field in record and record[field] is not None:
                assert isinstance(record[field], expected_type), (
                    f"{field}: expected {expected_type.__name__}, got {type(record[field]).__name__}"
                )


def test_each_invalid_record_has_expected_content(transformed_data):
    for item in transformed_data.get("invalid"):
        check.equal(
            set(item.keys()),
            {"record", "errors"},
            f"expected only record and error keys, but found {item.keys}",
        )
        check.is_instance(
            item["record"],
            dict,
            f"expected record to be type dict, got {type(item['record']).__name__}",
        )
        check.is_instance(
            item["errors"],
            list,
            f"expected errors to be type list, got {type(item['errors']).__name__}",
        )
        check.greater(len(item["errors"]), 0, "found empty errors list")
        check.is_true(
            all(isinstance(e, str) for e in item["errors"]),
            "found list of errors that are not all str",
        )


# Data Integrety Tests
def test_expected_count_of_valid_records(transformed_data, raw_orders):
    expected_valid = sum(1 for r in raw_orders if "!" not in r.get("product_id", ""))
    assert len(transformed_data["valid"]) == expected_valid


def test_expected_count_of_invalid_records(transformed_data, raw_orders):
    expected_invalid = sum(1 for r in raw_orders if "!" in r.get("product_id", ""))
    assert len(transformed_data["invalid"]) == expected_invalid


def test_all_raw_orders_in_transformed_data(transformed_data, raw_orders):
    expected_total_order_count = len(raw_orders)
    total_order_count = len(transformed_data["valid"]) + len(
        transformed_data["invalid"]
    )
    assert expected_total_order_count == total_order_count


def test_every_invalid_record_has_sigil(transformed_data):
    for item in transformed_data["invalid"]:
        assert "!" in item["record"].get("product_id", "")


def test_every_valid_record_does_not_have_sigil(transformed_data):
    for item in transformed_data["valid"]:
        assert "!" not in item.get("product_id", "")
