"""Futuristic and new-generation architecture: 3D models of futuristic, modern and next-generation buildings and
houses, and photos and renders of new-gen house designs and construction sites (user, 2026-11-01).

  archmodels  Objaverse objects whose name or tags describe a building, house or construction scene (openly
              licensed only: CC BY, CC BY-SA, CC0), filed by theme as .glb under
              05 CAD, BIM & 3D Models/3D Models/Architecture - Futuristic & New-Gen/<theme>/
  archimages  Wikimedia Commons and Openverse (no key) and Pixabay (PIXABAY_API_KEY) photos and renders, filed as
              21 Architecture & Construction Images/<theme>/<Photos | Renders & Concepts>/<topic>/<source>/
"""
import gzip
import json
import os
import re
import time

from . import split
from .common import get, safe, session
from .models3d import HF, MODELS
from .public import PUB, _download

ARCH = f"{MODELS}/Architecture - Futuristic & New-Gen"
IMAGES = f"{PUB}/21 Architecture & Construction Images"

BUILDING = (r"building|house|home|villa|tower|skyscraper|architect|city|cityscape|apartment|habitat|dome|base|"
            r"station|structure|pavilion|facade|interior|room|hall|temple|bridge|stadium|museum|arena|mall|hotel|"
            r"office|residence|mansion|colony|outpost|hangar|bunker|megastructure|metropolis|town|street|downtown")
# theme: words in an Objaverse name or tag (first theme that matches wins); futuristic needs a building word too
MODEL_THEMES = {
    "Futuristic & Sci-Fi Buildings": rf"(?=.*(?:futuris|sci-?fi|scifi|cyberpunk|neo-?futur|solarpunk|utopi))(?=.*(?:{BUILDING}))|"
                                     r"space ?station|space ?colony|mars base|moon base|lunar base|arcology|"
                                     r"parametric (?:architecture|building|facade|pavilion)|zaha hadid",
    "Modern & New-Gen Houses": r"modern (?:house|home|villa|cabin|residence)|contemporary (?:house|home|villa)|"
                               r"minimalist (?:house|home)|villa|tiny ?house|container ?(?:house|home)|"
                               r"prefab(?:ricated)? (?:house|home|building)|modular (?:house|home|building)|"
                               r"passive ?house|smart ?home|eco ?(?:house|home)|3d.?printed (?:house|home|building)|"
                               r"mansion|bungalow|log cabin|chalet|townhouse|duplex|beach house|lake house",
    "Skyscrapers & Towers": r"skyscraper|high-?rise|tower block|office tower|office building|commercial building",
    "Apartments & City Blocks": r"apartment|condo|residential building|city block|downtown|cityscape|city scene",
    "Construction Sites & Machinery": r"\bconstruction\b|scaffold|excavator|bulldozer|tower crane|crane truck|"
                                      r"concrete mixer|rebar|building site|backhoe|steel frame|formwork",
    "Interiors": r"interior|living ?room|kitchen|bedroom|bathroom|lobby|office space",
    "Houses (other)": r"house|home|cottage|farmhouse|cabin",
    "Architecture (other)": r"architect|archviz|facade|pavilion|building|stadium|museum|airport|train station|"
                            r"bridge|cathedral|church|temple|castle",
}
_THEME_RE = [(t, re.compile(p, re.I)) for t, p in MODEL_THEMES.items()]
LIC_OK = ("by", "by-sa", "cc0", "public")
SHARDS = 160  # Objaverse 1.0 metadata/000-000 .. 000-159


def _theme(md):
    text = " ".join([md.get("name") or ""] + [t.get("name", "") for t in md.get("tags") or []])
    for t, rx in _THEME_RE:
        if rx.search(text):
            return t
    return None


