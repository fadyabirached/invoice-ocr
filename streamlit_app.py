import streamlit as st
import pandas as pd
from ocr_cli import ocr_tsv
from layout_parser import parse_invoice_layout_A
from storage import save_json
from pathlib import Path

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="ChristBot",
    layout="wide"
)

# =========================================================
# GLOBAL STYLES (DARK SAAS THEME)
# =========================================================
st.markdown("""
<style>

/* ===============================
   COLOR SYSTEM
================================ */
:root {
    --bg-main: #0b0f19;
    --bg-card: #131a2a;
    --bg-input: #0f172a;
    --border-subtle: #263043;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --accent: #3b82f6;
}

/* App background */
.stApp {
    background-color: var(--bg-main);
    color: var(--text-primary);
}

/* Headings */
h1, h2, h3, h4 {
    color: var(--text-primary);
    font-weight: 600;
}

/* Captions / labels */
label, .stCaption {
    color: var(--text-secondary);
}

/* File uploader */
[data-testid="stFileUploader"] {
    background-color: var(--bg-card);
    border: 1px dashed var(--border-subtle);
    padding: 1.4rem;
    border-radius: 16px;
}

/* Invoice card */
.invoice-card {
    background-color: var(--bg-card);
    padding: 1.6rem;
    border-radius: 18px;
    margin-bottom: 2.2rem;
    border: 1px solid var(--border-subtle);
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
}

/* Inputs */
.stTextInput input {
    background-color: var(--bg-input);
    border-radius: 10px;
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
}

/* Data editor */
[data-testid="stDataEditor"] {
    background-color: var(--bg-input);
    border-radius: 14px;
    border: 1px solid var(--border-subtle);
}

/* Buttons */
.stButton button {
    background: linear-gradient(90deg, #3b82f6, #2563eb);
    color: white;
    border-radius: 12px;
    padding: 0.65rem 1.7rem;
    font-weight: 600;
    border: none;
    box-shadow: 0 6px 18px rgba(59,130,246,0.35);
}

.stButton button:hover {
    background: linear-gradient(90deg, #2563eb, #1e40af);
}

/* Divider */
hr {
    border-color: var(--border-subtle);
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.title("📄 ChristBot — Invoice Data Entry MVP")
st.caption("Upload invoices • Auto-extract data • Fix errors • Save structured JSON")
st.markdown("---")

# =========================================================
# FILE UPLOADER
# =========================================================
uploaded_files = st.file_uploader(
    "Upload up to 5 invoice images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

# =========================================================
# MAIN LOGIC
# =========================================================
if uploaded_files:
    for file in uploaded_files[:5]:

        # ---------- Invoice Card ----------
        st.markdown('<div class="invoice-card">', unsafe_allow_html=True)
        st.subheader(f"🧾 {file.name}")

        # Save uploaded image temporarily
        img_path = Path(file.name)
        img_path.write_bytes(file.read())

        # OCR + Parsing
        with st.spinner("Running OCR and parsing invoice..."):
            tsv = ocr_tsv(str(img_path))
            result = parse_invoice_layout_A(tsv)

        # ---------- Metadata ----------
        col1, col2, col3 = st.columns(3)
        with col1:
            seller = st.text_input(
                "Seller",
                result.get("seller", ""),
                key=f"s_{file.name}"
            )
        with col2:
            invoice_number = st.text_input(
                "Invoice Number",
                result.get("invoice_number", ""),
                key=f"i_{file.name}"
            )
        with col3:
            date = st.text_input(
                "Invoice Date",
                result.get("date", ""),
                key=f"d_{file.name}"
            )

        # ---------- Line Items ----------
        st.markdown("#### Line Items")
        df = pd.DataFrame(result.get("items", []))
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key=f"t_{file.name}"
        )

        # ---------- Save ----------
        col_left, col_right = st.columns([6, 1])
        with col_right:
            if st.button("💾 Save", key=f"save_{file.name}"):
                final = {
                    "seller": seller,
                    "invoice_number": invoice_number,
                    "date": date,
                    "items": edited_df.to_dict(orient="records")
                }
                out = save_json(final)
                st.success(f"Saved → {out}")

        st.markdown('</div>', unsafe_allow_html=True)
