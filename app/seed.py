import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import DB_PATH, get_db_connection, init_db

PRODUCTS = [
    "Mechanical Keyboard",
    "Wireless Mouse",
    "USB-C Multiport Hub",
    "27-inch 4K Monitor",
    "Noise-Cancelling Headphones",
    "Ergonomic Desk Mat",
]

CUSTOMERS = [
    "Alice Smith",
    "Bob Johnson",
    "Carol Williams",
    "David Brown",
    "Emma Jones",
    "Frank Miller",
    "Grace Davis",
    "Henry Wilson",
    "Ivy Martinez",
    "Jack Taylor",
    "Katherine Anderson",
    "Liam Thomas",
]


def seed_database(db_path: Path = DB_PATH, count: int = 200) -> int:
    init_db(db_path)
    rng = random.Random(42)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Safe to run twice: clean previous entries first
        cursor.execute("DELETE FROM orders;")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='orders';")
        except sqlite3.OperationalError:
            pass

        now = datetime.now()
        orders = []

        for _ in range(count):
            customer = rng.choice(CUSTOMERS)
            product = rng.choice(PRODUCTS)
            amount = round(rng.uniform(5.0, 200.0), 2)
            seconds_ago = rng.randint(0, 30 * 24 * 3600)
            created_at = (now - timedelta(seconds=seconds_ago)).strftime("%Y-%m-%d %H:%M:%S")
            orders.append((customer, product, amount, created_at))

        cursor.executemany(
            """
            INSERT INTO orders (customer, product, amount, created_at)
            VALUES (?, ?, ?, ?);
            """,
            orders,
        )
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM orders;")
        total_rows = cursor.fetchone()[0]
        return total_rows


if __name__ == "__main__":
    rows_first = seed_database()
    print(f"First seed run: {rows_first} orders inserted.")
    rows_second = seed_database()
    print(f"Second seed run: {rows_second} orders verified.")
    print(f"CHECKPOINT: SELECT COUNT(*) -> {rows_second} orders in {DB_PATH}")