def archmodels(sink, st, per_run=20000):
    """Objaverse buildings, houses and construction scenes by theme; the metadata is scanned once, shard by shard,
    and the matches are kept in the run state."""
    s = session()
    c = st.setdefault("arch", {"scan": 0, "queue": []})
    themes = list(MODEL_THEMES)
    taken = set((sink.state.data.get("catalog") or {}).get("objaverse", {}))
    # 1. scan the 160 metadata shards once (resumable), queueing the matching objects
    while c["scan"] < SHARDS and not sink.full():
        shard = f"000-{c['scan']:03d}"
        m = get(s, f"{HF}/metadata/{shard}.json.gz")
        if not m:
            break
        for uid, md in json.loads(gzip.decompress(m.content)).items():
            lic = (md.get("license") or "").lower()
            if uid in taken or "nc" in lic.split("-") or "nd" in lic.split("-") or not any(x in lic for x in LIC_OK):
                continue
            t = _theme(md)
            if t and split.objaverse_owner(uid, md) == "construction":
                c["queue"].append([uid, shard, themes.index(t), safe(md.get("name") or uid, 70), lic])
        c["scan"] += 1
        c["queue"].sort(key=lambda q: q[2])  # futuristic and new-gen themes first
    # 2. download
    n = 0
    cat = sink.state.data.setdefault("catalog", {}).setdefault("arch_models", {})
    while c["queue"] and n < per_run and not sink.full():
        uid, shard, ti, name, lic = c["queue"].pop(0)
        if split.objaverse_owner(uid, {"name": name}) == "mobility":
            continue  # queued before the split: a road vehicle / road object is the mobility Drive's
        if _download(s, f"{HF}/glbs/{shard}/{uid}.glb", 300 * 2 ** 20, sink, f"{ARCH}/{themes[ti]}/{name} {uid[:8]}.glb"):
            cat[uid] = lic
            n += 1
    return n


IMAGE_THEMES = {
    "Futuristic Architecture": {
        "Photos": ["futuristic architecture", "futuristic building", "neo-futurism architecture", "parametric architecture",
                   "high-tech architecture", "deconstructivism architecture", "biomimetic architecture",
                   "Zaha Hadid architecture", "Heydar Aliyev Center", "Museum of the Future Dubai", "Gardens by the Bay",
                   "The Shard London", "Burj Khalifa", "Marina Bay Sands", "Elbphilharmonie", "City of Arts and Sciences Valencia",
                   "geodesic dome", "green skyscraper", "vertical forest building", "smart city"],
        "Renders & Concepts": ["futuristic city concept art", "futuristic building render", "sci-fi architecture",
                               "future city illustration", "cyberpunk city", "space colony concept", "futuristic house render"],
    },
    "New-Gen House Designs": {
        "Photos": ["modern house", "modern house exterior", "contemporary house", "minimalist house", "modern villa",
                   "luxury modern home", "smart home", "passive house", "eco house", "green roof house", "tiny house",
                   "shipping container house", "prefabricated house", "modular home", "3D printed house",
                   "earth sheltered house", "A-frame house", "timber frame house", "cross laminated timber building",
                   "solar house", "net zero home", "modern cabin", "glass house architecture", "house with pool modern",
                   "modern interior living room", "modern kitchen interior", "open plan interior"],
        "Renders & Concepts": ["modern house render", "house 3d render", "architectural visualization house",
                               "villa rendering", "interior design render", "house floor plan", "house elevation drawing",
                               "isometric house", "house concept design"],
    },
    "Construction": {
        "Photos": ["construction site", "building construction", "skyscraper construction", "house construction",
                   "house framing", "timber frame construction", "concrete pouring", "rebar", "formwork",
                   "steel structure construction", "tower crane", "scaffolding", "construction worker",
                   "excavator construction", "bulldozer", "construction machinery", "road construction",
                   "bridge construction", "tunnel construction", "3D printing construction", "modular construction",
                   "prefabrication factory", "bricklaying", "roofing construction", "drywall installation",
                   "construction safety helmet", "building demolition", "construction aerial view", "foundation construction"],
        "Renders & Concepts": ["construction illustration", "construction site illustration", "building construction 3d render",
                               "construction blueprint", "isometric construction", "BIM model render"],
    },
}
CAP = 40 * 2 ** 20


def _queries():
    for theme, kinds in IMAGE_THEMES.items():
        for kind, qs in kinds.items():
            for q in qs:
                yield theme, kind, q


