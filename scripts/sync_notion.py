#!/usr/bin/env python3
"""
sync_notion.py
==============
Hämtar allt innehåll från Notion och sparar som JSON i /data/.

Databaser som synkas:
  - Hundarna  → data/dogs.json
  - Kull      → data/litters.json
  - Blogg     → data/blog.json
  - Galleri   → data/gallery.json

Miljövariabler (GitHub Secrets):
  NOTION_TOKEN
  NOTION_DOGS_DB_ID
  NOTION_LITTERS_DB_ID
  NOTION_BLOG_DB_ID
  NOTION_GALLERY_DB_ID
"""

import os, json, re, urllib.request, urllib.error
from datetime import datetime, timezone

NOTION_TOKEN         = os.environ.get("NOTION_TOKEN", "")
NOTION_DOGS_DB_ID    = os.environ.get("NOTION_DOGS_DB_ID", "")
NOTION_LITTERS_DB_ID = os.environ.get("NOTION_LITTERS_DB_ID", "")
NOTION_BLOG_DB_ID    = os.environ.get("NOTION_BLOG_DB_ID", "")
NOTION_GALLERY_DB_ID = os.environ.get("NOTION_GALLERY_DB_ID", "")

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION  = "2022-06-28"

# ── Notion API ────────────────────────────────────────────────

def notion_request(method, path, body=None):
    url     = f"{NOTION_API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  [FEL] HTTP {e.code} – {path}")
        return {}

def query_database(db_id, filter_body=None):
    results, body = [], {"page_size": 100}
    if filter_body:
        body["filter"] = filter_body
    while True:
        resp = notion_request("POST", f"/databases/{db_id}/query", body)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        body["start_cursor"] = resp["next_cursor"]
    return results

def get_page_blocks(page_id):
    blocks, path = [], f"/blocks/{page_id}/children?page_size=100"
    while path:
        resp = notion_request("GET", path)
        blocks.extend(resp.get("results", []))
        path = f"/blocks/{page_id}/children?page_size=100&start_cursor={resp['next_cursor']}" \
               if resp.get("has_more") else None
    return blocks

def rich_text(rt):
    return "".join(t.get("plain_text", "") for t in (rt or []))

def file_url(prop):
    for f in prop.get("files", []):
        if f.get("type") == "external": return f["external"].get("url", "")
        if f.get("type") == "file":     return f["file"].get("url", "")
    return ""

def file_urls(prop):
    urls = []
    for f in prop.get("files", []):
        if f.get("type") == "external": urls.append(f["external"].get("url", ""))
        elif f.get("type") == "file":   urls.append(f["file"].get("url", ""))
    return urls

def notion_date(prop):
    return (prop.get("date") or {}).get("start", "")

def notion_select(prop):
    return (prop.get("select") or {}).get("name", "")

def clean_id(raw):
    return re.sub(r"[^a-f0-9]", "", raw.lower())

def blocks_to_content(blocks):
    content = []
    for b in blocks:
        t = b.get("type")
        if t in ("paragraph", "quote"):
            text = rich_text(b[t].get("rich_text", []))
            if text.strip(): content.append({"type": "paragraph", "text": text})
        elif t in ("heading_1", "heading_2", "heading_3"):
            text = rich_text(b[t].get("rich_text", []))
            if text.strip(): content.append({"type": "heading", "text": text})
        elif t == "image":
            url = b["image"].get("external", {}).get("url") or b["image"].get("file", {}).get("url", "")
            if url: content.append({"type": "image", "url": url})
        elif t == "bulleted_list_item":
            text = rich_text(b[t].get("rich_text", []))
            if text.strip(): content.append({"type": "paragraph", "text": f"• {text}"})
    return content

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now():
    return datetime.now(timezone.utc).isoformat()

# ── Hundarna ──────────────────────────────────────────────────

