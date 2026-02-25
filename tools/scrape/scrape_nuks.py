# tools/scrape/scrape_nuks.py
from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "nuks"
RAW_DIR.mkdir(parents=True, exist_ok=True)

NORMALIZED_DIR = ROOT / "data" / "normalized"
BRANDS_JSON = NORMALIZED_DIR / "brands.json"
MODELS_BY_BRAND_JSON = NORMALIZED_DIR / "models-by-brand.json"

BASE = "https://www.nuks.com.tr"

HEADERS = {
    "User-Agent": "PasifikDisplayBot/0.1 (offline-scrape; local use)",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

# Panel tokenları: 6916L-1455B, ST5461D11-3, LC420DUN-PG-P1 vb.
PANEL_TOKEN_RE = re.compile(r"\b[A-Z0-9][A-Z0-9\-_/]{4,}\b")

# Model kodları: 42PFK6309/12, UE40J5270, 32HD7300 vb.
MODEL_CODE_RE = re.compile(r"\b[A-Z0-9]{2,}[A-Z]*[0-9]{2,}[A-Z0-9]*(/[0-9]{1,2})?\b", re.IGNORECASE)

# Etiketli blokları yakalamak için (asıl fix burada)
RE_PANEL_BLOCK = re.compile(
    r"(?:PANEL\s*NUMARALARI|PANEL\s*KOD(?:LARI)?|UYUMLU\s*PANEL(?:LER)?|PANEL\s*NO)\s*:\s*(.+?)(?=(?:KULLANILDIĞI|KULLANILACAK|KULLANIM|KUTU|UYARI|NOT|$))",
    re.IGNORECASE | re.DOTALL,
)
RE_MODEL_BLOCK = re.compile(
    r"(?:KULLANILDIĞI\s*MODELLER|UYUMLU\s*MODELLER|KULLANILDIĞI\s*TV\s*MODELLERİ|UYUMLU\s*TV\s*MODELLERİ)\s*:\s*(.+?)(?=(?:PANEL|KUTU|UYARI|NOT|$))",
    re.IGNORECASE | re.DOTALL,
)

BLACKLIST = {"LED", "TV", "HZ", "HD", "UHD", "4K", "FULL", "SMART", "INCH", "REV", "COF"}

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = (
        s.replace("ç", "c")
        .replace("ğ", "g")
        .replace("ı", "i")
        .replace("ö", "o")
        .replace("ş", "s")
        .replace("ü", "u")
    )
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

@dataclass
class Brand:
    slug: str
    name: str

def load_brand_maps() -> Tuple[Dict[str, Brand], Dict[str, Dict[str, str]]]:
    brands = read_json(BRANDS_JSON)
    brand_by_slug: Dict[str, Brand] = {}
    for b in brands:
        brand_by_slug[b["slug"]] = Brand(slug=b["slug"], name=b["name"])

    models_by_brand = read_json(MODELS_BY_BRAND_JSON)
    # brandSlug -> MODEL_CODE_UPPER -> modelSlug
    map_code_to_slug: Dict[str, Dict[str, str]] = {}
    for brand_slug, items in models_by_brand.items():
        m: Dict[str, str] = {}
        for it in items:
            code = str(it.get("modelCode", "")).strip().upper()
            if not code:
                continue
            m[code] = str(it.get("slug", "")).strip()
        map_code_to_slug[brand_slug] = m

    return brand_by_slug, map_code_to_slug

def http_get(url: str, session: requests.Session, timeout: int = 25) -> str:
    r = session.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()

    # ✅ NUKS bazen encoding'i yanlış gönderebiliyor, güvenli fix:
    if not r.encoding:
        r.encoding = "utf-8"
    return r.text

def find_product_url_from_search(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")

    # arama sonuçlarında ilk .html ürün linki genelde yeterli
    for a in soup.select('a[href*=".html"]'):
        href = a.get("href") or ""
        if href.startswith("/"):
            href = BASE + href
        if href.startswith(BASE) and href.endswith(".html"):
            return href

    # fallback
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        if ".html" in href:
            if href.startswith("/"):
                href = BASE + href
            if href.startswith(BASE):
                return href
    return None

def _extract_tokens(text: str) -> Tuple[List[str], List[str]]:
    """
    Metinden panel token ve model code ayıklar.
    """
    panels: set[str] = set()
    models: set[str] = set()

    # Panel tokenlar
    for tok in PANEL_TOKEN_RE.findall(text.upper()):
        tok = tok.replace("_", "-").strip()
        if tok in BLACKLIST:
            continue
        if len(tok) < 6:
            continue
        if not any(ch.isdigit() for ch in tok):
            continue
        panels.add(tok)

    # Model kodlar
    for mc in re.finditer(MODEL_CODE_RE, text.upper()):
        m = mc.group(0).strip().upper()
        if len(m) >= 5 and any(ch.isdigit() for ch in m):
            models.add(m)

    return sorted(panels), sorted(models)

def parse_nuks_page(html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(" ", strip=True)
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)

    # Daha “tek parça” metin: regex blok yakalamada daha iyi
    full_text = soup.get_text("\n", strip=True)
    lower_text = full_text.lower()
    stock_out = ("stok tükendi" in lower_text) or ("stokta yok" in lower_text)

    panels: set[str] = set()
    models: set[str] = set()

    # ✅ 1) Etiketli bloklardan yakala (asıl kritik)
    panel_blocks = []
    for m in RE_PANEL_BLOCK.finditer(full_text):
        blk = m.group(1)
        panel_blocks.append(blk)
        p_list, _ = _extract_tokens(blk)
        panels.update(p_list)

    model_blocks = []
    for m in RE_MODEL_BLOCK.finditer(full_text):
        blk = m.group(1)
        model_blocks.append(blk)
        _, m_list = _extract_tokens(blk)
        models.update(m_list)

    # ✅ 2) Eğer blok yoksa fallback: sayfanın tamamından çıkar (daha gürültülü ama boş dönmez)
    if not panels:
        p_list, _ = _extract_tokens(full_text)
        panels.update(p_list)

    if not models:
        _, m_list = _extract_tokens(full_text)
        models.update(m_list)

    # Title fallback (bazı panel kodları başlıkta geçer)
    if title:
        p_list, m_list = _extract_tokens(title)
        panels.update(p_list)
        models.update(m_list)

    # Temizlik: blacklist + çok genel olanları at
    panels = {
        p for p in panels
        if p not in BLACKLIST
        and any(ch.isdigit() for ch in p)
        and len(p) >= 6
    }
    models = {m for m in models if len(m) >= 5 and any(ch.isdigit() for ch in m)}

    # Debug: ilk 250 karakter blok örnekleri (issue olursa hızlı görürüz)
    dbg = {
        "panelBlockHit": bool(panel_blocks),
        "modelBlockHit": bool(model_blocks),
        "panelBlockSample": (panel_blocks[0][:250] if panel_blocks else ""),
        "modelBlockSample": (model_blocks[0][:250] if model_blocks else ""),
    }

    return {
        "title": title,
        "stockOut": bool(stock_out),
        "panels": sorted(panels),
        "models": sorted(models),
        "debug": dbg,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-brands", type=int, default=0, help="0=all")
    ap.add_argument("--max-models-per-brand", type=int, default=0, help="0=all")
    ap.add_argument("--sleep", type=float, default=1.25)
    ap.add_argument("--only-featured", action="store_true")
    ap.add_argument("--debug", action="store_true", help="items.json içine debug alanı ekler")
    args = ap.parse_args()

    brand_by_slug, code_to_slug = load_brand_maps()

    brands_list = list(brand_by_slug.values())
    if args.only_featured:
        brands_raw = read_json(BRANDS_JSON)
        featured = {b["slug"] for b in brands_raw if b.get("isFeatured")}
        brands_list = [b for b in brands_list if b.slug in featured]

    if args.max_brands and args.max_brands > 0:
        brands_list = brands_list[: args.max_brands]

    session = requests.Session()

    out_items: List[Dict] = []
    errors: List[Dict] = []

    print("=== NUKS scrape (offline) ===")
    print("Project root:", ROOT)
    print("Output     :", RAW_DIR)

    for b in brands_list:
        model_map = code_to_slug.get(b.slug, {})
        model_codes = list(model_map.keys())
        if args.max_models_per_brand and args.max_models_per_brand > 0:
            model_codes = model_codes[: args.max_models_per_brand]

        for mc in model_codes:
            q = f"{b.name} {mc}"
            url = f"{BASE}/?search={requests.utils.quote(q)}"
            try:
                html = http_get(url, session)
                product_url = find_product_url_from_search(html)
                if not product_url:
                    errors.append({"brand": b.slug, "modelCode": mc, "query": q, "reason": "no_result"})
                    continue

                p_html = http_get(product_url, session)
                parsed = parse_nuks_page(p_html)

                item = {
                    "brand": b.slug,
                    "modelCode": mc,
                    "query": q,
                    "productUrl": product_url,
                    "title": parsed["title"],
                    "stockOut": parsed["stockOut"],
                    "panels": parsed["panels"],
                    "models": parsed["models"],
                }
                if args.debug:
                    item["debug"] = parsed.get("debug", {})

                out_items.append(item)

                print(f"OK  {b.slug} {mc}  panels={len(parsed['panels'])} models={len(parsed['models'])}")

            except Exception as e:
                errors.append({"brand": b.slug, "modelCode": mc, "query": q, "reason": str(e)})
                print(f"ERR {b.slug} {mc}  {e}")

            time.sleep(args.sleep)

    write_json(RAW_DIR / "items.json", out_items)
    write_json(RAW_DIR / "errors.json", errors)

    # hızlı özet
    with_panels = sum(1 for it in out_items if it.get("panels"))
    with_models = sum(1 for it in out_items if it.get("models"))
    print("\nDONE ✅")
    print("-", RAW_DIR / "items.json", f"(items: {len(out_items)}, with_panels: {with_panels}, with_models: {with_models})")
    print("-", RAW_DIR / "errors.json", f"(errors: {len(errors)})")
    print("\nNOTE: Runtime'da NUKS'a istek YOK. Bu sadece offline veri üretir.")

if __name__ == "__main__":
    main()