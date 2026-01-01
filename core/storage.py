import json
from pathlib import Path
from datetime import datetime

def save_json(result: dict, out_dir: str = "data/results") -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"invoice_{ts}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)
