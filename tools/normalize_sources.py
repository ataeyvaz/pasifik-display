# tools/normalize_sources.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "normalized"

Z_BRANDS = RAW / "zeroteknik" / "brands.json"
Z_MODELS = RAW / "zeroteknik" / "models-by-brand.json"
S_PRODUCTS = RAW / "solobu" / "products-by-brand.json"
S_BRANDS = RAW / "solobu" / "brands-led-tv.json"  # optional


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        # ✅ Windows mojibake fix: always read UTF-8
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # ✅ ensure_ascii=False -> TR karakterler bozulmaz
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def slugify(s: str) -> str:
    # basit slug (senin slug kuralların varsa onu burada kullan)
    s = s.strip().lower()
    repl = {
        "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
        " ": "-", "/": "-", "_": "-", ".": "-", ",": "-", "&": "and",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def main() -> None:
    print("=== Pasifik Display Normalize (offline) ===")
    print("Project root:", ROOT)
    print("RAW folder  :", RAW)
    print("OUT folder  :", OUT)
    print()

    print("FILES:")
    print("Z_BRANDS  :", Z_BRANDS, "->", "YES" if Z_BRANDS.exists() else "NO",
          f"({Z_BRANDS.stat().st_size} bytes)" if Z_BRANDS.exists() else "")
    print("Z_MODELS  :", Z_MODELS, "->", "YES" if Z_MODELS.exists() else "NO",
          f"({Z_MODELS.stat().st_size} bytes)" if Z_MODELS.exists() else "")
    print("S_PRODUCTS:", S_PRODUCTS, "->", "YES" if S_PRODUCTS.exists() else "NO",
          f"({S_PRODUCTS.stat().st_size} bytes)" if S_PRODUCTS.exists() else "")
    print("S_BRANDS  :", S_BRANDS, "->", "YES" if S_BRANDS.exists() else "NO",
          f"({S_BRANDS.stat().st_size} bytes) (optional)" if S_BRANDS.exists() else "(optional)")
    print()

    z_brands = read_json(Z_BRANDS, [])
    z_models_by_brand = read_json(Z_MODELS, {})
    s_products_by_brand = read_json(S_PRODUCTS, {})
    s_brands = read_json(S_BRANDS, [])

    print("TYPES:")
    print("z_brands type:", type(z_brands), "len:", (len(z_brands) if hasattr(z_brands, "__len__") else "n/a"))
    print("z_models_by_brand type:", type(z_models_by_brand),
          "keys:", (len(z_models_by_brand.keys()) if isinstance(z_models_by_brand, dict) else "n/a"))
    print("s_products_by_brand type:", type(s_products_by_brand),
          "keys:", (len(s_products_by_brand.keys()) if isinstance(s_products_by_brand, dict) else "n/a"))
    print()

    # ---- Brands union ----
    # z_brands: list of {name/slug?...}
    # s_brands: list or dict depending on your scraper; we treat as list with 'name'
    all_names: Dict[str, str] = {}

    def add_brand_name(name: str) -> None:
        if not name:
            return
        sl = slugify(name)
        if sl not in all_names:
            all_names[sl] = name

    if isinstance(z_brands, list):
        for b in z_brands:
            if isinstance(b, dict):
                add_brand_name(str(b.get("name") or b.get("brand") or b.get("title") or "").strip())
            elif isinstance(b, str):
                add_brand_name(b.strip())

    if isinstance(s_brands, list):
        for b in s_brands:
            if isinstance(b, dict):
                add_brand_name(str(b.get("name") or b.get("brand") or b.get("title") or "").strip())
            elif isinstance(b, str):
                add_brand_name(b.strip())

    # also include keys from models/products to not lose brands
    if isinstance(z_models_by_brand, dict):
        for k in z_models_by_brand.keys():
            add_brand_name(str(k))
    if isinstance(s_products_by_brand, dict):
        for k in s_products_by_brand.keys():
            add_brand_name(str(k))

    # Featured list (senin config'ine göre uyarlayabilirsin)
    featured = {slugify(x) for x in [
        "Philips", "Samsung", "LG", "Grundig", "Beko", "Arçelik",
        "Telefunken", "TCL", "Blaupunkt", "Sony", "Vestel"
    ]}

    brands_out: List[Dict[str, Any]] = []

    for sl, display_name in sorted(all_names.items(), key=lambda x: x[1].lower()):
        # modelCount: zeroteknik models + solobu products (TV-only zaten raw'ta filtreli varsayıyoruz)
        z_count = 0
        if isinstance(z_models_by_brand, dict):
            arr = z_models_by_brand.get(sl) or z_models_by_brand.get(display_name) or []
            if isinstance(arr, list):
                z_count = len(arr)

        s_count = 0
        if isinstance(s_products_by_brand, dict):
            arr = s_products_by_brand.get(sl) or s_products_by_brand.get(display_name) or []
            if isinstance(arr, list):
                s_count = len(arr)

        model_count = max(z_count, s_count) if (z_count or s_count) else 0

        brands_out.append({
            "id": sl,
            "slug": sl,
            "name": display_name,  # ✅ UTF-8 okuma + ensure_ascii=False ile bozulmaz
            "modelCount": model_count,
            "isFeatured": (sl in featured),
            "sources": {
                "zeroteknik": bool(z_count),
                "solobu": bool(s_count),
            }
        })

    print(f"BRANDS UNION: {len(brands_out)} brands found\n")

    # ---- models-by-brand normalize (minimal) ----
    # hedef: site runtime'ı local JSON'dan okusun; sources alanı opsiyonel
    models_out: Dict[str, List[Dict[str, Any]]] = {}

    if isinstance(z_models_by_brand, dict):
        for brand_key, models in z_models_by_brand.items():
            bslug = slugify(str(brand_key))
            if not isinstance(models, list):
                continue
            out_list = []
            for m in models:
                if isinstance(m, dict):
                    model_code = str(m.get("modelCode") or m.get("code") or m.get("model") or m.get("name") or "").strip()
                else:
                    model_code = str(m).strip()
                if not model_code:
                    continue
                out_list.append({
                    "id": f"{bslug}-{slugify(model_code)}",
                    "brandId": bslug,
                    "modelCode": model_code,
                    "slug": slugify(model_code),
                    "screenType": "tv",  # TV-only policy
                    "sources": {"zeroteknik": True}
                })
            models_out[bslug] = out_list

    # keep solobu url map (optional)
    solobu_url_map: Dict[str, Dict[str, str]] = {}
    if isinstance(s_products_by_brand, dict):
        for brand_key, items in s_products_by_brand.items():
            bslug = slugify(str(brand_key))
            if not isinstance(items, list):
                continue
            m = {}
            for it in items:
                if not isinstance(it, dict):
                    continue
                model = str(it.get("model") or it.get("modelCode") or it.get("title") or "").strip()
                url = str(it.get("url") or it.get("href") or "").strip()
                if model and url:
                    m[model] = url
            if m:
                solobu_url_map[bslug] = m

    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "brands.json", brands_out)
    write_json(OUT / "models-by-brand.json", models_out)
    write_json(OUT / "solobu-product-urls-by-brand.json", solobu_url_map)

    print("OK ✅")
    print("-", OUT / "brands.json", f" (brands: {len(brands_out)})")
    print("-", OUT / "models-by-brand.json", f" (brands: {len(models_out)})")
    print("-", OUT / "solobu-product-urls-by-brand.json")
    print()
    print("NOTE: Bu proje runtime'da solobu/zeroteknik'e BAĞIMLI DEĞİLDİR.")
    print("      Bu dosyalar sadece offline normalize çıktısı üretmek içindir.")


if __name__ == "__main__":
    main()