import csv
import io
import re
from typing import List, Dict, Any, Optional, Tuple


NUM_RE = re.compile(r"^\d+[.,]?\d*$")          # 5 or 5,00 or 5.00
DATE_RE = re.compile(r"\b\d{2}/\d{2}/\d{4}\b") # 04/13/2013
INVNO_RE = re.compile(r"\b\d{6,}\b")           # 51109338


# ---------------- TSV -> WORDS ----------------

def read_tsv(tsv_text: str) -> List[Dict[str, Any]]:
    words = []
    reader = csv.DictReader(io.StringIO(tsv_text), delimiter="\t")
    for row in reader:
        text = (row.get("text") or "").strip()
        conf = row.get("conf")
        if not text:
            continue
        if conf in ("-1", "", None):
            continue
        try:
            words.append({
                "text": text,
                "left": int(row["left"]),
                "top": int(row["top"]),
                "width": int(row["width"]),
                "height": int(row["height"]),
                "conf": float(conf),
            })
        except Exception:
            continue
    return words


def page_bounds(words: List[Dict[str, Any]]) -> Tuple[int, int]:
    max_x = 0
    max_y = 0
    for w in words:
        max_x = max(max_x, w["left"] + w["width"])
        max_y = max(max_y, w["top"] + w["height"])
    return max_x, max_y


# ---------------- WORDS -> ROWS (Y clustering) ----------------

def cluster_rows(words: List[Dict[str, Any]], y_tol: int = 10) -> List[Dict[str, Any]]:
    """
    Groups words into 'rows' using top coordinate.
    Each row contains:
      - top (representative y)
      - words sorted by x
      - text concatenated
      - min_left / max_left
    """
    ws = sorted(words, key=lambda w: (w["top"], w["left"]))
    rows: List[Dict[str, Any]] = []

    for w in ws:
        placed = False
        for r in rows:
            if abs(w["top"] - r["top"]) <= y_tol:
                r["words"].append(w)
                placed = True
                break
        if not placed:
            rows.append({"top": w["top"], "words": [w]})

    for r in rows:
        r["words"].sort(key=lambda w: w["left"])
        r["text"] = " ".join(w["text"] for w in r["words"])
        r["min_left"] = min(w["left"] for w in r["words"])
        r["max_left"] = max(w["left"] for w in r["words"])
    rows.sort(key=lambda r: r["top"])
    return rows


# ---------------- Helpers ----------------

def find_row_index(rows: List[Dict[str, Any]], contains: str) -> Optional[int]:
    needle = contains.lower()
    for i, r in enumerate(rows):
        if needle in r["text"].lower():
            return i
    return None


def find_word_x(row: Dict[str, Any], target: str) -> Optional[int]:
    t = target.lower()
    for w in row["words"]:
        if w["text"].lower() == t:
            return w["left"]
    return None


def clean_num(s: str) -> str:
    # handle "1 394,67" -> "1394.67" partially if joined later
    s = s.replace(" ", "")
    s = s.replace(",", ".")
    return s


def extract_invoice_number_and_date(rows: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    inv = None
    date = None
    for r in rows[:40]:  # top area only
        low = r["text"].lower()
        if inv is None and "invoice" in low:
            m = INVNO_RE.search(r["text"])
            if m:
                inv = m.group()
        if date is None and "date" in low:
            m = DATE_RE.search(r["text"])
            if m:
                date = m.group()
        if inv and date:
            break
    return inv, date


def extract_seller(rows: List[Dict[str, Any]]) -> Optional[str]:
    """
    Robust seller extraction for your layout:
    - Find the row containing 'Seller:'
    - Next rows: pick first line whose words are mostly on LEFT side (avoid client)
    - Stop at 'Tax Id' or 'IBAN' or 'ITEMS'
    """
    idx = find_row_index(rows, "Seller")
    if idx is None:
        return None

    # determine column split using "Client" row if available
    client_idx = find_row_index(rows, "Client")
    split_x = None
    if client_idx is not None:
        # midpoint between Seller label and Client label words
        seller_x = rows[idx]["min_left"]
        client_x = rows[client_idx]["min_left"]
        if client_x > seller_x:
            split_x = (seller_x + client_x) / 2

    # fallback split_x: use page width heuristic only as fallback
    if split_x is None:
        # roughly half page based on observed row widths
        page_w = max(r["max_left"] for r in rows)
        split_x = page_w * 0.5

    # scan next few rows for left-column company name
    for j in range(idx + 1, min(idx + 10, len(rows))):
        t = rows[j]["text"].strip()
        low = t.lower()
        if not t:
            continue
        if "tax id" in low or "iban" in low or "items" in low:
            break

        # keep only words left of split_x
        left_words = [w["text"] for w in rows[j]["words"] if w["left"] < split_x]
        candidate = " ".join(left_words).strip()
        if candidate:
            # usually first line is the company name
            return candidate

    return None


def extract_items(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Table-aware item extraction:
    - Find 'ITEMS' row (start)
    - Find 'SUMMARY' row (end)
    - Find header row with 'Description' and 'Qty' inside that region
    - Use header word positions to define column boundaries
    - For each row cluster below header:
        * description = words in Description column region
        * qty = first numeric-ish word in Qty column region
        * merge continuation lines that don’t have qty
    """
    start_i = find_row_index(rows, "ITEMS")
    end_i = find_row_index(rows, "SUMMARY")
    if start_i is None:
        return []
    if end_i is None:
        end_i = len(rows)

    region = rows[start_i:end_i]

    # find header row containing both Description and Qty
    header_idx = None
    for i, r in enumerate(region[:20]):
        low = r["text"].lower()
        if "description" in low and "qty" in low:
            header_idx = i
            break
    if header_idx is None:
        return []

    header = region[header_idx]
    desc_x = find_word_x(header, "Description")
    qty_x = find_word_x(header, "Qty")

    if desc_x is None or qty_x is None:
        return []

    # define column regions:
    # description column = from desc_x - small padding to just before qty_x
    desc_min = max(0, desc_x - 30)
    desc_max = qty_x - 10

    # qty column = around qty_x
    qty_min = qty_x - 40
    qty_max = qty_x + 80

    items: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for r in region[header_idx + 1:]:
        txt = r["text"].strip()
        if not txt:
            continue

        # ignore obvious non-item table separators
        low = txt.lower()
        if "net price" in low and "vat" in low:
            continue

        # extract qty from qty column
        qty_candidates = [w["text"] for w in r["words"] if qty_min <= w["left"] <= qty_max]
        qty_value = None
        for qc in qty_candidates:
            # accept 5,00 / 5.00 / 5
            if NUM_RE.match(qc.replace(" ", "")):
                qty_value = clean_num(qc)
                break

        # extract description from description column
        desc_words = [w["text"] for w in r["words"] if desc_min <= w["left"] <= desc_max]
        desc_text = " ".join(desc_words).strip()

        # if this row has a qty and some description -> new item
        if qty_value and desc_text:
            current = {"description": desc_text, "quantity": qty_value}
            items.append(current)
            continue

        # continuation line: no qty, but has desc -> append to previous item
        if current and (not qty_value) and desc_text:
            current["description"] += " " + desc_text

    return items


def parse_invoice_layout_A(tsv_text: str) -> Dict[str, Any]:
    words = read_tsv(tsv_text)
    if not words:
        return {"invoice_number": None, "date": None, "seller": None, "items": []}

    rows = cluster_rows(words)

    inv, date = extract_invoice_number_and_date(rows)
    seller = extract_seller(rows)
    items = extract_items(rows)

    return {
        "invoice_number": inv,
        "date": date,
        "seller": seller,
        "items": items
    }
