import subprocess
from pathlib import Path

# Update if different on your machine
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_tsv(image_path: str) -> str:
    img = Path(image_path)
    if not img.exists():
        raise FileNotFoundError(f"Image not found: {img.resolve()}")

    out_base = img.with_suffix("")  # writes next to image: inv1.tsv

    subprocess.run(
        [
            TESSERACT_PATH,
            str(img),
            str(out_base),
            "--oem", "3",
            "--psm", "6",
            "tsv",
        ],
        check=True
    )
    tsv_path = out_base.with_suffix(".tsv")
    return tsv_path.read_text(encoding="utf-8", errors="ignore")
