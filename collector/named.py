"""Named datasets: specific Kaggle datasets, UCI datasets, and topic searches of the Hugging Face Hub."""
import os

from .common import english, get, safe, session
from .public import (ACC, BIM, COST, ENG, GTM, HAND, HR, LEGAL, MKT, PLAN, SECU, SITE, _download,
                     subtopic)

KAGGLE_DATASETS = {}  # folder: Kaggle dataset refs (topic searches in kaggle.py cover the rest)
KAGGLE_COMPETITIONS = {}


def kaggle_named(sink, st):
    """Specific Kaggle datasets and competition data (a competition needs its rules accepted on the Kaggle account)."""
    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        print("kaggle_named: KAGGLE_API_TOKEN not set, skipped")
        return 0
    s = session()
    s.headers["Authorization"] = f"Bearer {token}"
    done = st.setdefault("kaggle_named", [])
    n = 0
    jobs = [(f, f"datasets/download/{r}", r) for f, refs in KAGGLE_DATASETS.items() for r in refs] + \
           [(f, f"competitions/data/download-all/{c}", c) for f, cs in KAGGLE_COMPETITIONS.items() for c in cs]
    for folder, path, ref in jobs:
        if ref in done or sink.full():
            continue
        if _download(s, f"https://www.kaggle.com/api/v1/{path}", 8 * 2 ** 30, sink,
                     f"{folder}/{safe(ref.replace('/', ' - '), 80)}.zip"):
            done.append(ref)
            n += 1
        else:
            print(f"kaggle_named: {ref} not downloaded (competition rules not accepted, or no access)")
    return n


UCI = {  # UCI Machine Learning Repository id: (name, folder)
    165: ("Concrete compressive strength", f"{SITE}/Materials & Testing"),
    242: ("Energy efficiency", f"{HAND}/Energy & Performance"),
    437: ("Residential building data set", f"{COST}/Cost Data"),
    374: ("Appliances energy prediction", f"{HAND}/Energy & Performance"),
    360: ("Air quality", f"{HAND}/Building Operations"),
    222: ("Bank marketing", f"{GTM}/Sales & CRM"),
    352: ("Online retail", f"{GTM}/Sales & CRM"),
}


def uci(sink, st):
    s = session()
    done = st.setdefault("uci", [])
    n = 0
    for uid, (name, folder) in UCI.items():
        if uid in done or sink.full():
            continue
        slug = name.lower().replace(" ", "+")
        for url in (f"https://archive.ics.uci.edu/static/public/{uid}/{slug}.zip",
                    f"https://archive.ics.uci.edu/static/public/{uid}/data.zip"):
            if _download(s, url, 2 ** 30, sink, f"{folder}/{name} (UCI).zip"):
                done.append(uid)
                n += 1
                break
    return n


HF_SEARCHES = {  # folder: Hugging Face dataset searches
    PLAN: ["construction", "project management", "scheduling"],
    COST: ["construction cost", "bill of quantities", "estimating"],
    SITE: ["construction site", "ppe detection", "hard hat", "crack detection", "construction safety", "concrete",
           "construction equipment", "building damage"],
    HAND: ["building energy", "facility management", "hvac", "smart building"],
    BIM: ["bim", "ifc", "floor plan", "floorplan", "cad", "autocad", "dxf", "cad drawings", "3d models", "objaverse",
          "mesh", "point cloud", "architecture", "building 3d", "shapenet", "thingi10k", "text-to-cad", "sketch cad"],
    ACC: ["financial statements", "sec filings", "10-k", "invoices", "financial reports"],
    LEGAL: ["contracts", "legal", "case law", "building codes", "regulations"],
    HR: ["job postings", "resume", "salaries"],
    ENG: ["code", "github issues", "stack overflow", "software engineering"],
    GTM: ["customer support", "customer service dialogue", "crm", "sales emails"],
    SECU: ["phishing", "cybersecurity"],
    MKT: ["real estate", "housing", "construction industry"],
}
HF_OPEN = {"apache-2.0", "mit", "cc-by-4.0", "cc-by-sa-4.0", "cc0-1.0", "cc-by-3.0", "cc-by-sa-3.0", "odc-by", "odbl",
           "pddl", "bsd-3-clause", "bsd-2-clause", "cdla-permissive-2.0", "cdla-permissive-1.0", "openrail",
           "unlicense", "gpl-3.0", "cc-by-nc-4.0", "cc-by-nc-sa-4.0", "cc-by-2.0", "afl-3.0"}


def huggingface(sink, st, per_query=3, dataset_cap=5 * 2 ** 30):
    """Openly licensed Hugging Face datasets for every company field (resumes mid-dataset on the next run)."""
    s = session()
    if os.environ.get("HF_TOKEN"):
        s.headers["Authorization"] = f"Bearer {os.environ['HF_TOKEN']}"
    api = "https://huggingface.co/api/datasets"
    seen = st.setdefault("hf_seen", [])
    seen_set = set(seen)
    partial = st.setdefault("hf_partial", {})
    n = 0

    def fetch(rid, folder, start):
        r = get(s, f"{api}/{rid}/tree/main", params={"recursive": "true"})
        files = sorted((f for f in (r.json() if r else []) if f.get("type") == "file"
                        and not f["path"].startswith(".") and not f["path"].endswith(".gitattributes")),
                       key=lambda f: f["path"])
        if not files or sum(int(f.get("size") or 0) for f in files) > dataset_cap:
            partial.pop(rid, None)
            return 0
        dest = f"{folder}/{safe(rid.replace('/', ' - '), 100)}"
        for i in range(start, len(files)):
            if sink.full():
                partial[rid] = [folder, i]
                return 0
            _download(s, f"https://huggingface.co/datasets/{rid}/resolve/main/{files[i]['path']}", 3 * 2 ** 30, sink,
                      f"{dest}/{files[i]['path']}")
        partial.pop(rid, None)
        return 1

    for rid, (folder, start) in list(partial.items()):
        n += fetch(rid, folder, start)
    for top, queries in HF_SEARCHES.items():
        for q in queries:
            if sink.full():
                return n
            r = get(s, api, params={"search": q, "sort": "downloads", "limit": 50, "full": "true"})
            took = 0
            for d in (r.json() if r else []):
                if took >= per_query or sink.full():
                    break
                rid = d["id"]
                lic = (d.get("cardData") or {}).get("license")
                lic = (lic[0] if isinstance(lic, list) and lic else lic) or next(
                    (t.split(":", 1)[1] for t in d.get("tags", []) if t.startswith("license:")), "")
                langs = [t.split(":", 1)[1] for t in d.get("tags", []) if t.startswith("language:")]
                if rid in seen_set or d.get("gated") or d.get("private") or str(lic).lower() not in HF_OPEN                         or langs and "en" not in langs or not langs and not english(d.get("description")):
                    continue
                seen.append(rid)
                seen_set.add(rid)
                got = fetch(rid, f"{top}/{subtopic(q)}", 0)
                if got:
                    sink.state.data.setdefault("catalog", {})[f"{top}/{rid}"] = {
                        "source": f"https://huggingface.co/datasets/{rid}", "license": lic, "search": q}
                took += got
                n += got
    return n


SOURCES = {"kaggle_named": kaggle_named, "uci": uci, "huggingface": huggingface}
