import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import DB_PATH, get_db_connection


def get_report_data(db_path: Path = DB_PATH) -> Dict[str, Any]:
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Total number of orders
        cursor.execute("SELECT COUNT(*) AS total_orders FROM orders;")
        total_orders = cursor.fetchone()["total_orders"]

        # 2. Total revenue
        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) AS total_revenue FROM orders;")
        total_revenue = round(float(cursor.fetchone()["total_revenue"]), 2)

        # 3. Top 5 products by revenue
        cursor.execute(
            """
            SELECT product, COUNT(*) AS order_count, ROUND(SUM(amount), 2) AS revenue
            FROM orders
            GROUP BY product
            ORDER BY revenue DESC
            LIMIT 5;
            """
        )
        top_products = [
            {
                "product": row["product"],
                "order_count": row["order_count"],
                "revenue": float(row["revenue"]),
            }
            for row in cursor.fetchall()
        ]

        # 4. Orders per day for the last 7 days
        cursor.execute(
            """
            SELECT date(created_at) AS order_date, COUNT(*) AS order_count, ROUND(SUM(amount), 2) AS daily_revenue
            FROM orders
            GROUP BY date(created_at)
            ORDER BY order_date DESC
            LIMIT 7;
            """
        )
        orders_per_day = [
            {
                "date": row["order_date"],
                "order_count": row["order_count"],
                "daily_revenue": float(row["daily_revenue"]),
            }
            for row in cursor.fetchall()
        ]

        # Detailed item records (used for full report table)
        cursor.execute(
            """
            SELECT id, customer, product, amount, created_at
            FROM orders
            ORDER BY created_at DESC;
            """
        )
        all_orders = [
            {
                "id": row["id"],
                "customer": row["customer"],
                "product": row["product"],
                "amount": float(row["amount"]),
                "created_at": row["created_at"],
            }
            for row in cursor.fetchall()
        ]

        return {
            "summary": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "average_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0,
            },
            "top_products": top_products,
            "orders_per_day": orders_per_day,
            "all_orders": all_orders,
        }


# Alias matching the camelCase naming in the specification
getReportData = get_report_data


if __name__ == "__main__":
    data = get_report_data()
    # Print 4 key sections without the long list for clean inspection
    inspect_data = {
        "summary": data["summary"],
        "top_products": data["top_products"],
        "orders_per_day": data["orders_per_day"],
        "total_detailed_orders": len(data["all_orders"]),
    }
    print(json.dumps(inspect_data, indent=2))
