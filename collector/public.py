"""Openly licensed public data across every field a construction software company works in."""
import datetime as dt
import os
import re
import shutil
import subprocess
import time

from .common import english, english_zip, get, safe, session

PUB = "Public Data"
PLAN = f"{PUB}/01 Planning & Scheduling"
COST = f"{PUB}/02 Estimating & Cost Control"
SITE = f"{PUB}/03 Site Operations, Safety & Quality"
HAND = f"{PUB}/04 Handover, Facilities & Asset Management"
BIM = f"{PUB}/05 CAD, BIM & 3D Models"
ACC = f"{PUB}/06 Accounting & Finance"
LEGAL = f"{PUB}/07 Legal, Contracts & Compliance"
HR = f"{PUB}/08 HR & Workforce"
ENG = f"{PUB}/09 Software Engineering & Cloud"
GTM = f"{PUB}/10 Sales, Marketing & Customer Success"
SECU = f"{PUB}/11 Security & Data Protection"
SOP = f"{PUB}/12 SOPs, Manuals & Specifications"
COURSE = f"{PUB}/13 Courses & Training"
LIB = f"{PUB}/14 Books & Knowledge Library"
MKT = f"{PUB}/20 Construction Industry & Markets"

OPEN_LICENSES = ("cc-by", "cc0", "cc-zero", "odc", "pddl", "mit", "apache", "bsd", "gpl", "lgpl",
                 "public", "us-pd", "ogl", "etalab", "other-open", "other-pd")

# Topic searches for open dataset catalogues. Each query feeds one topic folder.
SEARCHES = {
    PLAN: ["construction schedule", "project scheduling", "construction delay", "critical path", "resource leveling",
           "construction project management", "construction progress", "earned value"],
    COST: ["construction cost", "cost estimation construction", "bill of quantities", "construction price index",
           "building cost", "change orders", "construction bids", "tender"],
    SITE: ["construction safety", "construction accidents", "occupational injuries construction", "site inspection",
           "construction defects", "concrete strength", "construction equipment", "hard hat detection",
           "construction site images", "crack detection", "building inspection", "construction waste"],
    HAND: ["facility management", "building energy", "building operations", "asset management buildings",
           "maintenance records building", "hvac fault", "building occupancy", "digital twin building"],
    BIM: ["building information modeling", "bim", "ifc", "point cloud building", "3d building models", "floor plans",
          "cad drawings", "architectural drawings", "3d models", "mesh dataset", "lidar building", "photogrammetry"],
    ACC: ["financial statements", "general ledger", "accounting dataset", "invoices", "xbrl", "budget",
          "expense reports", "retention payments"],
    LEGAL: ["construction contracts", "contracts dataset", "court decisions construction", "building codes",
            "construction disputes", "procurement contracts", "regulatory compliance", "gdpr"],
    HR: ["construction workforce", "construction labor", "salaries", "job postings", "employee attrition", "skills",
         "apprenticeship", "prevailing wage"],
    ENG: ["software repositories", "bug reports", "continuous integration", "mobile app offline", "api usage",
          "cloud workloads", "developer productivity"],
    GTM: ["customer support tickets", "crm", "sales pipeline", "customer churn", "saas metrics", "customer reviews"],
    SECU: ["phishing", "intrusion detection", "data breach", "authentication logs", "access control"],
    MKT: ["construction spending", "building permits", "housing starts", "construction industry",
          "infrastructure projects", "construction firms", "construction output", "public works"],
}


def title_query(q):
    """Search term that must appear in the title (Zenodo and CKAN both take Lucene syntax)."""
    words = [w for w in q.split() if w.lower() not in ("dataset", "data", "logs")] or q.split()
    return "title:(" + " AND ".join(words) + ")"


def meta_note(sink, folder, info):
    """Record where a folder's data came from (licence, URL) in the run state, not as a file beside it."""
    sink.state.data.setdefault("catalog", {})[folder] = dict(info, retrieved=dt.date.today().isoformat())


