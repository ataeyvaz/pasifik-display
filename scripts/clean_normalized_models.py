# scripts/clean_normalized_models.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT / "data" / "normalized"

MODELS_BY_BRAND_PATH = NORMALIZED_DIR / "models-by-brand.json"
BRANDS_PATH = NORMALIZED_DIR / "brands.json"

# Açıkça çöp olduğunu bildiğimiz slug/modelCode değerleri
INVALID_EXACT_SLUGS = {
    "kvkk",
    "4654",
    "6698",
    "cookie-policy",
    "privacy-policy",
    "gizlilik-politikasi",
    "kullanim-kosullari",
    "mesafeli-satis-sozlesmesi",
    "cerez-politikasi",
}

# İçinde bunlar geçiyorsa direkt çöpe at
INVALID_CONTAINS = [
    "kvkk",
    "cookie",
    "privacy",
    "gizlilik",
    "kullanim",
    "cerez",
    "mesafeli",
    "sozlesme",
    "policy",
]

# Sadece sayılardan oluşan ve çok kısa olanlar büyük ihtimalle model değil
INVALID_NUMERIC_ONLY = {
    "4654",
    "6698",
}

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_bad_slug(slug: str) -> bool:
    slug = (slug or "").strip().lower()

    if not slug:
        return True

    # Tam eşleşen çöpler
    if slug in INVALID_EXACT_SLUGS:
        return True

    # brand-kvkk / samsung-kvkk gibi
    for bad in INVALID_CONTAINS:
        if bad in slug:
            return True

    # Sadece rakam ve çok kısa / bilinen kanun numarası
    if slug.isdigit() and slug in INVALID_NUMERIC_ONLY:
        return True

    return False

def is_bad_model_code(model_code: str) -> bool:
    model_code = (model_code or "").strip().lower()

    if not model_code:
        return True

    if model_code in INVALID_EXACT_SLUGS:
        return True

    for bad in INVALID_CONTAINS:
        if bad in model_code:
            return True

    if model_code.isdigit() and model_code in INVALID_NUMERIC_ONLY:
        return True

    return False

def clean_models_by_brand(models_by_brand: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, list[dict[str, Any]]], list[tuple[str, str, str]]]:
    cleaned: dict[str, list[dict[str, Any]]] = {}
    removed: list[tuple[str, str, str]] = []

    for brand_slug, models in models_by_brand.items():
        brand_cleaned: list[dict[str, Any]] = []

        for model in models:
            slug = str(model.get("slug", "")).strip()
            model_code = str(model.get("modelCode", "")).strip()

            if is_bad_slug(slug) or is_bad_model_code(model_code):
                removed.append((brand_slug, model_code, slug))
                continue

            brand_cleaned.append(model)

        cleaned[brand_slug] = brand_cleaned

    return cleaned, removed

def refresh_brand_counts(brands: list[dict[str, Any]], models_by_brand: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    for brand in brands:
        slug = brand.get("slug")
        if slug:
            brand["modelCount"] = len(models_by_brand.get(slug, []))
    return brands

def main() -> None:
    if not MODELS_BY_BRAND_PATH.exists():
        raise FileNotFoundError(f"Bulunamadı: {MODELS_BY_BRAND_PATH}")

    models_by_brand = load_json(MODELS_BY_BRAND_PATH)
    brands = load_json(BRANDS_PATH) if BRANDS_PATH.exists() else []

    before_total = sum(len(v) for v in models_by_brand.values())

    cleaned_models_by_brand, removed = clean_models_by_brand(models_by_brand)
    after_total = sum(len(v) for v in cleaned_models_by_brand.values())

    if brands:
        brands = refresh_brand_counts(brands, cleaned_models_by_brand)
        save_json(BRANDS_PATH, brands)

    save_json(MODELS_BY_BRAND_PATH, cleaned_models_by_brand)

    print(f"Önceki toplam model sayısı : {before_total}")
    print(f"Sonraki toplam model sayısı: {after_total}")
    print(f"Silinen kayıt sayısı       : {len(removed)}")
    print()

    if removed:
        print("Silinen örnek kayıtlar:")
        for brand_slug, model_code, slug in removed[:100]:
            print(f"- {brand_slug}: modelCode='{model_code}' slug='{slug}'")
    else:
        print("Silinecek kayıt bulunamadı.")

if __name__ == "__main__":
    main()