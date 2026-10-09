import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import DB_PATH, get_db_connection, init_db
from app.renderer import generate_report_pdf, REPORTS_DIR

# Ensure database tables and reports directory are ready
init_db(DB_PATH)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="FlyRank PDF Report Generator")


class GenerateReportRequest(BaseModel):
    force: Optional[bool] = False


@app.on_event("startup")
def on_startup():
    init_db(DB_PATH)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/reports")
async def generate_report(request: Optional[GenerateReportRequest] = None):
    force = request.force if request else False
    today_prefix = datetime.now().strftime("%Y-%m-%d")

    with get_db_connection(DB_PATH) as conn:
        cursor = conn.cursor()

        # Idempotency Check: if not forced, return existing report generated today
        if not force:
            cursor.execute(
                """
                SELECT id, path, created_at FROM reports
                WHERE created_at LIKE ? AND path != 'pending'
                ORDER BY id DESC
                LIMIT 1;
                """,
                (f"{today_prefix}%",),
            )
            existing = cursor.fetchone()
            if existing:
                pdf_path = Path(existing["path"])
                if pdf_path.exists():
                    # Return 200 OK with existing report details
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content={
                            "id": existing["id"],
                            "file": f"/reports/{existing['id']}/file",
                            "cached": True,
                        },
                    )

        # Fresh generation required (first run of day or forced)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO reports (path, created_at) VALUES (?, ?);",
            ("pending", now_str),
        )
        conn.commit()
        report_id = cursor.lastrowid

        pdf_filename = f"{report_id}.pdf"
        pdf_path = REPORTS_DIR / pdf_filename

        # Render PDF via Playwright
        await generate_report_pdf(db_path=DB_PATH, output_path=pdf_path)

        # Update report path in database
        cursor.execute(
            "UPDATE reports SET path = ? WHERE id = ?;",
            (str(pdf_path), report_id),
        )
        conn.commit()

        # Return 201 Created for new generation
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": report_id,
                "file": f"/reports/{report_id}/file",
                "cached": False,
            },
        )


@app.get("/reports")
def list_reports():
    with get_db_connection(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, path, created_at FROM reports ORDER BY id DESC;")
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "path": row["path"],
                "created_at": row["created_at"],
                "file": f"/reports/{row['id']}/file",
            }
            for row in rows
        ]


@app.get("/reports/{report_id}")
def get_report_meta(report_id: int):
    with get_db_connection(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, path, created_at FROM reports WHERE id = ?;",
            (report_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")

        return {
            "id": row["id"],
            "path": row["path"],
            "created_at": row["created_at"],
            "file": f"/reports/{row['id']}/file",
        }


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    with get_db_connection(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, path FROM reports WHERE id = ?;",
            (report_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")

        file_path = Path(row["path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found on disk")

        return FileResponse(
            path=str(file_path),
            media_type="application/pdf",
            filename=f"sales-report-{report_id}.pdf",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
