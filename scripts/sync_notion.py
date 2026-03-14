#!/usr/bin/env python3
"""
sync_notion.py
==============
Hämtar bloggposter och galleribilder från Notion API
och sparar dem som JSON-filer i /data/.

Körs av GitHub Action vid varje push eller schema.

Miljövariabler som krävs (sätts som GitHub Secrets):
  NOTION_TOKEN            – Notion Integration API-token
  NOTION_BLOG_DB_ID       – ID för bloggens databas i Notion
  NOTION_GALLERY_DB_ID    – ID för galleriets databas i Notion
"""

import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Konfiguration ─────────────────────────────────────────────
NOTION_TOKEN        = os.environ.get("NOTION_TOKEN", "")
NOTION_BLOG_DB_ID   = os.environ.get("NOTION_BLOG_DB_ID", "")
NOTION_GALLERY_DB_ID = os.environ.get("NOTION_GALLERY_DB_ID", "")

OUTPUT_BLOG    = "data/blog.json"
OUTPUT_GALLERY = "data/gallery.json"

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION  = "2022-06-28"

# ── Hjälpfunktioner ───────────────────────────────────────────

def notion_request(method: str, path: str, body: dict = None) -> dict:
    """Gör ett anrop mot Notion API."""
    url = f"{NOTION_API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  [FEL] HTTP {e.code} – {e.reason} – {path}")
        return {}


def query_database(db_id: str, filter_body: dict = None) -> list:
    """Hämtar alla sidor ur en Notion-databas (hanterar pagination)."""
    results = []
    body    = {"page_size": 100}
    if filter_body:
        body["filter"] = filter_body

    while True:
        resp = notion_request("POST", f"/databases/{db_id}/query", body)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        body["start_cursor"] = resp["next_cursor"]

    return results


def get_page_blocks(page_id: str) -> list:
    """Hämtar alla block (innehåll) från en Notion-sida."""
    blocks  = []
    path    = f"/blocks/{page_id}/children?page_size=100"
    while path:
        resp = notion_request("GET", path)
        blocks.extend(resp.get("results", []))
        path = None
        if resp.get("has_more"):
            path = f"/blocks/{page_id}/children?page_size=100&start_cursor={resp['next_cursor']}"
    return blocks


def rich_text_to_str(rich_texts: list) -> str:
    """Konverterar Notions rich_text-array till vanlig text."""
    return "".join(t.get("plain_text", "") for t in (rich_texts or []))


def extract_file_url(prop) -> str:
    """Hämtar URL från en files-property i Notion."""
    files = prop.get("files", [])
    if not files:
        return ""
    f = files[0]
    if f.get("type") == "external":
        return f["external"].get("url", "")
    if f.get("type") == "file":
        return f["file"].get("url", "")   # Notions egna hosting (tidsbegränsad URL)
    return ""


def blocks_to_content(blocks: list) -> list:
    """Omvandlar Notion-block till en enkel lista med content-objekt."""
    content = []
    for b in blocks:
        btype = b.get("type")
        if btype in ("paragraph", "quote"):
            text = rich_text_to_str(b[btype].get("rich_text", []))
            if text.strip():
                content.append({"type": "paragraph", "text": text})
        elif btype in ("heading_1", "heading_2", "heading_3"):
            text = rich_text_to_str(b[btype].get("rich_text", []))
            if text.strip():
                content.append({"type": "heading", "text": text})
        elif btype == "image":
            img = b["image"]
            url = img.get("external", {}).get("url") or img.get("file", {}).get("url", "")
            if url:
                content.append({"type": "image", "url": url})
        elif btype == "bulleted_list_item":
            text = rich_text_to_str(b[btype].get("rich_text", []))
            if text.strip():
                content.append({"type": "paragraph", "text": f"• {text}"})
    return content


def notion_date(prop) -> str:
    """Hämtar datum (ISO-sträng) från en date-property."""
    d = prop.get("date") or {}
    return d.get("start", "")


def notion_select(prop) -> str:
    """Hämtar värdet från en select-property."""
    s = prop.get("select") or {}
    return s.get("name", "")


def clean_id(raw_id: str) -> str:
    """Normaliserar Notion-ID (tar bort bindestreck etc.)."""
    return re.sub(r"[^a-f0-9]", "", raw_id.lower())

# ── Blogg ─────────────────────────────────────────────────────

def sync_blog():
    print("→ Synkar blogg...")
    if not NOTION_BLOG_DB_ID:
        print("  [VARNING] NOTION_BLOG_DB_ID är inte satt. Hoppar över.")
        _save_json(OUTPUT_BLOG, {"posts": [], "updated": _now()})
        return

    pages = query_database(
        NOTION_BLOG_DB_ID,
        filter_body={
            "property": "Publicerad",
            "checkbox": {"equals": True}
        }
    )
    print(f"  Hittade {len(pages)} publicerade inlägg.")

    posts = []
    for page in pages:
        props = page.get("properties", {})
        pid   = page["id"]

        # Läs egenskaper
        title   = rich_text_to_str(props.get("Titel", {}).get("title", []))
        summary = rich_text_to_str(props.get("Sammanfattning", {}).get("rich_text", []))
        date    = notion_date(props.get("Datum", {}))
        cover   = extract_file_url(props.get("Omslagsbild", {}))

        # Hämta sidans innehåll (block)
        blocks  = get_page_blocks(pid)
        content = blocks_to_content(blocks)

        posts.append({
            "id":      clean_id(pid),
            "title":   title or "(Inlägg utan titel)",
            "summary": summary,
            "date":    date,
            "cover":   cover,
            "content": content,
        })

    # Sortera nyast först
    posts.sort(key=lambda p: p["date"] or "", reverse=True)

    _save_json(OUTPUT_BLOG, {"posts": posts, "updated": _now()})
    print(f"  ✓ Sparade {len(posts)} inlägg till {OUTPUT_BLOG}")

# ── Galleri ───────────────────────────────────────────────────

def sync_gallery():
    print("→ Synkar galleri...")
    if not NOTION_GALLERY_DB_ID:
        print("  [VARNING] NOTION_GALLERY_DB_ID är inte satt. Hoppar över.")
        _save_json(OUTPUT_GALLERY, {"images": [], "updated": _now()})
        return

    pages = query_database(NOTION_GALLERY_DB_ID)
    print(f"  Hittade {len(pages)} bilder.")

    images = []
    for page in pages:
        props = page.get("properties", {})
        pid   = page["id"]

        title    = rich_text_to_str(props.get("Titel", {}).get("title", []))
        url      = extract_file_url(props.get("Bild", {}))
        category = notion_select(props.get("Kategori", {}))
        date     = notion_date(props.get("Datum", {}))

        if not url:
            continue   # Hoppa över poster utan bild

        images.append({
            "id":       clean_id(pid),
            "title":    title,
            "url":      url,
            "category": category,
            "date":     date,
        })

    # Sortera nyast först
    images.sort(key=lambda i: i["date"] or "", reverse=True)

    _save_json(OUTPUT_GALLERY, {"images": images, "updated": _now()})
    print(f"  ✓ Sparade {len(images)} bilder till {OUTPUT_GALLERY}")

# ── Hjälpfunktioner ───────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    if not NOTION_TOKEN:
        raise SystemExit("FEL: NOTION_TOKEN är inte satt som miljövariabel.")

    sync_blog()
    sync_gallery()
    print("\n✅ Sync klar!")
