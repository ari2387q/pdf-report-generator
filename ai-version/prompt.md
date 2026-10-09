# AI Rematch Prompt

Build a data-to-document backend pipeline in Python using FastAPI, SQLite, and Playwright Chromium.
1. Schema & Seed: Create a SQLite database 'report.db' with an 'orders' table (id, customer, product, amount, created_at) and a seed script inserting 200 random orders across 6 products over the last 30 days. Re-running the seed must leave exactly 200 clean rows.
2. Aggregation: Compute total orders, total revenue, top 5 products by revenue, and 7-day daily breakdown using SQL COUNT, SUM, and GROUP BY.
3. PDF Rendering: Generate an A4 PDF using Playwright Chromium with clean print CSS (avoid slicing table rows across page breaks using tr { break-inside: avoid; } and repeat thead headers across pages). Include both summaries and a full 200-row transaction ledger.
4. API Endpoints:
   - GET /health -> {"status": "ok"}
   - POST /reports -> Idempotent report generation. If a report was already created today, return 200 OK with the existing report link unless {"force": true} is passed. If new, render PDF to reports/<id>.pdf and return 201 Created with {"id": <id>, "file": "/reports/<id>/file"}.
   - GET /reports/:id -> Return report record metadata (404 if missing).
   - GET /reports/:id/file -> Serve PDF binary from disk using FileResponse.
