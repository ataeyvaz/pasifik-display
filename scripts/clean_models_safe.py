"""
clean_models_safe.py
====================
Güvenli model veri temizlik scripti.

Silinenler:
  1. Marka adı olan model kodları  → SAMSUNG, PHILIPS, BEKO...
  2. Sadece rakamdan oluşanlar     → 4310, 5740, 6000...
  3. Çöp kelime içerenler          → kvkk, privacy, cookie...
  4. Çok kısa olanlar              → 3 karakter ve altı

Kullanım:
  python scripts/clean_models_safe.py           → dry-run
  python scripts/clean_models_safe.py --apply   → uygula
"""

from __future__ import annotations
import json, os, sys
from typing import Dict, List, Tuple

INPUT_FILE  = "data/normalized/models-by-brand.json"
OUTPUT_FILE = "data/normalized/models-by-brand.json"
REPORT_FILE = "scripts/clean_report_safe.txt"

ALL_BRAND_NAMES = {
    "samsung","philips","lg","sony","vestel","beko","arcelik","toshiba",
    "sharp","panasonic","grundig","hitachi","tcl","telefunken","blaupunkt",
    "hisense","skyworth","finlux","regal","profilo","altus","nordmende",
    "onvo","next","sunny","awox","axen","botech","jvc","xiaomi",
}

JUNK_WORDS = ["kvkk","privacy","cookie","policy","gdpr","kanun","aydinlatma","4654","6698"]
MIN_LEN = 4

def is_definite_junk(model_code: str) -> Tuple[bool, str]:
    mc = model_code.strip()
    mc_lower = mc.lower()
    if not mc:                             return True, "bos model kodu"
    if len(mc) < MIN_LEN:                  return True, f"cok kisa ({len(mc)} karakter)"
    if mc.isdigit():                        return True, "sadece rakam"
    if mc_lower in ALL_BRAND_NAMES:         return True, f"marka adi model kodu olarak: '{mc}'"
    for junk in JUNK_WORDS:
        if junk in mc_lower:               return True, f"cop kelime: '{junk}'"
    return False, ""

def clean_models(data):
    result, report = {}, []
    removed = kept = 0
    for brand_slug, models in data.items():
        clean = []
        for m in models:
            mc = (m.get("modelCode") or "").strip()
            junk, reason = is_definite_junk(mc)
            if junk:
                report.append(f"[SIL] {brand_slug:15} | {mc:30} | {reason}")
                removed += 1
            else:
                clean.append(m)
                kept += 1
        if clean:
            result[brand_slug] = clean
    report += [
        "", "=" * 60, "OZET", "=" * 60,
        f"Silinen  : {removed}",
        f"Kalan    : {kept}",
        f"Markalar : {len(result)}",
    ]
    return result, report

def main():
    dry_run = "--apply" not in sys.argv
    if not os.path.exists(INPUT_FILE):
        print(f"Dosya bulunamadi: {INPUT_FILE}")
        return
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)
    before = sum(len(v) for v in data.values())
    print(f"Once: {before} model, {len([b for b,v in data.items() if v])} marka")
    cleaned, report = clean_models(data)
    after = sum(len(v) for v in cleaned.values())
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print()
    for line in report: print(line)
    print(f"\nSonra: {after} model | Silinen: {before-after}")
    print(f"Rapor: {REPORT_FILE}")
    if dry_run:
        print("\nDRY-RUN - dosya degistirilmedi.")
        print("Uygulamak: python scripts/clean_models_safe.py --apply")
    else:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
        print(f"\nTemizlik uygulandi -> {OUTPUT_FILE}")
        print('Simdi: git add data/normalized/models-by-brand.json')
        print('       git commit -m "data: remove junk model codes"')

if __name__ == "__main__":
    main()