# Search term -> subtopic folder (first match wins, so specific keys come first)
SUBTOPICS = [
    ("construction schedule", "Schedules & Programmes"), ("project scheduling", "Schedules & Programmes"),
    ("critical path", "Schedules & Programmes"), ("resource level", "Resources & Crews"),
    ("delay", "Delays & Disruption"), ("progress", "Progress Tracking"), ("earned value", "Earned Value"),
    ("construction project management", "Project Management"), ("price index", "Price Indices"),
    ("bill of quantities", "Quantities & Takeoff"), ("change order", "Change Orders & Variations"),
    ("bids", "Bids & Tenders"), ("tender", "Bids & Tenders"), ("cost", "Cost Data"),
    ("safety", "Health & Safety"), ("accident", "Health & Safety"), ("injur", "Health & Safety"),
    ("hard hat", "Site Imagery & Computer Vision"), ("site images", "Site Imagery & Computer Vision"),
    ("crack", "Defects & Inspections"), ("defect", "Defects & Inspections"), ("inspection", "Defects & Inspections"),
    ("concrete", "Materials & Testing"), ("equipment", "Plant & Equipment"), ("waste", "Waste & Sustainability"),
    ("energy", "Energy & Performance"), ("hvac", "Building Systems & Faults"), ("occupancy", "Occupancy"),
    ("digital twin", "Digital Twins"), ("maintenance", "Maintenance & Work Orders"),
    ("facility", "Facilities Management"), ("asset", "Asset Registers"), ("operations", "Building Operations"),
    ("building information", "BIM Models & Research"), ("bim", "BIM Models & Research"), ("ifc", "IFC Models"),
    ("point cloud", "Point Clouds & Scans"), ("lidar", "Point Clouds & Scans"),
    ("photogrammetry", "Point Clouds & Scans"), ("floor plan", "Floor Plans & Drawings"),
    ("drawings", "Floor Plans & Drawings"), ("cad", "Floor Plans & Drawings"),
    ("3d building", "3D Buildings & Cities"), ("3d models", "3D Model Collections"), ("mesh", "3D Model Collections"),
    ("financial statements", "Financial Statements"), ("xbrl", "Financial Statements"),
    ("general ledger", "Bookkeeping & Ledgers"), ("accounting", "Bookkeeping & Ledgers"),
    ("invoice", "Invoices & Billing"), ("retention", "Retention & Payment Certificates"), ("expense", "Expenses"),
    ("budget", "Budgeting & Planning"), ("construction contracts", "Construction Contracts"),
    ("procurement", "Procurement"), ("contracts", "Contracts"), ("court", "Case Law & Disputes"),
    ("disputes", "Case Law & Disputes"), ("building codes", "Building Codes"), ("gdpr", "Privacy & Data Protection"),
    ("regulatory", "Regulation & Compliance"), ("apprentice", "Training & Apprenticeships"),
    ("prevailing wage", "Wages & Payroll"), ("salar", "Wages & Payroll"), ("job posting", "Recruiting"),
    ("attrition", "Workforce Analytics"), ("skills", "Skills & Occupations"), ("workforce", "Workforce Analytics"),
    ("labor", "Workforce Analytics"), ("bug", "Bugs & Defects"), ("continuous integration", "CI/CD & DevOps"),
    ("offline", "Mobile & Offline"), ("software repositor", "Code Repositories"), ("api", "APIs"),
    ("cloud", "Cloud Workloads"), ("developer", "Developer Productivity"), ("support ticket", "Customer Support"),
    ("crm", "Sales & CRM"), ("sales", "Sales & CRM"), ("churn", "Customer Success & Churn"), ("saas", "SaaS Metrics"),
    ("reviews", "Customer Feedback"), ("phishing", "Phishing & Fraud"), ("intrusion", "Intrusion Detection"),
    ("breach", "Data Breaches"), ("authentication", "Identity & Access"), ("access control", "Identity & Access"),
    ("spending", "Construction Spending"), ("permit", "Building Permits"), ("housing", "Housing Starts & Completions"),
    ("infrastructure", "Infrastructure Projects"), ("public works", "Infrastructure Projects"),
    ("firms", "Construction Firms"), ("output", "Construction Output"), ("industry", "Industry Statistics"),
]


def subtopic(q):
    ql = q.lower()
    return next((name for key, name in SUBTOPICS if key in ql), q.title())


# ---------- fixed sources ----------