def sync_dogs():
    print("→ Synkar hundarna...")
    if not NOTION_DOGS_DB_ID:
        print("  [VARNING] NOTION_DOGS_DB_ID saknas.")
        save("data/dogs.json", {"dogs": [], "updated": now()})
        return

    pages = query_database(NOTION_DOGS_DB_ID)
    dogs  = []
    for page in pages:
        props = page.get("properties", {})
        dogs.append({
            "id":             clean_id(page["id"]),
            "namn":           rich_text(props.get("Namn", {}).get("title", [])),
            "fullstandigt":   rich_text(props.get("Fullständigt namn", {}).get("rich_text", [])),
            "ras":            notion_select(props.get("Ras", {})),
            "beskrivning":    rich_text(props.get("Beskrivning", {}).get("rich_text", [])),
            "foto":           file_url(props.get("Foto", {})),
            "sortering":      (props.get("Sortering", {}).get("number") or 99),
        })

    dogs.sort(key=lambda d: d["sortering"])
    save("data/dogs.json", {"dogs": dogs, "updated": now()})
    print(f"  ✓ {len(dogs)} hundar sparade.")

# ── Kull ──────────────────────────────────────────────────────

def sync_litters():
    print("→ Synkar kull...")
    if not NOTION_LITTERS_DB_ID:
        print("  [VARNING] NOTION_LITTERS_DB_ID saknas.")
        save("data/litters.json", {"litters": [], "updated": now()})
        return

    pages   = query_database(NOTION_LITTERS_DB_ID,
                              filter_body={"property": "Aktiv", "checkbox": {"equals": True}})
    litters = []
    for page in pages:
        props = page.get("properties", {})
        litters.append({
            "id":          clean_id(page["id"]),
            "titel":       rich_text(props.get("Titel", {}).get("title", [])),
            "beskrivning": rich_text(props.get("Beskrivning", {}).get("rich_text", [])),
            "mor":         rich_text(props.get("Mor", {}).get("rich_text", [])),
            "far":         rich_text(props.get("Far", {}).get("rich_text", [])),
            "datum":       notion_date(props.get("Förväntad datum", {})),
            "mor_foto":    file_url(props.get("Mor foto", {})),
            "far_foto":    file_url(props.get("Far foto", {})),
            "bilder":      file_urls(props.get("Kullbilder", {})),
        })

    save("data/litters.json", {"litters": litters, "updated": now()})
    print(f"  ✓ {len(litters)} aktiva kull sparade.")

# ── Blogg ─────────────────────────────────────────────────────

def sync_blog():
    print("→ Synkar blogg...")
    if not NOTION_BLOG_DB_ID:
        print("  [VARNING] NOTION_BLOG_DB_ID saknas.")
        save("data/blog.json", {"posts": [], "updated": now()})
        return

    pages = query_database(NOTION_BLOG_DB_ID,
                            filter_body={"property": "Publicerad", "checkbox": {"equals": True}})
    posts = []
    for page in pages:
        props = page.get("properties", {})
        pid   = page["id"]
        posts.append({
            "id":      clean_id(pid),
            "title":   rich_text(props.get("Titel", {}).get("title", [])) or "(Inlägg utan titel)",
            "summary": rich_text(props.get("Sammanfattning", {}).get("rich_text", [])),
            "date":    notion_date(props.get("Datum", {})),
            "cover":   file_url(props.get("Omslagsbild", {})),
            "content": blocks_to_content(get_page_blocks(pid)),
        })

    posts.sort(key=lambda p: p["date"] or "", reverse=True)
    save("data/blog.json", {"posts": posts, "updated": now()})
    print(f"  ✓ {len(posts)} inlägg sparade.")

# ── Galleri ───────────────────────────────────────────────────

def sync_gallery():
    print("→ Synkar galleri...")
    if not NOTION_GALLERY_DB_ID:
        print("  [VARNING] NOTION_GALLERY_DB_ID saknas.")
        save("data/gallery.json", {"images": [], "updated": now()})
        return

    pages  = query_database(NOTION_GALLERY_DB_ID)
    images = []
    for page in pages:
        props = page.get("properties", {})
        url   = file_url(props.get("Bild", {}))
        if not url:
            continue
        images.append({
            "id":       clean_id(page["id"]),
            "title":    rich_text(props.get("Titel", {}).get("title", [])),
            "url":      url,
            "category": notion_select(props.get("Kategori", {})),
            "date":     notion_date(props.get("Datum", {})),
        })

    images.sort(key=lambda i: i["date"] or "", reverse=True)
    save("data/gallery.json", {"images": images, "updated": now()})
    print(f"  ✓ {len(images)} bilder sparade.")

# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    if not NOTION_TOKEN:
        raise SystemExit("FEL: NOTION_TOKEN saknas.")
    sync_dogs()
    sync_litters()
    sync_blog()
    sync_gallery()
    print("\n✅ Sync klar!")
