# tools/normalize_nuks_panels.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]

RAW_ITEMS = ROOT / "data" / "raw" / "nuks" / "items.json"
OUT_PANELS = ROOT / "data" / "normalized" / "panels.json"
OUT_MAP = ROOT / "data" / "normalized" / "model-panel-map.json"

def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def norm_panel_code(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.replace("_", "-")

def norm_model_code(s: str) -> str:
    return (s or "").strip().upper()

def main() -> None:
    items = read_json(RAW_ITEMS, [])

    panels_out: Dict[str, Dict[str, Any]] = {}
    map_out: Dict[str, List[str]] = {}

    for it in items:
        if not isinstance(it, dict):
            continue

        brand = (it.get("brand") or "").strip()
        product_url = (it.get("productUrl") or "").strip()
        stock_out = bool(it.get("stockOut"))

        panels = it.get("panels") or []
        models = it.get("models") or []

        if not isinstance(panels, list) or not isinstance(models, list):
            continue

        panels = [norm_panel_code(p) for p in panels if isinstance(p, str) and p.strip()]
        models = [norm_model_code(m) for m in models if isinstance(m, str) and m.strip()]

        # panel kayıtları
        for p in panels:
            pid = p.lower()
            if pid not in panels_out:
                panels_out[pid] = {
                    "id": pid,
                    "panelCode": p,
                    "source": "nuks",
                    "brandHint": brand,
                    "stockOutAtScrape": stock_out,
                    "exampleUrl": product_url,
                }

        # model -> panel map
        for m in models:
            if m not in map_out:
                map_out[m] = []
            for p in panels:
                if p not in map_out[m]:
                    map_out[m].append(p)

    write_json(OUT_PANELS, list(panels_out.values()))
    write_json(OUT_MAP, map_out)

    print("OK ✅")
    print("-", OUT_PANELS, f"(panels: {len(panels_out)})")
    print("-", OUT_MAP, f"(mappings: {len(map_out)})")
    print()
    print("NOTE: Runtime'da NUKS'a BAĞIMLILIK YOK (offline normalize çıktısı).")

if __name__ == "__main__":
    main()