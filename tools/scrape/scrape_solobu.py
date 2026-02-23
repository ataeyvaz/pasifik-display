import json
import re
from pathlib import Path
from typing import Dict, List
import requests
from bs4 import BeautifulSoup

BASE = "https://www.solobu.com"
START_URL = f"{BASE}/kategori/led-tv-ekran-panel"

OUT_DIR = Path("data/raw/solobu")
OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PasifikDisplayBot/0.1"
}

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text

def extract_led_tv_brand_links(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    brands = []
    seen = set()

    # Solobu menüde LED TV altında /kategori/<slug> linkleri var.
    # Basitçe /kategori/ ile başlayan linklerden, "Monitör" kısmına girmeden toplayacağız.
    # Pratik yaklaşım: START_URL sayfasındaki menüde "LED TV" başlığından sonraki ilk grup linkleri çek.
    # Bu sayfada en garanti yöntem: /kategori/<slug> linklerini topla ve slug'ı al.
    for a in soup.select('a[href^="/kategori/"]'):
        href = a.get("href", "").strip()
        slug = href.replace("/kategori/", "").strip("/")

        # led-tv-ekran-panel sayfasının kendisini geç
        if slug in {"led-tv-ekran-panel"}:
            continue

        name = a.get_text(" ", strip=True)
        if not name or len(name) > 30:
            continue

        key = (slug, name.lower())
        if key in seen:
            continue
        seen.add(key)

        brands.append({"slug": slug, "name": name, "url": f"{BASE}{href}"})

    # TV-only: Monitör slugs vb. filtrelemek için basit whitelist/blacklist:
    # Solobu'da monitör markaları da /kategori/<slug> olarak geliyor.
    # Bu yüzden burada sadece LED TV markalarını almak için bir taktik:
    # START_URL menüsünde LED TV listesi çok uzun ama yine de, monitör markalarında "Acer, Asus..." gibi çok bilgisayar markası var.
    # Burada ilk aşamada hepsini ham olarak alıyoruz; normalize aşamasında TV-only filtresini kesin uygulayacağız.
    brands.sort(key=lambda x: x["name"].lower())
    return brands

def extract_products_from_brand(brand_slug: str, max_pages: int = 60) -> List[Dict[str, str]]:
    """
    /kategori/samsung gibi sayfalarda ürün başlıkları var.
    Pagination yapısı değişebiliyor; biz:
      - ilk sayfayı çek
      - ürün linklerini topla
      - sayfada yeni ürün gelmezse dur
    """
    products = []
    seen = set()

    for page in range(1, max_pages + 1):
        url = f"{BASE}/kategori/{brand_slug}"
        if page > 1:
            # Solobu'da sayfa paramı farklı olabilir; şimdilik en sık kullanılanları deniyoruz
            # 1) ?page=2
            # 2) ?sayfa=2
            # ikisi de olmazsa aynı sayfayı tekrar çeker; 'yeni ürün gelmedi' kontrolü durdurur.
            url_try = f"{url}?page={page}"
            html = fetch(url_try)
            if html:
                url = url_try
            else:
                url = f"{url}?sayfa={page}"

        html = fetch(url)
        soup = BeautifulSoup(html, "lxml")

        found_this_page = 0
        for a in soup.select("a"):
            text = a.get_text(" ", strip=True)
            href = a.get("href", "").strip()

            # Ürün başlığı genelde "... LED TV Ekran Değişimi" içeriyor
            if "LED TV" not in text and "Ekran" not in text:
                continue
            if not href.startswith("/"):
                continue

            full = f"{BASE}{href}"
            if full in seen:
                continue

            seen.add(full)
            products.append({
                "title": text,
                "url": full
            })
            found_this_page += 1

        if page > 1 and found_this_page == 0:
            break

    return products

def main():
    html = fetch(START_URL)
    brands = extract_led_tv_brand_links(html)
    (OUT_DIR / "brands-led-tv.json").write_text(
        json.dumps(brands, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"[OK] brand sayısı (ham): {len(brands)}")

    # Şimdilik sadece “senin featured” listendeki markaları çekmek mantıklı (hız için).
    featured = {"philips","samsung","lg","grundig","beko","arcelik","telefunken","tcl","blaupunkt","sony","vestel"}
    products_by_brand: Dict[str, List[Dict[str, str]]] = {}

    for b in brands:
        if b["slug"] not in featured:
            continue
        slug = b["slug"]
        try:
            prods = extract_products_from_brand(slug)
        except Exception as e:
            prods = []
            print(f"[WARN] {slug} ürünleri çekilemedi: {e}")
        products_by_brand[slug] = prods
        print(f"[OK] {slug}: {len(prods)} ürün")

    (OUT_DIR / "products-by-brand.json").write_text(
        json.dumps(products_by_brand, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\nYazıldı: {OUT_DIR/'brands-led-tv.json'}")
    print(f"Yazıldı: {OUT_DIR/'products-by-brand.json'}")

if __name__ == "__main__":
    main()
