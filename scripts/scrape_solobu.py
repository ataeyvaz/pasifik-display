"""
scrape_solobu.py  v2
====================
solobu.com'dan tüm LED TV modellerini çeker.

Düzeltmeler (v2):
  - URL: önce /kategori/ dener, 404 gelirse /marka/ dener
  - Sayfalama: next link aramak yerine sayfa boşalınca durur
  - TV filtresi: /kategori/{brand} zaten sadece TV, ekstra filtre yok

Kullanım:
  pip install requests beautifulsoup4
  python scripts/scrape_solobu.py

Çıktı:
  raw/solobu/{brand}.json
"""

import json, os, re, time, requests
from bs4 import BeautifulSoup

BASE_URL  = "https://www.solobu.com"
OUT_DIR   = "raw/solobu"
DELAY     = 1.0
MAX_PAGES = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9",
}

# Menüdeki tüm LED TV markaları
TV_BRANDS = [
    ("altus",        "Altus"),
    ("arcelik",      "Arçelik"),
    ("awox",         "Awox"),
    ("axen",         "Axen"),
    ("beko",         "Beko"),
    ("blaupunkt",    "Blaupunkt"),
    ("botech",       "Botech"),
    ("daewoo",       "Daewoo"),
    ("delta",        "Delta"),
    ("dextel",       "Dextel"),
    ("digipoll",     "Digipoll"),
    ("dijitsu",      "Dijitsu"),
    ("dijitv",       "DijiTV"),
    ("dikom",        "Dikom"),
    ("dreamstar",    "Dreamstar"),
    ("eas",          "EAS"),
    ("electromaster","ElectroMaster"),
    ("elton",        "Elton"),
    ("fenoti",       "Fenoti"),
    ("finlux",       "Finlux"),
    ("fivo",         "Fivo"),
    ("fobem",        "Fobem"),
    ("goldmaster",   "Goldmaster"),
    ("grundig",      "Grundig"),
    ("hello",        "Hello"),
    ("hi-level",     "Hi-Level"),
    ("hitachi",      "Hitachi"),
    ("hyundai",      "Hyundai"),
    ("jameson",      "Jameson"),
    ("jvc",          "JVC"),
    ("kamosonic",    "Kamosonic"),
    ("keysmart",     "Keysmart"),
    ("lg",           "LG"),
    ("luxor",        "Luxor"),
    ("morio",        "Morio"),
    ("navitech",     "Navitech"),
    ("nexon",        "Nexon"),
    ("next",         "Next"),
    ("nordmende",    "Nordmende"),
    ("olimpia",      "Olimpia"),
    ("onvo",         "Onvo"),
    ("panasonic",    "Panasonic"),
    ("peaq",         "PEAQ"),
    ("philips",      "Philips"),
    ("piranha",      "Piranha"),
    ("practica",     "Practica"),
    ("premier",      "Premier"),
    ("preo",         "Preo"),
    ("profilo",      "Profilo"),
    ("quax",         "Quax"),
    ("redline",      "Redline"),
    ("regal",        "Regal"),
    ("rose",         "Rose"),
    ("rowell",       "Rowell"),
    ("saba",         "Saba"),
    ("samsung",      "Samsung"),
    ("seg",          "SEG"),
    ("sharp",        "Sharp"),
    ("sheen",        "Sheen"),
    ("simfer",       "Simfer"),
    ("skytech",      "Skytech"),
    ("sony",         "Sony"),
    ("strong",       "Strong"),
    ("sungate",      "Sungate"),
    ("sunny",        "Sunny"),
    ("tcl",          "TCL"),
    ("teba",         "Teba"),
    ("techwood",     "Techwood"),
    ("telefox",      "Telefox"),
    ("telefunken",   "Telefunken"),
    ("telenova",     "Telenova"),
    ("toshiba",      "Toshiba"),
    ("ventus",       "Ventus"),
    ("vestel",       "Vestel"),
    ("vox",          "Vox"),
    ("weston",       "Weston"),
    ("woon",         "Woon"),
    ("xiaomi",       "Xiaomi"),
    ("yumatu",       "Yumatu"),
]

SKIP_TITLE_WORDS = ["monitör", "monitor", "all-in-one", "video wall", "ekran koruyucu"]


def get(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"  ⚠️  Hata ({url}): {e} — {i+1}/{retries}")
            time.sleep(2)
    return None


