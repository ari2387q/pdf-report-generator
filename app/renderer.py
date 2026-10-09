import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from playwright.async_api import async_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import DB_PATH
from app.report_data import get_report_data

REPORTS_DIR = ROOT_DIR / "reports"


def generate_html_template(data: Dict[str, Any], title: str = "Executive Sales Performance Report") -> str:
    today_str = datetime.now().strftime("%B %d, %Y - %H:%M:%S")
    summary = data.get("summary", {})
    top_products = data.get("top_products", [])
    orders_per_day = data.get("orders_per_day", [])
    all_orders = data.get("all_orders", [])

    total_revenue = summary.get("total_revenue", 0.0)

    # Top products table rows
    top_products_rows = "".join(
        f"""
        <tr>
            <td class="font-medium">{idx + 1}. {p['product']}</td>
            <td class="text-right">{p['order_count']}</td>
            <td class="text-right font-semibold">${p['revenue']:,.2f}</td>
            <td class="text-right text-muted">{(p['revenue'] / total_revenue * 100) if total_revenue > 0 else 0:.1f}%</td>
        </tr>
        """
        for idx, p in enumerate(top_products)
    )

    # Orders per day table rows
    daily_rows = "".join(
        f"""
        <tr>
            <td>{d['date']}</td>
            <td class="text-right">{d['order_count']}</td>
            <td class="text-right font-semibold">${d['daily_revenue']:,.2f}</td>
        </tr>
        """
        for d in orders_per_day
    )

    # All orders long table rows (200 rows)
    all_orders_rows = "".join(
        f"""
        <tr>
            <td class="text-muted">#{order['id']}</td>
            <td>{order['created_at']}</td>
            <td class="font-medium">{order['customer']}</td>
            <td>{order['product']}</td>
            <td class="text-right font-semibold">${order['amount']:,.2f}</td>
        </tr>
        """
        for order in all_orders
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        @page {{
            size: A4;
            margin: 16mm 14mm 18mm 14mm;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #1f2937;
            background: #ffffff;
            font-size: 9.5pt;
            line-height: 1.4;
            padding: 0;
        }}

        .report-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-bottom: 2px solid #2563eb;
            padding-bottom: 12px;
            margin-bottom: 16px;
        }}

        .brand-title {{
            font-size: 20pt;
            font-weight: 800;
            color: #1e3a8a;
            letter-spacing: -0.5px;
        }}

        .report-subtitle {{
            font-size: 9pt;
            color: #4b5563;
            margin-top: 2px;
        }}

        .meta-box {{
            text-align: right;
            font-size: 8.5pt;
            color: #6b7280;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}

        .metric-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px 14px;
        }}

        .metric-label {{
            font-size: 8pt;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #64748b;
            margin-bottom: 4px;
        }}

        .metric-value {{
            font-size: 16pt;
            font-weight: 700;
            color: #0f172a;
        }}

        .section-title {{
            font-size: 11pt;
            font-weight: 700;
            color: #1e293b;
            margin: 16px 0 8px 0;
            border-left: 3px solid #2563eb;
            padding-left: 8px;
        }}

        .two-column {{
            display: grid;
            grid-template-columns: 3fr 2fr;
            gap: 16px;
            margin-bottom: 16px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8.5pt;
            page-break-inside: auto;
        }}

        thead {{
            display: table-header-group;
        }}

        thead tr {{
            background-color: #f1f5f9;
            border-top: 1px solid #cbd5e1;
            border-bottom: 2px solid #94a3b8;
        }}

        th {{
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: #334155;
            font-size: 8pt;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}

        tbody tr {{
            border-bottom: 1px solid #e2e8f0;
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        tbody tr:nth-child(even) {{
            background-color: #fafafa;
        }}

        td {{
            padding: 5px 8px;
            vertical-align: middle;
        }}

        .text-right {{ text-align: right; }}
        .font-medium {{ font-weight: 500; }}
        .font-semibold {{ font-weight: 600; }}
        .text-muted {{ color: #64748b; }}

        .footer-note {{
            margin-top: 16px;
            padding-top: 8px;
            border-top: 1px solid #e2e8f0;
            font-size: 7.5pt;
            color: #94a3b8;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <div>
            <div class="brand-title">FlyRank Commerce</div>
            <div class="report-subtitle">{title}</div>
        </div>
        <div class="meta-box">
            <div><strong>Generated:</strong> {today_str}</div>
            <div><strong>Status:</strong> Official Audit Snapshot</div>
        </div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Total Orders</div>
            <div class="metric-value">{summary.get('total_orders', 0):,}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Revenue</div>
            <div class="metric-value">${summary.get('total_revenue', 0.0):,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Average Order Value</div>
            <div class="metric-value">${summary.get('average_order_value', 0.0):,.2f}</div>
        </div>
    </div>

    <div class="two-column">
        <div>
            <div class="section-title">Top 5 Products by Revenue</div>
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th class="text-right">Orders</th>
                        <th class="text-right">Revenue</th>
                        <th class="text-right">Share</th>
                    </tr>
                </thead>
                <tbody>
                    {top_products_rows}
                </tbody>
            </table>
        </div>
        <div>
            <div class="section-title">Last 7 Days Activity</div>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th class="text-right">Orders</th>
                        <th class="text-right">Revenue</th>
                    </tr>
                </thead>
                <tbody>
                    {daily_rows}
                </tbody>
            </table>
        </div>
    </div>

    <div class="section-title">Complete Transaction Ledger ({len(all_orders)} Records)</div>
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">ID</th>
                <th style="width: 22%;">Timestamp</th>
                <th style="width: 28%;">Customer</th>
                <th style="width: 28%;">Product</th>
                <th style="width: 12%;" class="text-right">Amount</th>
            </tr>
        </thead>
        <tbody>
            {all_orders_rows}
        </tbody>
    </table>

    <div class="footer-note">
        Confidential Report • Generated automatically by FlyRank PDF Report Engine • Page break avoided rows & repeated header certified
    </div>
</body>
</html>
"""
    return html


async def render_pdf_from_html(html_content: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={
                "top": "16mm",
                "bottom": "18mm",
                "left": "14mm",
                "right": "14mm",
            },
        )
        await browser.close()
    return output_path


async def generate_report_pdf(db_path: Path = DB_PATH, output_path: Path = REPORTS_DIR / "test.pdf") -> Path:
    data = get_report_data(db_path)
    html = generate_html_template(data)
    return await render_pdf_from_html(html, output_path)
