"""
normalize_all.py  v6
====================
raw/solobu/ + raw/zeroteknik/ → data/normalized/

Temizlik:
  - source_url'de marka slug'u geçmiyorsa → sidebar kalıntısı → sil
  - Çöp model kodları → sil
  - İki kaynaktan gelen aynı model → birleştir (sources alanına işaretle)
"""

import json, os, re

SOLOBU_DIR   = "raw/solobu"
ZERO_DIR     = "raw/zeroteknik"
OUT_DIR      = "data/normalized"

JUNK_WORDS = ["kvkk", "privacy", "cookie", "policy", "gdpr", "kanun", "aydinlatma"]
JUNK_EXACT = {"yeni", "yeni!", "kampanya", "indirim", "stok", "new"}
MIN_LEN    = 3


def is_junk(mc):
    s = mc.strip()
    if not s:                    return True
    if len(s) < MIN_LEN:        return True
    if s.isdigit():              return True
    if s.lower() in JUNK_EXACT: return True
    for j in JUNK_WORDS:
        if j in s.lower():      return True
    return False


def model_slug(brand_slug, mc):
    s = mc.lower().replace("/", "-").replace(" ", "-").replace(".", "-")
    return f"{brand_slug}-{s}"


def load_source(directory, source_name):
    """Bir kaynaktan tüm marka dosyalarını oku."""
    result = {}  # brand_slug → list of items
    if not os.path.exists(directory):
        return result

    for fn in sorted(os.listdir(directory)):
        if fn == "brands.json" or not fn.endswith(".json"):
            continue
        brand_slug = fn.replace(".json", "")
        with open(os.path.join(directory, fn), encoding="utf-8") as f:
            items = json.load(f)

        clean = []
        for item in items:
            mc         = (item.get("model_code") or "").strip()
            source_url = item.get("source_url", "").lower()

            # source_url filtresi — sidebar temizliği
            if source_url and f"/urun/{brand_slug}-" not in source_url \
               and f"/markalar/{brand_slug}/" not in source_url:
                continue

            if is_junk(mc):
                continue

            clean.append({
                "brand":      item.get("brand", brand_slug.title()),
                "brand_slug": brand_slug,
                "model_code": mc,
                "model_slug": item.get("model_slug") or model_slug(brand_slug, mc),
                "source":     source_name,
            })

        if clean:
            if brand_slug not in result:
                result[brand_slug] = []
            result[brand_slug].extend(clean)

    return result


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Her iki kaynağı yükle
    solobu_data = load_source(SOLOBU_DIR, "solobu")
    zero_data   = load_source(ZERO_DIR,   "zeroteknik")

    print(f"Solobu    : {sum(len(v) for v in solobu_data.values())} model, {len(solobu_data)} marka")
    print(f"Zeroteknik: {sum(len(v) for v in zero_data.values())} model, {len(zero_data)} marka")

    # Tüm markaları birleştir
    all_brands = set(solobu_data.keys()) | set(zero_data.keys())
    brands_out      = {}
    models_by_brand = {}

    for brand_slug in sorted(all_brands):
        solobu_items = solobu_data.get(brand_slug, [])
        zero_items   = zero_data.get(brand_slug, [])

        brand_display = (
            (solobu_items or zero_items)[0].get("brand", brand_slug.title())
            if (solobu_items or zero_items) else brand_slug.title()
        )

        # Model kodlarını merge et
        merged = {}  # mc_upper → entry

        for item in solobu_items:
            mc = item["model_code"]
            key = mc.upper()
            if key not in merged:
                merged[key] = {
                    "id":         f"{brand_slug}:{mc}",
                    "brandSlug":  brand_slug,
                    "modelCode":  mc,
                    "slug":       item["model_slug"],
                    "screenType": "tv",
                    "sources":    {"solobu": True, "zeroteknik": False},
                }
            else:
                merged[key]["sources"]["solobu"] = True

        for item in zero_items:
            mc = item["model_code"]
            key = mc.upper()
            if key not in merged:
                merged[key] = {
                    "id":         f"{brand_slug}:{mc}",
                    "brandSlug":  brand_slug,
                    "modelCode":  mc,
                    "slug":       item["model_slug"],
                    "screenType": "tv",
                    "sources":    {"solobu": False, "zeroteknik": True},
                }
            else:
                merged[key]["sources"]["zeroteknik"] = True

        model_list = list(merged.values())

        if model_list:
            models_by_brand[brand_slug] = model_list
            brands_out[brand_slug] = {
                "slug":       brand_slug,
                "name":       brand_display,
                "modelCount": len(model_list),
            }

    # Yaz
    brands_list = sorted(brands_out.values(), key=lambda x: x["name"].lower())
    with open(os.path.join(OUT_DIR, "brands.json"), "w", encoding="utf-8") as f:
        json.dump(brands_list, f, ensure_ascii=False, indent=2)

    with open(os.path.join(OUT_DIR, "models-by-brand.json"), "w", encoding="utf-8") as f:
        json.dump(models_by_brand, f, ensure_ascii=False, indent=2)

    total    = sum(len(v) for v in models_by_brand.values())
    only_sol = sum(1 for ms in models_by_brand.values()
                   for m in ms if m["sources"]["solobu"] and not m["sources"]["zeroteknik"])
    only_zer = sum(1 for ms in models_by_brand.values()
                   for m in ms if not m["sources"]["solobu"] and m["sources"]["zeroteknik"])
    both     = sum(1 for ms in models_by_brand.values()
                   for m in ms if m["sources"]["solobu"] and m["sources"]["zeroteknik"])

    print(f"\n✅ Normalize tamamlandı!")
    print(f"   Markalar          : {len(brands_out)}")
    print(f"   Toplam model      : {total}")
    print(f"   Sadece solobu'da  : {only_sol}")
    print(f"   Sadece zeroteknik : {only_zer}")
    print(f"   Her ikisinde de   : {both}")
    print(f"\nSonraki adım: python scripts/build_search_index.py")


if __name__ == "__main__":
    main()