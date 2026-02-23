from __future__ import annotations
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import requests
from slugify import slugify

USER_AGENT = "PasifikDisplayBot/0.1 (+local-dev; contact: info@pasifikdisplay.com)"
DEFAULT_TIMEOUT = 25

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

def http_get(url: str, *, sleep_s: float = 0.8) -> str:
    """Polite fetch: rate-limited."""
    resp = session.get(url, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    time.sleep(sleep_s)
    return resp.text

def write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def tv_only_filter(text: str) -> bool:
    """
    Heuristic TV-only filter.
    Returns True if looks like TV-related, False if clearly monitor-related.
    You can tighten/relax later.
    """
    t = (text or "").lower()
    monitor_keywords = ["monitor", "monitör", "lcd monitor", "pc monitor"]
    if any(k in t for k in monitor_keywords):
        return False
    return True

def normalize_panel_code(code: str) -> str:
    """
    Canonicalize panel code:
    - strip spaces
    - upper-case
    - normalize separators
    """
    if not code:
        return ""
    c = code.strip()
    c = re.sub(r"\s+", "", c)
    c = c.replace("_", "-")
    return c.upper()

def make_slug(s: str) -> str:
    return slugify(s, lowercase=True, separator="-")

@dataclass
class Brand:
    slug: str
    name: str

@dataclass
class TVModel:
    brand_slug: str
    model_code: str
    slug: str  # e.g. samsung-ue55nu7100
    screen_size: Optional[int] = None
    year: Optional[int] = None
    panels: Optional[list[str]] = None  # list of panel codes

def model_slug(brand_slug: str, model_code: str) -> str:
    return make_slug(f"{brand_slug}-{model_code}")
