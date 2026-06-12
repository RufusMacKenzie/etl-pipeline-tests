# ETL Pipeline pytest Test Suite

A pytest-based test suite validating an ETL data pipeline that extracts order and 
promotion data from CSV files, transforms and validates the data against business rules, 
and loads clean records into a SQLite database.

Built as a portfolio project to demonstrate Python ETL testing practices.

## Pipeline Stages
- **Extract** — reads orders and promotions CSV files into Python dicts
- **Transform** — validates and type-converts records, separating valid from invalid
- **Load** — writes valid records to SQLite

## Test Data Convention
Orders in `data/orders.csv` use a sigil convention to identify expected invalid records:
- A `!` appended to the `product_id` field (e.g. `SKU-C3000003!`) marks a record as 
  expected to fail validation
- Records without `!` are expected to pass validation
- This allows tests to verify correct valid/invalid counts without hardcoding or 
  duplicating transformer logic

## Tech Stack
- Python / pytest
- pytest-check for soft assertions
- SQLite (built-in)
- GitHub Actions CI/CD

## Running the Tests
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `pytest`

## CI
Tests run automatically on every push via GitHub Actions.