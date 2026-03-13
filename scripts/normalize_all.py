from __future__ import annotations
import os
import re
from typing import Dict, List, Any

from scripts._shared import read_json, write_json, tv_only_filter, make_slug, model_slug, normalize_panel_code

RAW_SOLOBU = "raw/solobu"
RAW_ZERO   = "raw/zeroteknik"
OUT_DATA   = "data"

# ── Veri Doğrulama Sabitleri ──────────────────────────────────────────────────

KNOWN_BRANDS = {
    "samsung", "lg", "philips", "sony", "vestel", "beko", "arcelik",
    "toshiba", "sharp", "panasonic", "grundig", "hitachi", "tcl",
    "telefunken", "blaupunkt", "hisense", "skyworth", "finlux",
    "regal", "profilo", "altus", "nordmende", "onvo",
}

JUNK_WORDS = [
    "kvkk", "privacy", "cookie", "policy", "gdpr",
    "4654", "6698", "kanun", "aydinlatma",
]

MIN_MODEL_LEN = 4

# ── Yardımcı Fonksiyonlar ─────────────────────────────────────────────────────

def load_raw_files(folder: str) -> List[Any]:
    items = []
    if not os.path.exists(folder):
        return items
    for fn in os.listdir(folder):
        if fn.endswith(".json"):
            items.append(read_json(os.path.join(folder, fn)))
    return items


def is_valid_model_code(brand_slug: str, model_code: str) -> tuple[bool, str]:
    """
    Model kodunun geçerli olup olmadığını kontrol eder.
    (True, "") geçerli → işleme al
    (False, sebep) geçersiz → atla
    """
    mc = model_code.strip()
    mc_lower = mc.lower()

    # Boş
    if not mc:
        return False, "boş model kodu"

    # Çok kısa
    if len(mc) < MIN_MODEL_LEN:
        return False, f"çok kısa ({len(mc)} karakter)"

    # Sadece rakam
    if mc.isdigit():
        return False, "sadece rakam"

    # Çöp kelime içeriyor mu?
    for junk in JUNK_WORDS:
        if junk in mc_lower:
            return False, f"çöp kelime: '{junk}'"

    # Marka adının kendisi model kodu olarak mı girilmiş?
    if mc_lower in KNOWN_BRANDS:
        return False, f"marka adı model kodu olarak: '{mc}'"

    return True, ""


# ── Pipeline Fonksiyonları ────────────────────────────────────────────────────

def build_brands(raw_sources: List[Any]) -> Dict[str, Dict]:
    brands: Dict[str, Dict] = {}
    for blob in raw_sources:
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
    per_brand: Dict[str, List[Dict]] = {b: [] for b in brands.keys()}
    skipped = 0

    for blob in raw_sources:
        rows = blob if isinstance(blob, list) else blob.get("items", [])
        for r in rows:
            brand      = (r.get("brand_slug") or "").strip()
            brand_name = (r.get("brand") or "").strip()

            if not brand and brand_name:
                brand = make_slug(brand_name)
            if not brand:
                continue

            if brand not in per_brand:
                per_brand[brand] = []
                if brand not in brands:
                    brands[brand] = {"slug": brand, "name": brand_name or brand, "modelCount": 0}

            model_code = (r.get("model_code") or r.get("model") or "").strip()

            # ── YENİ: Model kodu doğrulama ──
            valid, reason = is_valid_model_code(brand, model_code)
            if not valid:
                skipped += 1
                continue

            # TV-only filtresi
            if not tv_only_filter(f"{brand_name} {model_code} {r.get('title','')}"):
                skipped += 1
                continue

            slug         = r.get("model_slug") or model_slug(brand, model_code)
            screen_size  = r.get("screen_size")
            year         = r.get("year")

            panel_codes_raw = r.get("panel_codes") or r.get("panels") or []
            panel_codes     = [normalize_panel_code(p) for p in panel_codes_raw if p]

            per_brand[brand].append({
                "slug":       slug,
                "brandSlug":  brand,
                "modelCode":  model_code,
                "screenSize": screen_size,
                "year":       year,
                "panelCodes": panel_codes,
            })
            brands[brand]["modelCount"] += 1

    if skipped:
        print(f"⚠️  Doğrulama filtresi: {skipped} kayıt atlandı")

    return per_brand


def main():
    solobu  = load_raw_files(RAW_SOLOBU)
    zero    = load_raw_files(RAW_ZERO)
    raw_all = solobu + zero

    brands         = build_brands(raw_all)
    models_by_brand = build_models(raw_all, brands)

    # brands.json yaz
    write_json(
        os.path.join(OUT_DATA, "brands.json"),
        sorted(brands.values(), key=lambda x: x["name"].lower()),
    )

    # models/{brand}.json yaz
    out_models_dir = os.path.join(OUT_DATA, "models")
    os.makedirs(out_models_dir, exist_ok=True)
    for brand, items in models_by_brand.items():
        if not items:
            continue
        write_json(os.path.join(out_models_dir, f"{brand}.json"), items)

    total_models = sum(len(v) for v in models_by_brand.values() if v)
    print("✅ normalize tamamlandı")
    print(f"   Markalar : {len(brands)}")
    print(f"   Modeller : {total_models}")


if __name__ == "__main__":
    main()