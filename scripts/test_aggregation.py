import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.report_data import get_report_data

if __name__ == "__main__":
    report_data = get_report_data()

    # Four core sections required by the assignment specification:
    output = {
        "total_orders": report_data["summary"]["total_orders"],
        "total_revenue": report_data["summary"]["total_revenue"],
        "top_products_by_revenue": report_data["top_products"],
        "orders_per_day_last_7_days": report_data["orders_per_day"],
    }

    print(json.dumps(output, indent=2))

    # Basic sanity checks
    assert output["total_orders"] == 200, f"Expected 200 orders, got {output['total_orders']}"
    assert output["total_revenue"] > 0, "Total revenue must be positive"
    assert len(output["top_products_by_revenue"]) <= 5, "Top products must have at most 5 items"
    assert len(output["orders_per_day_last_7_days"]) > 0, "Orders per day must not be empty"

    top_product_rev = sum(p["revenue"] for p in output["top_products_by_revenue"])
    assert top_product_rev <= output["total_revenue"] + 0.01, "Top product revenue sum cannot exceed total revenue"
    print("\nStage 2 Checkpoint Passed: Valid JSON with all 4 required sections and verified aggregations.")
