"""Kaggle datasets with open licences. Listing is anonymous; downloads need KAGGLE_API_TOKEN
(or the older KAGGLE_USERNAME / KAGGLE_KEY pair)."""
import os
import time

from .common import english, get, safe, session
from .public import (ACC, BIM, COST, ENG, GTM, HAND, HR, LEGAL, MKT, PLAN, SECU, SITE, _download,
                     meta_note, subtopic)

SEARCHES = {
    PLAN: ["construction project", "project management", "construction delay", "project schedule", "construction progress"],
    COST: ["construction cost", "building cost", "construction estimate", "construction price", "construction bids",
           "material prices"],
    SITE: ["construction safety", "construction accidents", "osha", "workplace injuries", "ppe detection",
           "hard hat", "construction site", "crack detection", "concrete strength", "construction equipment",
           "construction waste", "building defects"],
    HAND: ["building energy", "facility management", "hvac", "smart building", "building maintenance", "energy consumption buildings"],
    BIM: ["bim", "ifc", "floor plan", "floorplan", "cad", "autocad", "3d models", "3d shapes", "point cloud",
          "architecture", "building footprints", "lidar", "mesh", "stl"],
    ACC: ["financial statements", "accounting", "invoices", "general ledger", "company financials", "budget",
          "expenses"],
    LEGAL: ["contracts", "legal documents", "court cases", "building permits", "regulations"],
    HR: ["construction workers", "construction labor", "employee attrition", "hr analytics", "salaries", "job postings"],
    ENG: ["github repositories", "software bugs", "app reviews", "developer survey", "api"],
    GTM: ["customer support tickets", "customer churn", "crm", "saas", "sales", "customer reviews"],
    SECU: ["phishing", "intrusion detection", "cybersecurity"],
    MKT: ["construction industry", "construction spending", "housing starts", "real estate", "infrastructure",
          "building permits"],
}
OPEN = ("cc0", "cc-by", "cc by", "attribution", "odbl", "open database", "odc", "public domain", "mit",
        "apache", "gpl", "lgpl", "bsd", "community data license", "cdla", "world bank", "us government",
        "open government")


def _ok(lic):
    lic = (lic or "").lower()
    return any(x in lic for x in OPEN) and "noncommercial" not in lic and "nc-" not in lic


def kaggle(sink, st, per_query=3, cap=3 * 2 ** 30):
    token = os.environ.get("KAGGLE_API_TOKEN")
    user, key = os.environ.get("KAGGLE_USERNAME"), os.environ.get("KAGGLE_KEY")
    if not (token or (user and key)):
        print("kaggle: no Kaggle credentials, skipped")
        return 0
    s = session()
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    else:
        s.auth = (user, key)
    seen = st.setdefault("kaggle_seen", [])
    seen_set = set(seen)
    pages = st.setdefault("kaggle_page", {})
    n = 0
    for folder, qs in SEARCHES.items():
        for q in qs:
            if sink.full():
                return n
            page = pages.get(q, 1)
            time.sleep(1)
            r = get(s, "https://www.kaggle.com/api/v1/datasets/list",
                    params={"search": q, "sortBy": "votes", "page": page})
            res = r.json() if r else []
            pages[q] = page + 1 if res else 1
            took = 0
            for d in res:
                if took >= per_query or sink.full():
                    break
                ref = d.get("ref", "")
                if not ref or ref in seen_set or not _ok(d.get("licenseName")) or d.get("totalBytes", 0) > cap                         or not english(f"{d.get('title') or ''} {d.get('subtitle') or ''}"):
                    continue
                seen.append(ref)
                seen_set.add(ref)
                dest = f"{folder}/{subtopic(q)}/{safe(d.get('title') or ref, 80)}"
                time.sleep(1)
                if _download(s, f"https://www.kaggle.com/api/v1/datasets/download/{ref}", cap, sink,
                             f"{dest}/{safe(ref.replace('/', ' - '), 100)}.zip"):
                    meta_note(sink, dest, {"source": "Kaggle", "dataset": f"https://www.kaggle.com/datasets/{ref}",
                                           "title": d.get("title"), "subtitle": d.get("subtitle"),
                                           "license": d.get("licenseName"), "updated": d.get("lastUpdated"),
                                           "votes": d.get("voteCount"), "downloads": d.get("downloadCount"),
                                           "search": q})
                    took += 1
                    n += 1
    return n


SOURCES = {"kaggle": kaggle}
