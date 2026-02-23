import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
import requests
from bs4 import BeautifulSoup

BASE = "https://www.zeroteknik.com"
START_URL = f"{BASE}/markalar"

OUT_DIR = Path("data/raw/zeroteknik")
OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PasifikDisplayBot/0.1"
}

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text

def extract_brands(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")

    # /markalar/samsung gibi linkleri al
    brands = []
    seen = set()

    for a in soup.select('a[href^="/markalar/"]'):
        href = a.get("href", "").strip()
        if href.count("/") < 2:
            continue
        if href == "/markalar/":
            continue

        # slug
        slug = href.replace("/markalar/", "").strip("/")

        name = a.get_text(" ", strip=True)
        # name bazen "Samsung 4.9 (15) ... İncele" gibi uzun geliyor.
        # İlk kelimeyi değil; mümkün olduğunca temiz marka adı yakalayalım:
        # "Samsung TV Tamiri..." kısmını kırp
        name = re.split(r"\sTV\s|\s4\.\d|\s\(", name, maxsplit=1)[0].strip()

        key = (slug, name)
        if key in seen:
            continue
        seen.add(key)

        brands.append({
            "slug": slug,
            "name": name,
            "url": f"{BASE}{href}"
        })

    # slug'a göre sırala
    brands.sort(key=lambda x: x["slug"])
    return brands

def extract_models_from_brand_pages(brand_slug: str, max_pages: int = 80) -> List[str]:
    """
    ZeroTeknik marka sayfasında model listesi pagination ile geliyor.
    URL yapısı genelde:
      /markalar/samsung?page=2
    Eğer çalışmazsa, ilk sayfayı yine de alır.
    """
    models: List[str] = []
    seen = set()

    for page in range(1, max_pages + 1):
        url = f"{BASE}/markalar/{brand_slug}"
        if page > 1:
            url = f"{url}?page={page}"

        html = fetch(url)
        soup = BeautifulSoup(html, "lxml")

        # Model listeleri genelde sayfada çok sayıda link: "Samsung 32T5300 ✓ ... "
        # Buradan 32T5300 gibi kodu çekmeye çalışıyoruz:
        anchors = soup.select("a")
        found_this_page = 0

        for a in anchors:
            txt = a.get_text(" ", strip=True)
            # Samsung 32T5300 ... veya LG 55UM... gibi pattern
            m = re.search(r"\b([A-Z0-9]{4,})\b", txt)
            if not m:
                continue

            code = m.group(1).strip()
            # Çok genel kelimeleri ele (TV, OLED vs)
            if code.upper() in {"OLED", "QLED", "UHD", "FULL", "HD"}:
                continue

            if code not in seen:
                seen.add(code)
                models.append(code)
                found_this_page += 1

        # Sayfada hiç yeni model bulamadıysa pagination bitmiş olabilir
        if page > 1 and found_this_page == 0:
            break

    return models

def main():
    index_html = fetch(START_URL)
    brands = extract_brands(index_html)

    (OUT_DIR / "brands.json").write_text(
        json.dumps(brands, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    models_by_brand: Dict[str, List[str]] = {}
    for b in brands:
        slug = b["slug"]
        try:
            models = extract_models_from_brand_pages(slug)
        except Exception as e:
            models = []
            print(f"[WARN] {slug} modeller çekilemedi: {e}")
        models_by_brand[slug] = models
        print(f"[OK] {slug}: {len(models)} model")

    (OUT_DIR / "models-by-brand.json").write_text(
        json.dumps(models_by_brand, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\nYazıldı: {OUT_DIR/'brands.json'}")
    print(f"Yazıldı: {OUT_DIR/'models-by-brand.json'}")

if __name__ == "__main__":
    main()
