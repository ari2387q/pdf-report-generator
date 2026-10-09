import asyncio
import sys
from pathlib import Path
from pypdf import PdfReader

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.renderer import generate_report_pdf, REPORTS_DIR

async def main():
    test_pdf_path = REPORTS_DIR / "test.pdf"
    print(f"Rendering PDF report to {test_pdf_path}...")
    await generate_report_pdf(output_path=test_pdf_path)
    
    assert test_pdf_path.exists(), f"PDF file not found at {test_pdf_path}"
    file_size_kb = test_pdf_path.stat().st_size / 1024
    print(f"Generated PDF file size: {file_size_kb:.2f} KB")
    
    # Verify page count
    reader = PdfReader(str(test_pdf_path))
    num_pages = len(reader.pages)
    print(f"Total pages generated: {num_pages}")
    
    assert num_pages >= 2, f"Expected at least 2 pages, got {num_pages}"
    print(f"Stage 3 Checkpoint Passed: {test_pdf_path} successfully generated with {num_pages} pages.")

if __name__ == "__main__":
    asyncio.run(main())
