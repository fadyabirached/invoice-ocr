import streamlit as st
import pandas as pd
from ocr_cli import ocr_tsv
from layout_parser import parse_invoice_layout_A
from storage import save_json
from pathlib import Path

st.set_page_config(layout="wide")
st.title("Invoice OCR – Human Review MVP")

uploaded_files = st.file_uploader(
    "Upload 1-5 invoice images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    for file in uploaded_files[:5]:
        st.divider()
        st.subheader(file.name)

        img_path = Path(file.name)
        img_path.write_bytes(file.read())

        tsv = ocr_tsv(str(img_path))
        result = parse_invoice_layout_A(tsv)

        col1, col2, col3 = st.columns(3)
        with col1:
            seller = st.text_input("Seller", result["seller"], key=f"s_{file.name}")
        with col2:
            invoice_number = st.text_input("Invoice Number", result["invoice_number"], key=f"i_{file.name}")
        with col3:
            date = st.text_input("Date", result["date"], key=f"d_{file.name}")

        df = pd.DataFrame(result["items"])
        edited_df = st.data_editor(df, num_rows="dynamic", key=f"t_{file.name}")

        if st.button(f"Save corrected – {file.name}"):
            final = {
                "seller": seller,
                "invoice_number": invoice_number,
                "date": date,
                "items": edited_df.to_dict(orient="records")
            }
            out = save_json(final)
            st.success(f"Saved to {out}")
