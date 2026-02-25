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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}

PANEL_TOKEN_RE = re.compile(r"\b[A-Z0-9][A-Z0-9\-_/]{4,}\b")
MODEL_CODE_RE = re.compile(
    r"\b[A-Z0-9]{2,}[A-Z]*[0-9]{2,}[A-Z0-9]*(/[0-9]{1,2})?\b", re.IGNORECASE
)

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
    brand_by_slug: Dict[str, Brand] = {b["slug"]: Brand(slug=b["slug"], name=b["name"]) for b in brands}

    models_by_brand = read_json(MODELS_BY_BRAND_JSON)
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
    r = session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return r.text

def detect_js_gate_or_rate_limit(html: str) -> Optional[str]:
    t = html.lower()
    # Çok hızlı arama / bekleme ekranı
    if "çok hızlı arama" in t or "bekleyiniz" in t and "saniye" in t:
        return "rate_limit"
    # Cloudflare / JS required tarzı
    if "checking your browser" in t or "enable javascript" in t or "cloudflare" in t:
        return "js_gate"
    return None

def find_product_url_from_search(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    for a in soup.select('a[href*=".html"]'):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        if href.startswith("/"):
            href = BASE + href
        if href.startswith(BASE) and ".html" in href:
            # bazı linklerde query olabilir, yine de olur
            return href.split("#")[0]
    return None

def _extract_from_line(line: str, panels: set[str], models: set[str]):
    for tok in PANEL_TOKEN_RE.findall(line.upper()):
        panels.add(tok.replace("_", "-"))
    for mc in re.finditer(MODEL_CODE_RE, line.upper()):
        models.add(mc.group(0).upper())

def parse_nuks_page(html: str, debug: bool = False) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(" ", strip=True)
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)

    full_text = soup.get_text("\n", strip=True)
    lower_text = full_text.lower()

    stock_out = ("stok tükendi" in lower_text) or ("stokta yok" in lower_text)

    panels: set[str] = set()
    models: set[str] = set()

    lines = [ln.strip() for ln in full_text.split("\n") if ln.strip()]

    # 1) Başlık yakala → ALT SATIRLARA BAK (asıl fix burada)
    trigger_panel_headers = ("uyumlu panel", "uyumlu panel kod", "uyumlu panel kodları", "panel kod", "panel kodları", "panel numara")
    trigger_model_headers = ("uyumlu televizyon", "uyumlu tv", "uyumlu model", "uyumlu televizyon modelleri", "uyumlu tv modelleri")

    for i, ln in enumerate(lines):
        l = ln.lower()

        if any(h in l for h in trigger_panel_headers):
            # başlığın altındaki birkaç satırda kodlar listeleniyor
            for j in range(i, min(i + 8, len(lines))):
                _extract_from_line(lines[j], panels, models)

        if any(h in l for h in trigger_model_headers):
            for j in range(i, min(i + 12, len(lines))):
                _extract_from_line(lines[j], panels, models)

    # 2) DOM üzerinden: heading sonrası blok tarama (h2/h3/h4)
    def scan_after_heading(needle: str, take: int):
        for tag in soup.find_all(["h2", "h3", "h4", "strong"]):
            txt = tag.get_text(" ", strip=True).lower()
            if needle in txt:
                # heading'den sonra gelen kardeşlerden bir süre topla
                cur = tag
                steps = 0
                while cur and steps < take:
                    cur = cur.find_next()
                    if not cur:
                        break
                    t = cur.get_text(" ", strip=True)
                    if t:
                        _extract_from_line(t, panels, models)
                    steps += 1

    scan_after_heading("uyumlu panel", 40)
    scan_after_heading("uyumlu televizyon", 60)
    scan_after_heading("uyumlu tv", 60)

    # 3) Fallback: başlıktan panel benzeri token
    if title:
        _extract_from_line(title, panels, models)

    # Temizlik
    blacklist = {"LED", "TV", "HZ", "HD", "UHD", "4K", "FULL", "SMART", "INCH"}
    panels = {p for p in panels if p not in blacklist and any(ch.isdigit() for ch in p) and len(p) >= 6}
    models = {m for m in models if any(ch.isdigit() for ch in m) and len(m) >= 5}

    if debug:
        print("DEBUG title:", title)
        print("DEBUG panels sample:", sorted(list(panels))[:10])
        print("DEBUG models sample:", sorted(list(models))[:10])

    return {
        "title": title,
        "stockOut": bool(stock_out),
        "panels": sorted(panels),
        "models": sorted(models),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-brands", type=int, default=0, help="0=all")
    ap.add_argument("--max-models-per-brand", type=int, default=0, help="0=all")
    ap.add_argument("--sleep", type=float, default=2.0, help="Her isteğin arasına bekleme (NUKS rate-limit için 6-10 öneririm)")
    ap.add_argument("--only-featured", action="store_true")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--save-html", action="store_true")
    ap.add_argument("--retry", type=int, default=2, help="rate-limit/js-gate olursa kaç kere denesin")
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

    html_dir = RAW_DIR / "html"
    if args.save_html:
        html_dir.mkdir(parents=True, exist_ok=True)

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

            # NUKS aramada bazen "/" sorun çıkarabiliyor
            q_clean = q.replace("/", " ")
            search_url = f"{BASE}/?search={requests.utils.quote(q_clean)}"

            attempt = 0
            while True:
                attempt += 1
                try:
                    html = http_get(search_url, session)
                    gate = detect_js_gate_or_rate_limit(html)
                    if gate == "rate_limit":
                        # çok hızlı arama: bekle ve retry
                        wait_s = max(8.0, args.sleep * 4)
                        print(f"WARN {b.slug} {mc}  rate_limit → wait {wait_s:.1f}s (attempt {attempt})")
                        time.sleep(wait_s)
                        if attempt <= args.retry:
                            continue
                    if gate == "js_gate":
                        print(f"WARN {b.slug} {mc}  search_js_gate (attempt {attempt})")
                        # js gate'de retry çoğu zaman işe yaramaz; yine de kısa bekle
                        time.sleep(max(6.0, args.sleep * 3))
                        if attempt <= args.retry:
                            continue
                        errors.append({"brand": b.slug, "modelCode": mc, "query": q, "reason": "search_js_gate"})
                        break

                    product_url = find_product_url_from_search(html)
                    if not product_url:
                        errors.append({"brand": b.slug, "modelCode": mc, "query": q, "reason": "no_result"})
                        break

                    p_html = http_get(product_url, session)
                    parsed = parse_nuks_page(p_html, debug=args.debug)

                    if args.save_html:
                        safe = f"{b.slug}__{mc}".replace("/", "_").replace("\\", "_")
                        (html_dir / f"{safe}.html").write_text(p_html, encoding="utf-8")

                    out_items.append(
                        {
                            "brand": b.slug,
                            "modelCode": mc,
                            "query": q,
                            "productUrl": product_url,
                            "title": parsed["title"],
                            "stockOut": parsed["stockOut"],
                            "panels": parsed["panels"],
                            "models": parsed["models"],
                        }
                    )

                    print(f"OK  {b.slug} {mc}  panels={len(parsed['panels'])} models={len(parsed['models'])}")
                    break

                except Exception as e:
                    msg = str(e)
                    print(f"ERR {b.slug} {mc}  {msg}")
                    if attempt <= args.retry:
                        time.sleep(max(6.0, args.sleep * 3))
                        continue
                    errors.append({"brand": b.slug, "modelCode": mc, "query": q, "reason": msg})
                    break

            time.sleep(args.sleep)

    write_json(RAW_DIR / "items.json", out_items)
    write_json(RAW_DIR / "errors.json", errors)

    with_panels = sum(1 for it in out_items if it.get("panels"))
    with_models = sum(1 for it in out_items if it.get("models"))

    print("\nDONE ✅")
    print("-", RAW_DIR / "items.json", f"(items: {len(out_items)}, with_panels: {with_panels}, with_models: {with_models})")
    print("-", RAW_DIR / "errors.json", f"(errors: {len(errors)})")
    print("\nNOTE: Runtime'da NUKS'a istek YOK. Bu sadece offline veri üretir.")

if __name__ == "__main__":
    main()