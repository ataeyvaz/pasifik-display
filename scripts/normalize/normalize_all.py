from __future__ import annotations
import os
from typing import Dict, List, Any

from scripts._shared import read_json, write_json, tv_only_filter, make_slug, model_slug, normalize_panel_code

RAW_SOLOBU = "raw/solobu"
RAW_ZERO = "raw/zeroteknik"
OUT_DATA = "data"

def load_raw_files(folder: str) -> List[Any]:
    items = []
    if not os.path.exists(folder):
        return items
    for fn in os.listdir(folder):
        if fn.endswith(".json"):
            items.append(read_json(os.path.join(folder, fn)))
    return items

def build_brands(raw_sources: List[Any]) -> Dict[str, Dict]:
    """
    Expected raw item example (we'll adapt in scraper):
    { "brand": "Samsung", "brand_slug": "samsung", ... }
    """
    brands: Dict[str, Dict] = {}
    for blob in raw_sources:
        # blob can be list or dict depending on scraper
        rows = blob if isinstance(blob, list) else blob.get("items", [])
        for r in rows:
            name = (r.get("brand") or r.get("brand_name") or "").strip()
            if not name:
                continue
            slug = r.get("brand_slug") or make_slug(name)
            brands[slug] = {
                "slug": slug,
                "name": name,
                "modelCount": 0,
            }
    return brands

def build_models(raw_sources: List[Any], brands: Dict[str, Dict]) -> Dict[str, List[Dict]]:
    """
    Output per brand file: data/models/{brand}.json
    Canonical model record:
    {
      "slug": "samsung-ue55nu7100",
      "brandSlug": "samsung",
      "modelCode": "UE55NU7100",
      "screenSize": 55,
      "year": 2019,
      "panelCodes": ["LM550WF5-SSB3"]
    }
    """
    per_brand: Dict[str, List[Dict]] = {b: [] for b in brands.keys()}

    for blob in raw_sources:
        rows = blob if isinstance(blob, list) else blob.get("items", [])
        for r in rows:
            brand = (r.get("brand_slug") or "").strip()
            brand_name = (r.get("brand") or "").strip()
            if not brand and brand_name:
                brand = make_slug(brand_name)
            if not brand:
                continue
            if brand not in per_brand:
                # unknown brand → add dynamically
                per_brand[brand] = []
                if brand not in brands:
                    brands[brand] = {"slug": brand, "name": brand_name or brand, "modelCount": 0}

            model_code = (r.get("model_code") or r.get("model") or "").strip()
            if not model_code:
                continue

            # TV-only heuristic
            if not tv_only_filter(f"{brand_name} {model_code} {r.get('title','')}"):
                continue

            slug = r.get("model_slug") or model_slug(brand, model_code)
            screen_size = r.get("screen_size")
            year = r.get("year")

            panel_codes_raw = r.get("panel_codes") or r.get("panels") or []
            panel_codes = [normalize_panel_code(p) for p in panel_codes_raw if p]

            per_brand[brand].append({
                "slug": slug,
                "brandSlug": brand,
                "modelCode": model_code,
                "screenSize": screen_size,
                "year": year,
                "panelCodes": panel_codes,
            })
            brands[brand]["modelCount"] += 1

    return per_brand

def main():
    solobu = load_raw_files(RAW_SOLOBU)
    zero = load_raw_files(RAW_ZERO)
    raw_all = solobu + zero

    brands = build_brands(raw_all)
    models_by_brand = build_models(raw_all, brands)

    # write brands
    write_json(os.path.join(OUT_DATA, "brands.json"), sorted(brands.values(), key=lambda x: x["name"].lower()))

    # write models per brand
    out_models_dir = os.path.join(OUT_DATA, "models")
    os.makedirs(out_models_dir, exist_ok=True)
    for brand, items in models_by_brand.items():
        if not items:
            continue
        write_json(os.path.join(out_models_dir, f"{brand}.json"), items)

    print("✅ normalize done")
    print(f"- brands: {len(brands)}")
    print(f"- model files: {len([k for k,v in models_by_brand.items() if v])}")

if __name__ == "__main__":
    main()
