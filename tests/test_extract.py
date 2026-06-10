import pytest

from src.constants import ORDERS_PATH, PROMOTIONS_PATH
from src.extractor import read_csv

CSV_FILES = [ORDERS_PATH, PROMOTIONS_PATH]


@pytest.mark.parametrize("filepath", CSV_FILES)
def test_returns_correct_record_count(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    expected_count = len(lines) - 1  # minus header
    extracted_rows = read_csv(filepath)
    assert expected_count == len(extracted_rows)


@pytest.mark.parametrize("filepath", CSV_FILES)
def test_each_record_is_dict(filepath):
    extracted_rows = read_csv(filepath)
    assert all(isinstance(item, dict) for item in extracted_rows)


@pytest.mark.parametrize("filepath", CSV_FILES)
def test_malformed_rows_do_not_crash(filepath):
    records = read_csv(filepath)
    assert isinstance(records, list)