def brand_base_url(brand_slug):
    """Önce /kategori/ dene, 404 gelirse /marka/ dene."""
    url = f"{BASE_URL}/kategori/{brand_slug}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code == 200:
        return f"{BASE_URL}/kategori/{brand_slug}"
    return f"{BASE_URL}/marka/{brand_slug}"


def extract_products(soup, brand_slug, brand_display, seen):
    """Sayfadaki ürün linklerini parse et, TV olmayanları atla."""
    results = []
    for a in soup.select("a[href*='/urun/']"):
        href  = a.get("href", "")
        title = (a.get("title") or a.get_text(strip=True) or "").strip()

        if not href or not title:
            continue
        if href.startswith("/"):
            href = BASE_URL + href
        if href in seen:
            continue

        # Monitör vb. atla
        title_lower = title.lower()
        if any(w in title_lower for w in SKIP_TITLE_WORDS):
            continue

        seen.add(href)

        # Slug: URL'nin son parçası, gürültüyü temizle
        url_slug = href.split("/urun/")[-1].rstrip("/")
        for suffix in ["-led-tv-ekran-degisimi", "-ekran-degisimi",
                       "-oled-tv-ekran-degisimi", "-qled-tv-ekran-degisimi"]:
            if url_slug.endswith(suffix):
                url_slug = url_slug[:-len(suffix)]
                break

        # Model kodunu başlıktan çıkar
        model_code = title.strip()
        # Marka adını baştaki kaldır
        for prefix in [brand_display, brand_slug.title(), brand_slug.upper()]:
            if model_code.lower().startswith(prefix.lower()):
                model_code = model_code[len(prefix):].strip()
                break
        # Sonundaki gürültüyü at
        for noise in ["LED TV Ekran Değişimi", "OLED TV Ekran Değişimi",
                      "QLED TV Ekran Değişimi", "Ekran Değişimi",
                      "LED TV", "OLED TV", "QLED TV"]:
            idx = model_code.lower().find(noise.lower())
            if idx > 0:
                model_code = model_code[:idx].strip()

        model_code = model_code.strip(" -–()")
        if not model_code or len(model_code) < 3:
            continue

        results.append({
            "brand":      brand_display,
            "brand_slug": brand_slug,
            "model_code": model_code,
            "model_slug": url_slug,
            "source_url": href,
            "source":     "solobu",
        })
    return results


def scrape_brand(brand_slug, brand_display):
    base = brand_base_url(brand_slug)
    models = []
    seen   = set()

    for page in range(1, MAX_PAGES + 1):
        url = base if page == 1 else f"{base}?tp={page}"
        r   = get(url)
        if not r:
            break

        soup        = BeautifulSoup(r.text, "html.parser")
        page_items  = extract_products(soup, brand_slug, brand_display, seen)

        if not page_items:
            break  # Boş sayfa → dur

        models.extend(page_items)
        print(f"    Sayfa {page}: {len(page_items):3d} model  (toplam: {len(models)})")

        # Son sayfa kontrolü: sayfalama linkinde tp=page+1 var mı?
        pagination = soup.select("a[href*='tp=']")
        max_page = 1
        for a in pagination:
            m = re.search(r"tp=(\d+)", a.get("href", ""))
            if m:
                max_page = max(max_page, int(m.group(1)))

        if page >= max_page:
            break

        time.sleep(DELAY)

    return models


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    all_brands   = []
    total_models = 0

    for i, (slug, display) in enumerate(TV_BRANDS, 1):
        print(f"\n[{i:2d}/{len(TV_BRANDS)}] {display} ({slug})")
        models = scrape_brand(slug, display)

        if models:
            out_file = os.path.join(OUT_DIR, f"{slug}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(models, f, ensure_ascii=False, indent=2)
            all_brands.append({"slug": slug, "name": display, "modelCount": len(models)})
            total_models += len(models)
            print(f"  ✅ {len(models)} model → {out_file}")
        else:
            print(f"  ⚠️  Model bulunamadı")

        time.sleep(DELAY)

    brands_file = os.path.join(OUT_DIR, "brands.json")
    with open(brands_file, "w", encoding="utf-8") as f:
        json.dump(all_brands, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ Tamamlandı!")
    print(f"   Markalar : {len(all_brands)}")
    print(f"   Modeller : {total_models}")
    print(f"\nSonraki adım:")
    print(f"   python scripts/normalize_all.py")
    print(f"   python scripts/build_search_index.py")


if __name__ == "__main__":
    main()