from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]   # pasifik-panel/
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "normalized"

Z_BRANDS = RAW / "zeroteknik" / "brands.json"
Z_MODELS = RAW / "zeroteknik" / "models-by-brand.json"

S_PRODUCTS = RAW / "solobu" / "products-by-brand.json"
S_BRANDS = RAW / "solobu" / "brands-led-tv.json"   # optional


# ------------------------------------------------------------
# Project Rules
# ------------------------------------------------------------
FEATURED_BRANDS = [
    "philips", "samsung", "lg", "grundig", "beko", "arcelik",
    "telefunken", "tcl", "blaupunkt", "sony", "vestel"
]

TV_ONLY_RULE = True  # roadmap: sadece TV


MODEL_TOKEN_RE = re.compile(r"\b([A-Z0-9]{3,}[A-Z0-9\/\-]{0,})\b")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def read_json(p: Path) -> Any:
    """
    Bazı TR sitelerinden gelen json dosyaları UTF-8 değil (cp1254 vb.) olabiliyor.
    Bu yüzden birkaç encoding deneyip ilk başarılıyı kullanıyoruz.
    """
    encodings = ["utf-8", "utf-8-sig", "cp1254", "latin-1"]
    last_err = None
    for enc in encodings:
        try:
            txt = p.read_text(encoding=enc)
            return json.loads(txt)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"JSON read failed for {p}. Last error: {last_err}")


