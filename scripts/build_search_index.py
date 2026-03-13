"""
build_search_index.py
=====================
Arama motoru için statik JSON index üretir.
Çıktı: public/search-index.json

Kullanım:
  python scripts/build_search_index.py

package.json'daki build komutunu şu şekilde güncelleyin:
  "build": "python scripts/build_search_index.py && astro build"
  "dev":   "python scripts/build_search_index.py && astro dev"
"""

import json
import os
import re

INPUT_FILE  = "data/normalized/models-by-brand.json"
OUTPUT_FILE = "public/search-index.json"

# Marka görünen adları
BRAND_DISPLAY_NAMES = {
    "arcelik":    "Arçelik",
    "awox":       "Awox",
    "axen":       "Axen",
    "beko":       "Beko",
    "blaupunkt":  "Blaupunkt",
    "botech":     "Botech",
    "finlux":     "Finlux",
    "grundig":    "Grundig",
    "hi-level":   "Hi-Level",
    "hisense":    "Hisense",
    "jvc":        "JVC",
    "lg":         "LG",
    "next":       "Next",
    "philips":    "Philips",
    "profilo":    "Profilo",
    "regal":      "Regal",
    "samsung":    "Samsung",
    "sony":       "Sony",
    "sunny":      "Sunny",
    "tcl":        "TCL",
    "telefunken": "Telefunken",
    "toshiba":    "Toshiba",
    "vestel":     "Vestel",
    "xiaomi":     "Xiaomi",
}

def extract_screen_size(model_code: str) -> str | None:
    """Model kodunun başından ekran boyutunu tahmin et (ilk 2-3 rakam)."""
    mc = model_code.upper()
    # Başındaki rakam bloğunu al (örn: "55" from "55A5K", "100" from "100ZD9")
    m = re.match(r'^(\d{2,3})', mc)
    if m:
        size = int(m.group(1))
        # Makul TV boyutları: 19–100 inç
        if 19 <= size <= 100:
            return str(size)
    return None

def build_index(data: dict) -> list:
    index = []
    for brand_slug, models in data.items():
        brand_name = BRAND_DISPLAY_NAMES.get(brand_slug, brand_slug.title())
        for m in models:
            mc   = m.get("modelCode", "").strip()
            slug = m.get("slug", "").strip()
            if not mc or not slug:
                continue

            size = extract_screen_size(mc)
            url  = f"/markalar/{brand_slug}/{slug}/"

            entry = {
                "modelCode":  mc,
                "modelLower": mc.lower(),   # hızlı prefix match için
                "brand":      brand_name,
                "brandSlug":  brand_slug,
                "slug":       slug,
                "url":        url,
            }
            if size:
                entry["size"] = size

            index.append(entry)

    # Model koduna göre sırala
    index.sort(key=lambda x: (x["brandSlug"], x["modelCode"]))
    return index

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Dosya bulunamadi: {INPUT_FILE}")
        return

    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    index = build_index(data)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    total = len(index)
    brands = len(set(e["brandSlug"] for e in index))
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"✅ search-index.json olusturuldu")
    print(f"   {total} model, {brands} marka, {size_kb:.1f} KB")

if __name__ == "__main__":
    main()