def _ext(url, default="jpg"):
    e = url.split("?", 1)[0].rsplit(".", 1)[-1].lower()
    return e if e in ("jpg", "jpeg", "png", "tif", "tiff", "webp") else default


def _save(s, sink, url, theme, kind, q, source, title, e):
    if split.building_image_owner(source, title, title) != "construction":
        return 0  # the Asset Library's half of the shared building images, or a road sign (split.py)
    return 1 if _download(s, url, CAP, sink,
                          f"{IMAGES}/{theme}/{kind}/{safe(q.title(), 50)}/{source}/{safe(title, 100)}.{e}") else 0


def _commons(s, sink, pos):
    n = 0
    for theme, kind, q in _queries():
        off = pos.get(q, 0)
        search = f"filetype:{'bitmap' if kind == 'Photos' else 'bitmap|drawing'} {q}"
        while off is not None and off < 9950 and not sink.full():
            r = get(s, "https://commons.wikimedia.org/w/api.php", params={
                "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrsearch": search,
                "gsrlimit": 50, "gsroffset": off, "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": 2560})
            d = r.json() if r else {}
            pages = (d.get("query") or {}).get("pages", {})
            for p in pages.values():
                info = (p.get("imageinfo") or [{}])[0]
                url = info.get("url") or ""
                if info.get("mime") == "image/svg+xml" or info.get("size", 0) > CAP:
                    url = info.get("thumburl") or ""
                if url:
                    title = p.get("title", "").replace("File:", "").rsplit(".", 1)[0]
                    n += _save(s, sink, url, theme, kind, q, "Wikimedia Commons", title, _ext(url, "png"))
            off = (d.get("continue") or {}).get("gsroffset") if pages else None
            pos[q] = off if off is not None else 10000
        if sink.full():
            break
    return n


def _pixabay(s, sink, pos):
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return 0
    n = 0
    for theme, kind, q in _queries():
        page = pos.get(q, 1)
        while page and page <= 3 and not sink.full():  # at most 500 results per search
            r = get(s, "https://pixabay.com/api/", params={
                "key": key, "q": q, "page": page, "per_page": 200, "safesearch": "true",
                "image_type": "photo" if kind == "Photos" else "illustration"})
            res = (r.json().get("hits") or []) if r else []
            for h in res:
                url = h.get("largeImageURL")
                if url:
                    n += _save(s, sink, url, theme, kind, q, "Pixabay", f"{h.get('tags') or h['id']} {h['id']}", _ext(url))
            page = page + 1 if res else 0
            pos[q] = page
            time.sleep(1)
        if sink.full():
            break
    return n


def _openverse(s, sink, pos):
    n = 0
    for theme, kind, q in _queries():
        page = pos.get(q, 1)
        while page and page <= 20 and not sink.full():
            r = get(s, "https://api.openverse.org/v1/images/", tries=3, params={
                "q": q, "page": page, "page_size": 20,
                "category": "photograph" if kind == "Photos" else "illustration,digitized_artwork"})
            res = (r.json().get("results") or []) if r else []
            for it in res:
                if it.get("url"):
                    n += _save(s, sink, it["url"], theme, kind, q, "Openverse",
                               f"{it.get('title') or it['id']} {it['id'][:8]}", _ext(it["url"]))
            page = page + 1 if res else 0
            pos[q] = page
            time.sleep(1.5)  # anonymous rate limit
        if sink.full():
            break
    return n


def archimages(sink, st):
    """Each image source gets its share of the slice, so one slow source cannot starve the others."""
    s = session()
    parts = [_pixabay, _commons, _openverse]
    end = sink.slice_end
    n = 0
    for i, part in enumerate(parts):
        sink.slice_end = time.time() + max(300, (min(end, sink.deadline) - time.time()) / (len(parts) - i))
        n += part(s, sink, st.setdefault(f"arch_{part.__name__[1:]}", {}))
        sink.slice_end = end
    return n


SOURCES = {"archmodels": archmodels, "archimages": archimages}
