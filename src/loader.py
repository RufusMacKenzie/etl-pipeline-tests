import sqlite3


def _create_orders_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        order_date DATE,
        product_id TEXT,
        quantity INTEGER,
        unit_price REAL,
        discount_amount REAL,
        order_total REAL,
        promo_code TEXT,
        status TEXT,
        previous_status TEXT,
        last_updated TIMESTAMP,
        email TEXT
    );
    """
    cursor.execute(create_table_query)


def create_schema(conn: sqlite3.Connection) -> None:
    _create_orders_table(conn)


def load(valid_records: list[dict], conn: sqlite3.Connection) -> int:
    if not valid_records:
        return 0

    cursor = conn.cursor()
    columns = ", ".join(valid_records[0].keys())
    placeholders = ", ".join(f":{k}" for k in valid_records[0].keys())
    cursor.executemany(
        f"INSERT OR REPLACE INTO orders ({columns}) VALUES ({placeholders})",
        valid_records,
    )
    return len(valid_records)
