import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import streamlit as st
import tempfile

from core.ocr_cli import ocr_tsv
from core.layout_parser import parse_invoice_layout_A
from core.storage import save_json

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Invoice OCR",
    layout="wide"
)

st.title("📄 Invoice OCR & Layout-Based Parsing Demo")
st.caption("Layout-specific invoice OCR system (sample invoices only).")

st.divider()

uploaded_files = st.file_uploader(
    "Upload invoice images",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)


def process_image(uploaded_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / uploaded_file.name
        img_path.write_bytes(uploaded_file.getbuffer())

        # OCR
        tsv_text = ocr_tsv(str(img_path))

        # Parse
        result = parse_invoice_layout_A(tsv_text)

        # Save output (optional)
        out_path = save_json(result)

        return result, out_path


if uploaded_files:
    for file in uploaded_files:
        st.subheader(file.name)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(file, use_container_width=True)

        with col2:
            try:
                with st.spinner("Running OCR + parsing..."):
                    result, out_path = process_image(file)

                st.success("Done")

                st.markdown("### Parsed JSON")
                st.json(result)

                if result.get("items"):
                    st.markdown("### Extracted Items")
                    st.table(result["items"])
                else:
                    st.info("No line items detected.")

                st.caption(f"Saved to `{out_path}`")

            except Exception as e:
                st.error("Processing failed")
                st.code(str(e))

        st.divider()
else:
    st.info("Upload sample invoices from the test folder to see results.")