def write_json(p: Path, data: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def slugify_tr(text: str) -> str:
    m = str.maketrans({
        "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
        "Ç": "c", "Ğ": "g", "İ": "i", "Ö": "o", "Ş": "s", "Ü": "u",
    })
    t = str(text).translate(m).strip().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t


def extract_models_from_solobu_title(title: str) -> List[str]:
    tokens = MODEL_TOKEN_RE.findall((title or "").upper())

    bad = {
        "LED", "TV", "EKRAN", "PANEL", "DEGISIMI", "DEĞİŞİMİ", "DEGİSİMİ",
        "INCH", "INC", "EKRANI", "KODU", "KATALOGU", "KATALOĞU"
    }

    out: List[str] = []
    for t in tokens:
        t2 = t.strip("()[]{}:,.")
        if len(t2) < 4:
            continue
        if t2 in bad:
            continue
        if re.fullmatch(r"\d{1,3}", t2):
            continue
        if t2.startswith("HTTP"):
            continue
        out.append(t2)

    seen = set()
    uniq = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def debug_print_exists(p: Path) -> str:
    if p.exists():
        return f"YES ({p.stat().st_size} bytes)"
    return "NO"


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main() -> None:
    print("=== Pasifik Display Normalize (offline) ===")
    print(f"Project root: {ROOT}")
    print(f"RAW folder  : {RAW}")
    print(f"OUT folder  : {OUT}")
    print()

    print("FILES:")
    print("Z_BRANDS  :", Z_BRANDS, "->", debug_print_exists(Z_BRANDS))
    print("Z_MODELS  :", Z_MODELS, "->", debug_print_exists(Z_MODELS))
    print("S_PRODUCTS:", S_PRODUCTS, "->", debug_print_exists(S_PRODUCTS))
    print("S_BRANDS  :", S_BRANDS, "->", debug_print_exists(S_BRANDS), "(optional)")
    print()

    if not Z_BRANDS.exists() or not Z_MODELS.exists() or not S_PRODUCTS.exists():
        raise SystemExit("❌ Raw dosyalar bulunamadı. data/raw/ altında yolları kontrol et.")

    z_brands = read_json(Z_BRANDS)
    z_models_by_brand = read_json(Z_MODELS)
    s_products_by_brand = read_json(S_PRODUCTS)

    print("TYPES:")
    print("z_brands type:", type(z_brands), "len:", (len(z_brands) if hasattr(z_brands, "__len__") else "n/a"))
    print("z_models_by_brand type:", type(z_models_by_brand))
    if isinstance(z_models_by_brand, dict):
        print("z_models_by_brand keys:", len(z_models_by_brand.keys()))
    print("s_products_by_brand type:", type(s_products_by_brand))
    if isinstance(s_products_by_brand, dict):
        print("s_products_by_brand keys:", len(s_products_by_brand.keys()))
    print()

    if not isinstance(z_brands, list):
        raise SystemExit("❌ zeroteknik/brands.json beklenen formatta değil (list olmalı).")
    if not isinstance(z_models_by_brand, dict):
        raise SystemExit("❌ zeroteknik/models-by-brand.json beklenen formatta değil (dict olmalı).")
    if not isinstance(s_products_by_brand, dict):
        raise SystemExit("❌ solobu/products-by-brand.json beklenen formatta değil (dict olmalı).")

    z_brand_map: Dict[str, Dict[str, Any]] = {}
    for b in z_brands:
        if isinstance(b, dict) and "slug" in b:
            z_brand_map[str(b["slug"])] = b

    solobu_models_by_brand: Dict[str, Set[str]] = {}
    solobu_product_urls_by_brand: Dict[str, List[str]] = {}

    for brand_slug, items in s_products_by_brand.items():
        models: Set[str] = set()
        urls: List[str] = []

        if not isinstance(items, list):
            continue

        for it in items:
            if not isinstance(it, dict):
                continue
            url = str(it.get("url", "") or "")
            title = str(it.get("title", "") or "")

            if "/urun/" not in url:
                continue

            urls.append(url)

            for m in extract_models_from_solobu_title(title):
                models.add(m)

        solobu_models_by_brand[str(brand_slug)] = models
        solobu_product_urls_by_brand[str(brand_slug)] = urls

    all_brand_slugs = set(z_brand_map.keys()) | set(s_products_by_brand.keys())
    print("BRANDS UNION:", len(all_brand_slugs), "brands found")
    if len(all_brand_slugs) == 0:
        raise SystemExit("❌ Brand listesi 0 çıktı. Raw dosyaların içeriği boş veya format farklı.")

    models_out_by_brand: Dict[str, List[Dict[str, Any]]] = {}

    for slug in sorted(all_brand_slugs):
        z_list = z_models_by_brand.get(slug, [])
        if not isinstance(z_list, list):
            z_list = []

        s_set = solobu_models_by_brand.get(slug, set())
        if not isinstance(s_set, set):
            s_set = set()

        merged: Dict[str, Dict[str, Any]] = {}

        for mc in z_list:
            mc = str(mc).strip()
            if not mc:
                continue
            merged[mc] = {"sources": {"zeroteknik": True, "solobu": False}}

        for mc in sorted(s_set):
            mc = str(mc).strip()
            if not mc:
                continue
            if mc in merged:
                merged[mc]["sources"]["solobu"] = True
            else:
                merged[mc] = {
                    "sources": {"zeroteknik": False, "solobu": True},
                    "note": "Solobu başlığından otomatik çıkarım"
                }

        out_list: List[Dict[str, Any]] = []
        for mc, obj in merged.items():
            out_list.append({
                "id": f"{slug}:{mc}",
                "brandId": slug,
                "modelCode": mc,
                "slug": f"{slug}-{slugify_tr(mc)}",
                "screenType": "tv" if TV_ONLY_RULE else "unknown",
                **obj
            })

        out_list.sort(key=lambda x: (not x["sources"]["zeroteknik"], x["modelCode"]))
        models_out_by_brand[slug] = out_list

    brands_out: List[Dict[str, Any]] = []
    for slug in sorted(all_brand_slugs):
        z = z_brand_map.get(slug)
        name = z.get("name") if isinstance(z, dict) else None
        if not name:
            name = slug.replace("-", " ").title()

        brands_out.append({
            "id": slug,
            "slug": slug,
            "name": name,
            "modelCount": len(models_out_by_brand.get(slug, [])),
            "isFeatured": slug in FEATURED_BRANDS,
            "sources": {
                "zeroteknik": bool(z),
                "solobu": slug in s_products_by_brand
            }
        })

    if len(brands_out) == 0:
        raise SystemExit("❌ brands_out boş çıktı. Script raw datayı okuyamıyor veya union 0.")

    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "brands.json", brands_out)
    write_json(OUT / "models-by-brand.json", models_out_by_brand)
    write_json(OUT / "solobu-product-urls-by-brand.json", solobu_product_urls_by_brand)

    print()
    print("OK ✅")
    print(f"- {OUT / 'brands.json'}  (brands: {len(brands_out)})")
    print(f"- {OUT / 'models-by-brand.json'}  (brands: {len(models_out_by_brand)})")
    print(f"- {OUT / 'solobu-product-urls-by-brand.json'}")
    print()
    print("NOTE: Bu proje runtime'da solobu/zeroteknik'e BAĞIMLI DEĞİLDİR.")
    print("      Bu dosyalar sadece offline normalize çıktısı üretmek içindir.")


if __name__ == "__main__":
    main()
