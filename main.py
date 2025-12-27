from ocr_cli import ocr_tsv
from layout_parser import parse_invoice_layout_A
from storage import save_json

def process_image(image_path: str):
    tsv = ocr_tsv(image_path)
    result = parse_invoice_layout_A(tsv)
    out_path = save_json(result)
    return result, out_path

def main(image_paths):
    all_results = []
    for img in image_paths:
        print(f"\nProcessing: {img}")
        result, out = process_image(img)
        print(result)
        print(f"Saved to: {out}")
        all_results.append(result)

    return all_results

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py <img1> <img2> ...")
        raise SystemExit(1)

    main(sys.argv[1:])
