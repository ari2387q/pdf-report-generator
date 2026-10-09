"""
AI-generated alternative implementation (Quarantined comparison version).
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright

app = FastAPI(title="AI Version - Report Generator")
DB_PATH = Path("report.db")
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

class ReportRequest(BaseModel):
    force: bool = False

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/reports")
async def create_report(req: ReportRequest = ReportRequest()):
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        c = conn.cursor()
        if not req.force:
            c.execute("SELECT id FROM reports WHERE created_at LIKE ? ORDER BY id DESC LIMIT 1", (f"{today}%",))
            row = c.fetchone()
            if row:
                return JSONResponse(status_code=status.HTTP_200_OK, content={"id": row["id"], "file": f"/reports/{row['id']}/file"})

        # Fetch aggregates
        c.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM orders")
        tot_cnt, tot_rev = c.fetchone()
        c.execute("SELECT product, SUM(amount) as rev FROM orders GROUP BY product ORDER BY rev DESC LIMIT 5")
        top_prod = c.fetchall()
        c.execute("SELECT id, customer, product, amount, created_at FROM orders ORDER BY created_at DESC")
        orders = c.fetchall()

        # Insert record
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO reports (path, created_at) VALUES (?, ?)", ("pending", now))
        report_id = c.lastrowid
        pdf_path = REPORTS_DIR / f"{report_id}.pdf"

        # Simple HTML template
        rows_html = "".join(f"<tr><td>{o['id']}</td><td>{o['customer']}</td><td>{o['product']}</td><td>${o['amount']}</td></tr>" for o in orders)
        html = f"""
        <html>
        <head><style>table {{ width: 100%; border-collapse: collapse; }} tr {{ break-inside: avoid; }} thead {{ display: table-header-group; }}</style></head>
        <body>
            <h1>Sales Report</h1>
            <p>Orders: {tot_cnt} | Revenue: ${tot_rev:.2f}</p>
            <table><thead><tr><th>ID</th><th>Customer</th><th>Product</th><th>Amount</th></tr></thead><tbody>{rows_html}</tbody></table>
        </body>
        </html>
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html)
            await page.pdf(path=str(pdf_path), format="A4")
            await browser.close()

        c.execute("UPDATE reports SET path = ? WHERE id = ?", (str(pdf_path), report_id))
        conn.commit()

        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"id": report_id, "file": f"/reports/{report_id}/file"})

@app.get("/reports/{id}")
def get_report(id: int):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, path, created_at FROM reports WHERE id = ?", (id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return dict(row)

@app.get("/reports/{id}/file")
def get_file(id: int):
    pdf = REPORTS_DIR / f"{id}.pdf"
    if not pdf.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(pdf), media_type="application/pdf")
