"""
scrape_zeroteknik.py  v2
========================
Model kodu URL'den alınır (temiz), sayfalama düzeltildi.

URL: zeroteknik.com/markalar/{brand}?page={n}
Model kodu: URL son segmenti → büyük harf
  /markalar/samsung/32t5300 → 32T5300
  /markalar/samsung/43ls05b-the-sero → 43LS05B (the-sero atılır)
"""

import json, os, re, time, requests
from bs4 import BeautifulSoup

BASE_URL  = "https://www.zeroteknik.com"
OUT_DIR   = "raw/zeroteknik"
DELAY     = 1.0
MAX_PAGES = 50

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9",
}

TV_BRANDS = [
    ("samsung",    "Samsung"),
    ("lg",         "LG"),
    ("sony",       "Sony"),
    ("philips",    "Philips"),
    ("vestel",     "Vestel"),
    ("arcelik",    "Arçelik"),
    ("beko",       "Beko"),
    ("grundig",    "Grundig"),
    ("toshiba",    "Toshiba"),
    ("hisense",    "Hisense"),
    ("tcl",        "TCL"),
    ("telefunken", "Telefunken"),
    ("panasonic",  "Panasonic"),
    ("sharp",      "Sharp"),
    ("finlux",     "Finlux"),
    ("regal",      "Regal"),
    ("profilo",    "Profilo"),
    ("altus",      "Altus"),
    ("nordmende",  "Nordmende"),
    ("sunny",      "Sunny"),
    ("next",       "Next"),
    ("axen",       "Axen"),
    ("awox",       "Awox"),
    ("hi-level",   "Hi-Level"),
    ("xiaomi",     "Xiaomi"),
    ("seg",        "SEG"),
    ("hitachi",    "Hitachi"),
]


def get(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code in (404, 410):
                return None
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"  ⚠️  Hata: {e} — {i+1}/{retries}")
            time.sleep(2)
    return None


def url_to_model_code(href, brand_slug):
    """
    /markalar/samsung/32t5300           → 32T5300
    /markalar/samsung/43ls05b-the-sero  → 43LS05B
    /markalar/lg/oled55c1               → OLED55C1
    """
    slug = href.rstrip("/").split("/")[-1]

    # "-the-sero", "-frame", "-serif" gibi marketing eklerini kaldır
    # Kural: model kodu rakam+harf karışımı, marketing eki sadece kelimelerden oluşur
    # Örn: "43ls05b-the-sero" → "43ls05b"
    parts = slug.split("-")
    # İlk parça rakamla başlıyorsa → model kodu o parça
    # Yoksa tüm slug model kodu
    model_parts = []
    for p in parts:
        # Eğer parça sadece harf (marketing eki) ve önceki parça zaten var → dur
        if model_parts and re.match(r'^[a-z]+$', p) and not re.match(r'^[a-z0-9]+$', parts[0]):
            break
        model_parts.append(p)
        # İlk parçadan sonra gelen alfanümerik olmayan ekler marketing olabilir
        if len(model_parts) >= 2 and re.match(r'^[a-z]+$', p):
            # "the", "sero", "frame" gibi kelimeler → dur
            if p in ("the", "frame", "serif", "sero", "flip", "fold", "pro", "plus", "ultra"):
                model_parts.pop()
                break

    model_slug = "-".join(model_parts)
    return model_slug.upper().replace("-", "").strip()[:20]  # max 20 char


def scrape_brand(brand_slug, brand_display):
    models = []
    seen   = set()
    total_pages = None

    for page in range(1, MAX_PAGES + 1):
        url = f"{BASE_URL}/markalar/{brand_slug}"
        if page > 1:
            url += f"?page={page}"

        r = get(url)
        if not r:
            break

        soup = BeautifulSoup(r.text, "html.parser")

        # Toplam sayfa sayısını bul (ilk sayfada)
        if total_pages is None:
            text = soup.get_text()
            m = re.search(r'Sayfa\s+\d+\s*/\s*(\d+)', text)
            if m:
                total_pages = int(m.group(1))
            else:
                total_pages = 1

        # Model linklerini bul
        pattern = f"/markalar/{brand_slug}/"
        page_items = []

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")

            # Sadece model sayfaları: /markalar/samsung/32t5300
            if not href.startswith(pattern):
                continue
            # Marka sayfasının kendisi değil
            if href.rstrip("/") == f"/markalar/{brand_slug}":
                continue
            # ?page= parametresi içermesin
            if "?page=" in href:
                continue

            full_url = BASE_URL + href if href.startswith("/") else href

            if full_url in seen:
                continue
            seen.add(full_url)

            # Model kodu URL'den al
            model_code = url_to_model_code(href, brand_slug)
            if not model_code or len(model_code) < 3:
                continue

            # Model slug: brand-modelcode
            ms = href.rstrip("/").split("/")[-1]
            model_slug_val = f"{brand_slug}-{ms}"

            page_items.append({
                "brand":      brand_display,
                "brand_slug": brand_slug,
                "model_code": model_code,
                "model_slug": model_slug_val,
                "source_url": full_url,
                "source":     "zeroteknik",
            })

        if not page_items:
            break

        models.extend(page_items)
        print(f"    Sayfa {page}/{total_pages}: {len(page_items):3d} model  (toplam: {len(models)})")

        if page >= total_pages:
            break

        time.sleep(DELAY)

    return models


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    all_brands, total = [], 0

    for i, (slug, display) in enumerate(TV_BRANDS, 1):
        print(f"\n[{i:2d}/{len(TV_BRANDS)}] {display} ({slug})")
        models = scrape_brand(slug, display)

        if models:
            out_file = os.path.join(OUT_DIR, f"{slug}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(models, f, ensure_ascii=False, indent=2)
            all_brands.append({"slug": slug, "name": display, "modelCount": len(models)})
            total += len(models)
            print(f"  ✅ {len(models)} model → {out_file}")
        else:
            print(f"  ⚠️  Model bulunamadı")

        time.sleep(DELAY)

    with open(os.path.join(OUT_DIR, "brands.json"), "w", encoding="utf-8") as f:
        json.dump(all_brands, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ Tamamlandı! {len(all_brands)} marka, {total} model")
    print(f"Sonraki: python scripts/normalize_all.py")


if __name__ == "__main__":
    main()