import subprocess
from pathlib import Path
import shutil
import os

# ---------------------------------------------------------
# Locate Tesseract in a portable + Windows-safe way
# ---------------------------------------------------------
def find_tesseract() -> str | None:
    # 1️⃣ Try PATH (Linux, Mac, CI, Streamlit Cloud)
    path = shutil.which("tesseract")
    if path:
        return path

    # 2️⃣ Common Windows install locations
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for p in possible_paths:
        if os.path.exists(p):
            return p

    return None


TESSERACT_PATH = find_tesseract()

if TESSERACT_PATH is None:
    raise EnvironmentError(
        "Tesseract OCR not found.\n"
        "Install it from: https://github.com/UB-Mannheim/tesseract/wiki\n"
        "Or add tesseract.exe to your PATH."
    )


# ---------------------------------------------------------
# OCR function
# ---------------------------------------------------------
def ocr_tsv(image_path: str) -> str:
    img = Path(image_path)
    if not img.exists():
        raise FileNotFoundError(f"Image not found: {img.resolve()}")

    out_base = img.parent / img.stem

    subprocess.run(
        [
            TESSERACT_PATH,
            str(img),
            str(out_base),
            "--oem", "3",
            "--psm", "6",
            "tsv",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    tsv_path = out_base.with_suffix(".tsv")
    return tsv_path.read_text(encoding="utf-8", errors="ignore")
