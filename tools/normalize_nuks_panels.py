# tools/normalize_nuks_panels.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Set

ROOT = Path(__file__).resolve().parents[1]
RAW_ITEMS = ROOT / "data" / "raw" / "nuks" / "items.json"

OUT_PANELS = ROOT / "data" / "normalized" / "panels.json"
OUT_MAP = ROOT / "data" / "normalized" / "model-panel-map.json"

PANEL_TOKEN_RE = re.compile(r"\b[A-Z0-9][A-Z0-9\-_/]{4,}\b")

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def normalize_panel_code(s: str) -> str:
    s = (s or "").strip().upper().replace("_", "-")
    s = re.sub(r"\s+", "", s)
    return s

def normalize_model_code(s: str) -> str:
    s = (s or "").strip().upper()
    s = re.sub(r"\s+", "", s)
    return s

def main():
    if not RAW_ITEMS.exists():
        print("ERR: items.json not found:", RAW_ITEMS)
        return

    items = read_json(RAW_ITEMS)

    panels_index: Dict[str, Dict] = {}
    mapping: Dict[str, Dict[str, List[str]]] = {}  # brand -> modelCode -> [panelCodes]

    for it in items:
        brand = str(it.get("brand") or "").strip()
        model_code = normalize_model_code(str(it.get("modelCode") or ""))

        raw_panels = it.get("panels") or []
        # bazen parse listesi boşsa yine de title/description içinde token olabilir
        if (not raw_panels) and it.get("title"):
            raw_panels = PANEL_TOKEN_RE.findall(str(it.get("title")).upper())

        panel_codes = [normalize_panel_code(p) for p in raw_panels if p]
        panel_codes = sorted({p for p in panel_codes if any(ch.isdigit() for ch in p) and len(p) >= 6})

        if not brand or not model_code:
            continue
        if not panel_codes:
            continue

        mapping.setdefault(brand, {})
        mapping[brand].setdefault(model_code, [])
        # merge unique
        merged = set(mapping[brand][model_code])
        merged.update(panel_codes)
        mapping[brand][model_code] = sorted(merged)

        # panels index (basit)
        for pc in panel_codes:
            if pc not in panels_index:
                panels_index[pc] = {
                    "code": pc,
                    "source": "nuks",
                    "seenInBrands": sorted({brand}),
                }
            else:
                seen = set(panels_index[pc].get("seenInBrands") or [])
                seen.add(brand)
                panels_index[pc]["seenInBrands"] = sorted(seen)

    panels_out = [panels_index[k] for k in sorted(panels_index.keys())]

    write_json(OUT_PANELS, panels_out)
    write_json(OUT_MAP, mapping)

    print("OK ✅")
    print("-", OUT_PANELS, f"(panels: {len(panels_out)})")
    print("-", OUT_MAP, f"(mappings: {sum(len(v) for v in mapping.values())})")
    print("\nNOTE: Runtime'da NUKS'a BAĞIMLILIK YOK (offline normalize çıktısı).")

if __name__ == "__main__":
    main()