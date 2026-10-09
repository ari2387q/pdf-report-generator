import sys
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import DB_PATH, get_db_connection
from app.main import app

def run_test():
    client = TestClient(app)
    
    # Clean previous reports for clean test
    with get_db_connection(DB_PATH) as conn:
        conn.cursor().execute("DELETE FROM reports;")
        conn.commit()
    reports_dir = ROOT_DIR / "reports"
    for f in reports_dir.glob("*.pdf"):
        f.unlink()
        
    initial_files = list(reports_dir.glob("*.pdf"))
    print(f"Initial PDF files in reports/: {len(initial_files)}")

    # 1. First POST request -> Should generate new report (201 Created)
    res1 = client.post("/reports")
    print(f"1st POST status: {res1.status_code}, data: {res1.json()}")
    assert res1.status_code == 201
    id1 = res1.json()["id"]
    files_after_1 = list(reports_dir.glob("*.pdf"))
    assert len(files_after_1) == 1

    # 2. Second POST request (rapid duplicate) -> Should return cached report (200 OK)
    res2 = client.post("/reports")
    print(f"2nd POST status: {res2.status_code}, data: {res2.json()}")
    assert res2.status_code == 200
    id2 = res2.json()["id"]
    files_after_2 = list(reports_dir.glob("*.pdf"))
    assert id1 == id2, f"Expected same report id, got {id1} vs {id2}"
    assert len(files_after_2) == 1, f"Expected exactly 1 file, found {len(files_after_2)}"

    # 3. Third POST request with { "force": true } -> Should generate new report (201 Created)
    res3 = client.post("/reports", json={"force": True})
    print(f"3rd POST (forced) status: {res3.status_code}, data: {res3.json()}")
    assert res3.status_code == 201
    id3 = res3.json()["id"]
    files_after_3 = list(reports_dir.glob("*.pdf"))
    assert id3 != id1, f"Expected new id on force, got {id3}"
    assert len(files_after_3) == 2, f"Expected 2 files after forced generation, found {len(files_after_3)}"

    print("\nStage 5 Checkpoint Passed: Idempotency verified. Same request returns identical id and produces no duplicate files; force=true generates new report.")

if __name__ == "__main__":
    run_test()
