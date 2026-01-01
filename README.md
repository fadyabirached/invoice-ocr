# Geometric Invoice Parser

**A layout-specific invoice OCR and document parsing system utilizing Tesseract and coordinate-based layout analysis.**

## 📌 Project Overview

This system explores deterministic document parsing under OCR noise without reliance on Machine Learning or Large Language Models (LLMs). By treating document structure as a geometric problem, the system reconstructs rows, identifies table headers, and anchors column boundaries to achieve reliable extraction within a constrained layout scope.

The core objective is to demonstrate **coordinate-based document reconstruction**, emphasizing explainable logic and correctness over broad generalization.

## 🛠 Technology Stack

- **Language:** Python 3.10+
- **OCR Engine:** Tesseract OCR (TSV output mode)
- **Visualization:** Streamlit (Interactive demo)
- **Parsing Logic:** Standard library only (`csv`, `regex`, `pathlib`) — **Zero external parsing dependencies.**

## ⚙️ Parsing Pipeline

The system implements a transparent extraction pipeline that converts raw OCR data into structured JSON through the following heuristic geometry-driven approach:

1.  **OCR Execution:** Runs Tesseract in TSV mode to generate tokens with precise bounding box coordinates ($X, Y, Width, Height$).
2.  **Confidence Filtering:** Eliminates low-confidence noise from the OCR stream.
3.  **Row Clustering:** Groups words into logical lines based on Y-axis proximity and vertical tolerance.
4.  **Spatial Sorting:** Sorts clustered rows top-to-bottom, left-to-right.
5.  **Header Detection:** Locates the specific table header row to establish the document's coordinate reference frame.
6.  **Column Inference:** Calculates column boundaries based on the X-positions of header words.
7.  **Extraction & Merging:**
    - Iterates through item rows using calculated column bounds.
    - Merges multi-line descriptions into single logical items.
8.  **Serialization:** Emits the final state as structured JSON.

## 📂 System Components

```text
.
├── core/
│   ├── ocr_cli.py        # Wrapper for Tesseract; produces TSV with bounding boxes
│   ├── layout_parser.py  # Geometry engine: row clustering and column anchoring
│   ├── storage.py        # Persists parsed output to disk
│   └── main.py           # CLI entry point for batch processing
├── streamlit_app.py      # Interactive visualization dashboard
├── test/                 # Sample invoices used for validation
└── README.md
```
## 🚀 Usage
Prerequisites
Python 3.10+
Tesseract OCR installed and accessible via system PATH.
1. Installation
code
Bash
pip install -r requirements.txt
2. CLI Batch Processing
Run the deterministic parser on a specific image via the command line:
code
Bash
python core/main.py test/inv3.jpg
3. Interactive Visualization
Launch the Streamlit app to upload images, visualize the OCR bounding boxes, and inspect the JSON output in real-time.
code
Bash
streamlit run streamlit_app.py

## 📄 Output Format

The system produces a strict JSON schema containing metadata and tabular data:
```
{
  "invoice_number": "INV-1023",
  "date": "2023-10-15",
  "seller": "Acme Corp",
  "items": [
    {
      "description": "Consulting Services - Phase 1",
      "quantity": "10.0"
    },
    {
      "description": "Hardware Installation",
      "quantity": "2.0"
    }
  ]
}
```
## 🎯 Scope & Design Principles
This project is layout-specific by design. It prioritizes deep, correct understanding of a single template over shallow understanding of many.
### Supported Scope
Validated on sample templates: Works strictly with the invoice layout provided in the test/ directory.

Structured Tables: Assumes consistent column alignment and identifiable headers.

Digital/Clean Scans: Optimized for standard DPI document images.
### Design Principles
Deterministic Parsing: Same input always yields the same output. No stochastic ML behavior.

Explainable Failures: Every extraction error can be traced to a specific geometric calculation or OCR artifact.

Transparent Logic: The logic is inspectable; there are no "black box" neural networks.
### Limitations
Layout Scope: Does not support general invoice parsing or varying templates.
OCR Dependency: Extraction quality is directly correlated to Tesseract's raw output.
Handwriting: Out of scope.