# Data files kept from dataset records, including drawings, BIM and 3D model formats
KEEP_EXT = {"csv", "tsv", "xlsx", "xls", "xlsm", "json", "geojson", "xml", "txt", "log", "pdf", "docx", "doc",
            "pptx", "ppt", "zip", "gz", "parquet", "ipynb", "md", "odt", "ods", "rtf", "jsonl", "7z", "tar", "tgz",
            "ifc", "ifczip", "ifcxml", "bcf", "bcfzip", "dwg", "dxf", "dgn", "rvt", "rfa", "rte", "nwd", "nwc", "nwf",
            "skp", "3dm", "step", "stp", "iges", "igs", "stl", "obj", "mtl", "fbx", "3ds", "blend", "glb", "gltf",
            "dae", "ply", "off", "usd", "usdz", "las", "laz", "e57", "pts", "xer", "mpp", "mpx", "p6xml", "gbxml",
            "citygml", "gml", "kmz", "shp"}


def _download(s, url, cap, sink, rel):
    """Stream url to the sink path; drop it if it is bigger than cap. Returns True when saved."""
    p = sink.path(rel)
    try:
        with s.get(url, stream=True, timeout=180) as r:
            if r.status_code != 200 or int(r.headers.get("Content-Length") or 0) > cap:
                return False
            n = 0
            with open(p, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    n += len(chunk)
                    if n > cap:
                        break
                    f.write(chunk)
        if n > cap or n == 0:
            os.remove(p)
            return False
        if p.lower().endswith(".pdf"):
            with open(p, "rb") as f:
                if not f.read(1024).lstrip().startswith(b"%PDF"):  # a landing page served in place of the PDF
                    os.remove(p)
                    return False
        if p.lower().endswith(".zip"):
            try:
                english_zip(p)  # English only: drop bundled translations
            except Exception:
                pass
        if p.lower().endswith((".htm", ".html")):
            p = html_to_pdf(p)
        sink.wrote(p)
        return True
    except Exception:
        if os.path.exists(p):
            os.remove(p)
        return False


def html_to_pdf(p):
    """Web-page documents (SEC filings, contract exhibits) are kept as PDF; the HTML is removed when it converts."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return p
    outdir = os.path.dirname(p)
    try:
        subprocess.run([soffice, "--headless", "--norestore", "--convert-to", "pdf:writer_web_pdf_Export",
                        "--outdir", outdir, p], capture_output=True, timeout=300)
    except (subprocess.TimeoutExpired, OSError):
        return p
    pdf = os.path.splitext(p)[0] + ".pdf"
    if os.path.exists(pdf) and os.path.getsize(pdf) > 0:
        os.remove(p)
        return pdf
    return p


def _open(lic):
    lic = (lic or "").lower()
    return any(lic.startswith(x) or x in lic for x in OPEN_LICENSES) and "closed" not in lic \
        and "nc" not in lic.split("-")


def zenodo(sink, st, per_query=6, cap=2 * 2 ** 30):
    s = session()
    seen = st.setdefault("zenodo_seen", [])
    seen_set = set(seen)
    pages = st.setdefault("zenodo_page", {})
    n = 0
    for folder, qs in SEARCHES.items():
        for q in qs:
            if sink.full():
                return n
            page = pages.get(q, 1)
            time.sleep(2.5)
            r = get(s, "https://zenodo.org/api/records", params={
                "q": title_query(q), "size": 25, "page": page, "sort": "mostviewed", "access_status": "open"})
            hits = r.json().get("hits", {}).get("hits", []) if r else []
            pages[q] = page + 1 if hits else 1
            took = 0
            for h in hits:
                if took >= per_query or sink.full():
                    break
                rid = str(h["id"])
                md = h.get("metadata", {})
                lic = (md.get("license") or {}).get("id", "")
                if rid in seen_set or not _open(lic) or not english(
                        f"{md.get('title', '')} {re.sub('<[^>]+>', ' ', md.get('description') or '')[:2000]}",
                        md.get("language")):
                    continue
                seen.append(rid)
                seen_set.add(rid)
                files = [f for f in h.get("files", []) if f["key"].rsplit(".", 1)[-1].lower() in KEEP_EXT
                         and f.get("size", 0) <= cap]
                if not files:
                    continue
                dest = f"{folder}/{subtopic(q)}/{safe(md.get('title', rid), 90)}"
                got = 0
                for f in files[:12]:
                    time.sleep(1)
                    if _download(s, f["links"]["self"], cap, sink, f"{dest}/{f['key']}"):
                        got += 1
                if got:
                    meta_note(sink, dest, {"source": "Zenodo", "record": h.get("links", {}).get("self_html"),
                                           "doi": h.get("doi"), "title": md.get("title"),
                                           "license": lic, "search": q,
                                           "description": (md.get("description") or "")[:4000]})
                    took += 1
                    n += 1
    return n


# Searches suited to government open-data portals; every word must be in the dataset name.
PORTAL_SEARCHES = {
    PLAN: ["capital projects", "construction projects", "project schedule", "capital improvement"],
    COST: ["construction contracts", "bid tabulations", "change orders", "construction costs", "unit prices"],
    SITE: ["building inspections", "construction inspections", "code violations", "construction permits",
           "osha inspections", "work zone", "street construction", "elevator inspections"],
    HAND: ["facilities", "building energy", "energy benchmarking", "work orders", "asset inventory",
           "building footprints", "facility condition"],
    BIM: ["building footprints", "3d buildings", "building outlines", "lidar"],
    ACC: ["expenditures", "vendor payments", "capital budget", "general ledger", "purchase orders"],
    LEGAL: ["contracts", "procurement", "debarred contractors", "contractor licenses", "prevailing wage"],
    HR: ["employee salaries", "payroll", "apprenticeship", "workforce", "certified payroll"],
    ENG: ["it projects", "software", "technology spending"],
    GTM: ["311 service requests", "customer service", "customer satisfaction"],
    SECU: ["data breach", "cybersecurity"],
    MKT: ["building permits", "construction permits", "issued permits", "housing units", "new construction",
          "demolition permits", "certificates of occupancy"],
}

STOP = {"for", "of", "and", "the", "it"}


def _open_portal(lic):
    lic = (lic or "").lower()
    if not lic:
        return True  # government portals without a stated licence publish public records
    if "noncommercial" in lic or "non-commercial" in lic or "no derivatives" in lic:
        return False
    return any(x in lic for x in ("public domain", "creative commons", "open data commons", "odc", "open government",
                                  "cc0", "attribution", "open database"))


def opendata(sink, st, per_query=5, cap=1 * 2 ** 30):
    """US city / state / federal open-data portals through the Socrata Discovery API (CSV exports)."""
    s = session()
    seen = st.setdefault("socrata_seen", [])
    seen_set = set(seen)
    offs = st.setdefault("socrata_offset", {})
    n = 0
    for folder, qs in PORTAL_SEARCHES.items():
        for q in qs:
            if sink.full():
                return n
            off = offs.get(q, 0)
            time.sleep(1)
            r = get(s, "https://api.us.socrata.com/api/catalog/v1",
                    params={"q": q, "only": "dataset", "limit": 20, "offset": off, "order": "relevance"})
            res = r.json().get("results", []) if r else []
            offs[q] = off + 20 if res else 0
            want = [w for w in q.lower().split() if w not in STOP] or q.lower().split()
            took = 0
            for x in res:
                if took >= per_query or sink.full():
                    break
                rs, md = x["resource"], x["metadata"]
                key = f"{md['domain']}/{rs['id']}"
                name = rs.get("name") or rs["id"]
                if key in seen_set or not _open_portal(md.get("license")) or not english(
                        f"{name} {(rs.get('description') or '')[:2000]}"):
                    continue
                words = set(re.findall(r"[a-z0-9]+", name.lower()))
                if not all(w in words or w + "s" in words for w in want):
                    continue
                seen.append(key)
                seen_set.add(key)
                dest = f"{folder}/{subtopic(q)}/{safe(name, 80)} ({md['domain']})"
                url = f"https://{md['domain']}/api/views/{rs['id']}/rows.csv?accessType=DOWNLOAD"
                if _download(s, url, cap, sink, f"{dest}/{safe(name, 80)}.csv"):
                    meta_note(sink, dest, {"source": "Socrata open-data portal", "portal": md["domain"],
                                           "dataset": x.get("permalink") or x.get("link"),
                                           "publisher": (x.get("classification") or {}).get("domain_category"),
                                           "license": md.get("license") or "not stated (government open data)",
                                           "updated": rs.get("data_updated_at"), "search": q,
                                           "columns": rs.get("columns_name", [])[:200],
                                           "description": (rs.get("description") or "")[:4000]})
                    took += 1
                    n += 1
    return n


SOURCES = {"zenodo": zenodo, "opendata": opendata}
