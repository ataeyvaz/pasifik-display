"""
build_search_index.py
=====================
Arama motoru için statik JSON index üretir.
Çıktı: public/search-index.json

Kullanım:
  python scripts/build_search_index.py
"""

import json, os, re

INPUT_FILE  = "data/normalized/models-by-brand.json"
OUTPUT_FILE = "public/search-index.json"

BRAND_DISPLAY_NAMES = {
    "altus":        "Altus",
    "arcelik":      "Arçelik",
    "awox":         "Awox",
    "axen":         "Axen",
    "beko":         "Beko",
    "blaupunkt":    "Blaupunkt",
    "botech":       "Botech",
    "daewoo":       "Daewoo",
    "delta":        "Delta",
    "dextel":       "Dextel",
    "digipoll":     "Digipoll",
    "dijitsu":      "Dijitsu",
    "dijitv":       "DijiTV",
    "dikom":        "Dikom",
    "dreamstar":    "Dreamstar",
    "eas":          "EAS",
    "electromaster":"ElectroMaster",
    "elton":        "Elton",
    "fenoti":       "Fenoti",
    "finlux":       "Finlux",
    "fivo":         "Fivo",
    "fobem":        "Fobem",
    "goldmaster":   "Goldmaster",
    "grundig":      "Grundig",
    "hello":        "Hello",
    "hi-level":     "Hi-Level",
    "hisense":      "Hisense",
    "hitachi":      "Hitachi",
    "hyundai":      "Hyundai",
    "jameson":      "Jameson",
    "jvc":          "JVC",
    "kamosonic":    "Kamosonic",
    "keysmart":     "Keysmart",
    "lg":           "LG",
    "luxor":        "Luxor",
    "morio":        "Morio",
    "navitech":     "Navitech",
    "nexon":        "Nexon",
    "next":         "Next",
    "nordmende":    "Nordmende",
    "olimpia":      "Olimpia",
    "onvo":         "Onvo",
    "panasonic":    "Panasonic",
    "peaq":         "PEAQ",
    "philips":      "Philips",
    "piranha":      "Piranha",
    "practica":     "Practica",
    "premier":      "Premier",
    "preo":         "Preo",
    "profilo":      "Profilo",
    "quax":         "Quax",
    "redline":      "Redline",
    "regal":        "Regal",
    "rose":         "Rose",
    "rowell":       "Rowell",
    "saba":         "Saba",
    "samsung":      "Samsung",
    "seg":          "SEG",
    "sharp":        "Sharp",
    "sheen":        "Sheen",
    "simfer":       "Simfer",
    "skytech":      "Skytech",
    "sony":         "Sony",
    "strong":       "Strong",
    "sungate":      "Sungate",
    "sunny":        "Sunny",
    "tcl":          "TCL",
    "teba":         "Teba",
    "techwood":     "Techwood",
    "telefox":      "Telefox",
    "telefunken":   "Telefunken",
    "telenova":     "Telenova",
    "toshiba":      "Toshiba",
    "ventus":       "Ventus",
    "vestel":       "Vestel",
    "vox":          "Vox",
    "weston":       "Weston",
    "woon":         "Woon",
    "xiaomi":       "Xiaomi",
    "yumatu":       "Yumatu",
}


def extract_screen_size(model_code):
    mc = model_code.upper()
    m = re.match(r'^(\d{2,3})', mc)
    if m:
        size = int(m.group(1))
        if 19 <= size <= 100:
            return str(size)
    return None


def build_index(data):
    index = []
    for brand_slug, models in data.items():
        # Marka adı: önce BRAND_DISPLAY_NAMES'e bak, yoksa slug'dan türet
        brand_name = BRAND_DISPLAY_NAMES.get(
            brand_slug,
            brand_slug.replace("-", " ").title()
        )

        for m in models:
            mc   = (m.get("modelCode") or "").strip()
            slug = (m.get("slug") or "").strip()

            if not mc or not slug:
                continue

            size = extract_screen_size(mc)
            url  = f"/markalar/{brand_slug}/{slug}/"

            entry = {
                "modelCode":  mc,
                "modelLower": mc.lower(),
                "brand":      brand_name,
                "brandSlug":  brand_slug,
                "slug":       slug,
                "url":        url,
            }
            if size:
                entry["size"] = size

            index.append(entry)

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

    total  = len(index)
    brands = len(set(e["brandSlug"] for e in index))
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"✅ search-index.json olusturuldu")
    print(f"   {total} model, {brands} marka, {size_kb:.1f} KB")


if __name__ == "__main__":
    main()