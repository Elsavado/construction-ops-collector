"""Sources specific to a construction software company: SEC financial statement data, filings of listed construction
software / contractor / materials companies, real construction contracts filed as SEC exhibits, federal regulations,
case law, occupations data, construction statistics (US, EU) and government construction manuals, SOPs and
specifications."""
import datetime as dt
import html
import os
import re
import time
from urllib.parse import urljoin, urlparse

from .common import get, safe, session
from .public import ACC, COST, HR, LEGAL, MKT, PLAN, SITE, SOP, _download, meta_note

SEC_UA = os.environ.get("SEC_USER_AGENT") or "ConstructionOps research collector hassannoobie@gmail.com"


def _sec():
    s = session()
    s.headers["User-Agent"] = SEC_UA
    return s


def fsds(sink, st, per_run=30):
    """SEC Financial Statement Data Sets: every company's XBRL financial statements, one archive per quarter."""
    s = _sec()
    done = st.setdefault("fsds_done", [])
    today = dt.date.today()
    n = 0
    for y in range(2009, today.year + 1):
        for q in range(1, 5):
            key = f"{y}q{q}"
            if key in done or (y, q) >= (today.year, (today.month - 1) // 3 + 1) or n >= per_run or sink.full():
                continue
            time.sleep(0.5)
            if _download(s, f"https://www.sec.gov/files/dera/data/financial-statement-data-sets/{key}.zip", 2 ** 31,
                         sink, f"{ACC}/SEC Financial Statement Data Sets/{y}/{key} financial statements.zip"):
                done.append(key)
                n += 1
    if n:
        meta_note(sink, f"{ACC}/SEC Financial Statement Data Sets", {
            "source": "SEC DERA Financial Statement Data Sets", "license": "US Government work, public domain",
            "url": "https://www.sec.gov/dera/data/financial-statement-data-sets"})
    return n


# Listed peers by group (tickers; CIKs are looked up from the SEC ticker file)
PEER_GROUPS = {
    "Construction & Design Software": ["PCOR", "ADSK", "TRMB", "BSY", "PTC", "TTAN", "IOT", "MTTR", "BLKB"],
    "General Contractors & Engineering": ["ACM", "FLR", "J", "KBR", "TPC", "GVA", "STRL", "PRIM", "AGX", "ORN",
                                          "MTRX", "ROAD", "TTEK", "WLDN", "BWMN", "NVEE", "GLDD"],
    "Specialty Contractors (MEP, Electrical, Infrastructure)": ["PWR", "EME", "FIX", "MTZ", "DY", "IESC", "LMB",
                                                                 "AMRC", "MYRG"],
    "Homebuilders & Developers": ["LEN", "DHI", "TOL", "PHM", "NVR", "KBH"],
    "Materials, Equipment & Rental": ["VMC", "MLM", "URI", "CAT", "HRI", "EXP", "SUM", "OC"],
}
PEER_FORMS = {"10-K": "Annual reports", "10-K405": "Annual reports", "10-Q": "Quarterly reports",
              "DEF 14A": "Proxy statements", "S-1": "IPO prospectus", "S-1/A": "IPO prospectus",
              "424B4": "IPO prospectus", "20-F": "Annual reports", "8-K": "Current reports"}


def peers(sink, st):
    """Annual, quarterly, current, proxy and IPO filings of listed construction-sector companies."""
    s = _sec()
    r = get(s, "https://www.sec.gov/files/company_tickers.json")
    ciks = {v["ticker"]: (int(v["cik_str"]), v["title"]) for v in (r.json().values() if r else [])}
    done = set(st.setdefault("peer_done", []))
    n = 0
    for group, tickers in PEER_GROUPS.items():
        for t in tickers:
            if t not in ciks or sink.full():
                continue
            cik, title = ciks[t]
            name = safe(title.title(), 60)
            r = get(s, f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
            if not r:
                continue
            rec = r.json()["filings"]["recent"]
            for form, date, acc, doc in zip(rec["form"], rec["filingDate"], rec["accessionNumber"],
                                            rec["primaryDocument"]):
                if form not in PEER_FORMS or not doc or acc in done or sink.full():
                    continue
                if form == "8-K" and date < "2020":
                    continue  # current reports: recent years only
                time.sleep(0.15)
                url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}"
                ext = doc.rsplit(".", 1)[-1].lower() if "." in doc else "htm"
                if _download(s, url, 300 * 2 ** 20, sink,
                             f"{ACC}/Peer Company Filings/{group}/{name}/{PEER_FORMS[form]}/{date} {form}.{ext}"):
                    n += 1
                done.add(acc)
            st["peer_done"] = sorted(done)
    return n


CONTRACT_TYPES = {
    "Construction contracts (owner-contractor)": '"construction contract" OR "construction agreement"',
    "AIA standard form agreements": '"AIA Document" A101 OR A102 OR A201 OR A133',
    "Design-build agreements": '"design-build agreement" OR "design build agreement"',
    "EPC agreements": '"engineering, procurement and construction"',
    "Construction management agreements": '"construction management agreement" OR "construction manager at risk"',
    "Subcontract agreements": '"subcontract agreement"',
    "General contractor agreements": '"general contractor agreement" OR "general contract" construction',
    "Architect & engineering services": '"architectural services agreement" OR "engineering services agreement"',
    "Performance & payment bonds": '"performance bond" "payment bond"',
    "Development agreements": '"development agreement" construction',
    "Joint venture agreements": '"joint venture agreement" construction',
    "Equipment leases & purchases": '"equipment lease agreement" OR "equipment purchase agreement"',
    "Software licence agreements": '"software license agreement"',
    "SaaS & subscription agreements": '"subscription agreement" software',
    "Master services agreements": '"master services agreement"',
    "Professional services agreements": '"professional services agreement"',
    "Employment agreements": '"employment agreement"',
    "Consulting & contractor agreements": '"consulting agreement" OR "independent contractor agreement"',
    "Confidentiality & NDAs": '"confidentiality agreement" OR "non-disclosure agreement"',
    "Office & facility leases": '"office lease" OR "lease agreement" warehouse',
    "Credit & loan agreements": '"credit agreement"',
    "Equity incentive plans": '"equity incentive plan"',
    "Separation agreements": '"separation agreement"',
    "Reseller & distribution agreements": '"reseller agreement" OR "distribution agreement" software',
    "Data processing agreements": '"data processing agreement"',
}


def contracts(sink, st, per_type=60):
    """Real contracts filed as exhibits (EX-10) with SEC filings, found with EDGAR full-text search."""
    s = _sec()
    offs = st.setdefault("contract_from", {})
    seen = set(st.setdefault("contract_seen", []))
    n = 0
    for folder, q in CONTRACT_TYPES.items():
        took, start = 0, offs.get(folder, 0)
        while took < per_type and not sink.full():
            time.sleep(0.3)
            r = get(s, "https://efts.sec.gov/LATEST/search-index", params={"q": q, "from": start})
            hits = (r.json().get("hits", {}).get("hits", []) if r else [])
            if not hits:
                start = 0
                break
            start += len(hits)
            for h in hits:
                src = h.get("_source", {})
                if not str(src.get("file_type", "")).startswith("EX-10") or h["_id"] in seen:
                    continue
                seen.add(h["_id"])
                acc, fname = h["_id"].split(":", 1)
                cik = (src.get("ciks") or ["0"])[0].lstrip("0")
                company = re.sub(r"\s*\(CIK.*", "", (src.get("display_names") or ["Company"])[0])
                url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{fname}"
                ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "htm"
                if _download(s, url, 50 * 2 ** 20, sink, f"{LEGAL}/Contracts (SEC exhibits)/{folder}/"
                             f"{src.get('file_date', '')} {safe(company, 60)} {safe(fname.rsplit('.', 1)[0], 40)}.{ext}"):
                    took += 1
                    n += 1
                if took >= per_type:
                    break
        offs[folder] = start
    st["contract_seen"] = sorted(seen)[-200000:]
    return n


ECFR_TITLES = {29: "Labor (OSHA construction standards, Davis-Bacon)", 48: "Federal Acquisition Regulations",
               2: "Grants and Agreements", 40: "Protection of Environment", 23: "Highways",
               24: "Housing and Urban Development", 10: "Energy", 36: "Parks, Forests and Public Property (ADA/ABA)",
               41: "Public Contracts and Property Management", 49: "Transportation"}


def ecfr(sink, st):
    """Current Code of Federal Regulations titles that govern construction, procurement, labour and safety (XML)."""
    s = session()
    r = get(s, "https://www.ecfr.gov/api/versioner/v1/titles.json")
    if not r:
        return 0
    latest = {t["number"]: t.get("latest_issue_date") for t in r.json().get("titles", [])}
    n = 0
    for num, name in ECFR_TITLES.items():
        date = latest.get(num)
        if not date or st.get(f"ecfr_{num}") == date or sink.full():
            continue
        if _download(s, f"https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{num}.xml", 2 ** 31, sink,
                     f"{LEGAL}/Federal Regulations (eCFR)/Title {num} {safe(name, 60)} ({date}).xml"):
            st[f"ecfr_{num}"] = date
            n += 1
    return n


REPORTERS = {"fed-cl": "Federal Claims Reporter (government contract disputes)", "ct-cl": "Court of Claims Reports",
             "f4th": "Federal Reporter 4th", "f3d": "Federal Reporter 3d", "f-supp-3d": "Federal Supplement 3d",
             "br": "Bankruptcy Reporter"}


def caselaw(sink, st, per_run=150):
    """Court decisions from the Caselaw Access Project (public domain): contract claims, federal and bankruptcy courts."""
    s = session()
    vols = st.setdefault("case_vol", {})
    n = 0
    for rep, name in REPORTERS.items():
        v = vols.get(rep, 1)
        while n < per_run and not sink.full():
            if _download(s, f"https://static.case.law/{rep}/{v}.zip", 2 ** 31, sink,
                         f"{LEGAL}/Case Law/{name}/Volume {v:04d}.zip"):
                n += 1
                v += 1
            else:
                if not get(s, f"https://static.case.law/{rep}/{v + 1}.zip", tries=1, stream=True):
                    break  # end of the reporter
                v += 1
        vols[rep] = v
    if n:
        meta_note(sink, f"{LEGAL}/Case Law", {"source": "Caselaw Access Project (Harvard Law School Library)",
                                              "url": "https://static.case.law", "license": "Public domain / CC0"})
    return n


def onet(sink, st):
    """O*NET occupation database: tasks, skills, knowledge, tools and technology for every job."""
    if st.get("onet"):
        return 0
    s = session()
    for ver in ("30_1", "30_0", "29_3", "29_2"):
        if _download(s, f"https://www.onetcenter.org/dl_files/database/db_{ver}_excel.zip", 2 ** 30, sink,
                     f"{HR}/Occupations & Skills (O-NET)/O-NET database {ver.replace('_', '.')} (Excel).zip"):
            st["onet"] = ver
            meta_note(sink, f"{HR}/Occupations & Skills (O-NET)", {
                "source": "O*NET Resource Center", "license": "CC BY 4.0 (US Department of Labor/ETA)"})
            return 1
    return 0


EUROSTAT = {  # dataset code: (title, folder)
    "sts_copr_m": ("Production in construction, monthly", f"{MKT}/European Construction Statistics"),
    "sts_copr_q": ("Production in construction, quarterly", f"{MKT}/European Construction Statistics"),
    "sts_cobp_m": ("Building permits, monthly", f"{MKT}/European Construction Statistics"),
    "sts_cobp_q": ("Building permits, quarterly", f"{MKT}/European Construction Statistics"),
    "sts_copi_q": ("Construction producer prices and costs, quarterly", f"{COST}/Price Indices"),
    "sts_copi_a": ("Construction producer prices and costs, annual", f"{COST}/Price Indices"),
    "sts_coes_m": ("Employment in construction, monthly", f"{HR}/Workforce Analytics"),
    "sts_cohr_m": ("Hours worked in construction, monthly", f"{HR}/Workforce Analytics"),
    "sts_cowa_m": ("Wages in construction, monthly", f"{HR}/Wages & Payroll"),
    "sbs_ovw_act": ("Enterprise statistics by activity (NACE F construction)", f"{MKT}/Construction Firms"),
    "ei_bsbu_m_r2": ("Construction confidence indicator", f"{MKT}/European Construction Statistics"),
    "hsw_n2_01": ("Non-fatal accidents at work by activity", f"{SITE}/Health & Safety"),
    "hsw_n2_02": ("Fatal accidents at work by activity", f"{SITE}/Health & Safety"),
    "env_wasgen": ("Waste generation by activity", f"{SITE}/Waste & Sustainability"),
    "prc_hpi_q": ("House price index", f"{MKT}/European Construction Statistics"),
}


def eurostat(sink, st):
    """Eurostat construction statistics (EU, UK history, EFTA) as compressed SDMX-CSV, refreshed monthly."""
    s = session()
    n = 0
    for code, (title, folder) in EUROSTAT.items():
        stamp = st.get(f"estat_{code}")
        if sink.full() or stamp and stamp > (dt.date.today() - dt.timedelta(days=30)).isoformat():
            continue
        url = (f"https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{code}"
               "?format=SDMX-CSV&compressed=true")
        if _download(s, url, 2 ** 30, sink, f"{folder}/Eurostat {code} - {safe(title, 70)} {dt.date.today()}.csv.gz"):
            meta_note(sink, f"{folder}/Eurostat {code}", {"source": "Eurostat", "dataset": code, "title": title,
                                                          "license": "CC BY 4.0 (Eurostat reuse policy)"})
            n += 1
        st[f"estat_{code}"] = dt.date.today().isoformat()
    return n


# ---------- page crawls: statistics releases, safety data, manuals, SOPs, specifications ----------
FILE_EXT = r"\.(pdf|xlsx?|xlsm|csv|zip|txt|docx?|pptx?|dwg|dxf|rvt|rfa|ifc|xer|mpp|7z)(\?|$)"

# (key, folder, start page, follow-link regex (same site), file-link regex, max files per run, licence)
CRAWLS = [
    ("census_c30", f"{MKT}/Construction Spending (US Census)", "https://www.census.gov/construction/c30/data/index.html",
     r"/construction/c30/", r"\.(xlsx?|csv|pdf|txt)$", 200, "US Government work, public domain"),
    ("census_nrc", f"{MKT}/Housing Starts & Completions (US Census)",
     "https://www.census.gov/construction/nrc/data/series.html", r"/construction/nrc/", r"\.(xlsx?|csv|pdf|txt)$", 200,
     "US Government work, public domain"),
    ("census_bps", f"{MKT}/Building Permits (US Census)", "https://www2.census.gov/econ/bps/",
     r"^https://www2\.census\.gov/econ/bps/", r"\.(txt|csv|xlsx?|zip)$", 400, "US Government work, public domain"),
    ("census_cpi", f"{COST}/Price Indices", "https://www.census.gov/construction/cpi/index.html",
     r"/construction/cpi/", r"\.(xlsx?|csv|pdf)$", 50, "US Government work, public domain"),
    ("osha_ita", f"{SITE}/Health & Safety/OSHA Injury Tracking Application data",
     "https://www.osha.gov/Establishment-Specific-Injury-and-Illness-Data", r"^$", r"\.(zip|csv|xlsx?)$", 60,
     "US Government work, public domain"),
    ("osha_severe", f"{SITE}/Health & Safety/OSHA Severe Injury Reports", "https://www.osha.gov/severeinjury",
     r"^$", r"\.(zip|csv|xlsx?)$", 20, "US Government work, public domain"),
    ("osha_fatal", f"{SITE}/Health & Safety/OSHA Fatality Inspection Data", "https://www.osha.gov/fatalities",
     r"/fatalities", r"\.(zip|csv|xlsx?|pdf)$", 40, "US Government work, public domain"),
    ("osha_construction", f"{SOP}/Safety Manuals & Programs/OSHA construction publications",
     "https://www.osha.gov/publications/bytype/fact-sheets", r"/publications/", r"\.pdf$", 300,
     "US Government work, public domain"),
    ("niosh_construction", f"{SOP}/Safety Manuals & Programs/NIOSH construction safety",
     "https://www.cdc.gov/niosh/construction/index.html", r"/niosh/(construction|docs)/", r"\.pdf$", 150,
     "US Government work, public domain"),
    ("wbdg_ufc", f"{SOP}/Design & Construction Criteria (UFC)",
     "https://www.wbdg.org/dod/ufc", r"^https://www\.wbdg\.org/(dod/ufc|FFC/DOD/UFC)", r"\.pdf$", 300,
     "US Government work, public domain"),
    ("wbdg_ufgs", f"{SOP}/Construction Specifications (UFGS)", "https://www.wbdg.org/dod/ufgs",
     r"^https://www\.wbdg\.org/(dod/ufgs|FFC/DOD/UFGS)", r"\.(pdf|zip|docx?)$", 400,
     "US Government work, public domain"),
    ("gsa_pbs", f"{SOP}/Facility Standards & Project Delivery (GSA)",
     "https://www.gsa.gov/real-estate/design-and-construction", r"/real-estate/design-and-construction",
     r"\.(pdf|docx?|xlsx?)$", 200, "US Government work, public domain"),
    ("fhwa_construction", f"{SOP}/Highway Construction Manuals (FHWA)",
     "https://www.fhwa.dot.gov/construction/", r"^https://www\.fhwa\.dot\.gov/construction/", r"\.(pdf|docx?|xlsx?)$",
     200, "US Government work, public domain"),
    ("fta_pmo", f"{SOP}/Project Management Oversight (FTA)",
     "https://www.transit.dot.gov/funding/project-management-oversight/project-management-oversight",
     r"/project-management-oversight|/oversight-procedures", r"\.(pdf|docx?|xlsx?)$", 150,
     "US Government work, public domain"),
    ("caltrans_cm", f"{SOP}/State DOT Construction Manuals/Caltrans",
     "https://dot.ca.gov/programs/construction/construction-manual", r"/programs/construction/",
     r"\.(pdf|docx?|xlsx?)$", 200, "California public records"),
    ("txdot_specs", f"{SOP}/State DOT Construction Manuals/TxDOT",
     "https://www.txdot.gov/business/resources/txdot-specifications.html", r"/business/resources/",
     r"\.(pdf|docx?|xlsx?)$", 150, "Texas public records"),
    ("usace_pubs", f"{SOP}/Safety Manuals & Programs/USACE engineer manuals",
     "https://www.publications.usace.army.mil/USACE-Publications/Engineer-Manuals/",
     r"/USACE-Publications/Engineer-Manuals", r"\.pdf$", 200, "US Government work, public domain"),
    ("nist_bfrl", f"{SOP}/Building & Fire Research (NIST)",
     "https://www.nist.gov/el/building-and-fire-research-laboratory-publications", r"^$", r"\.pdf$", 80,
     "US Government work, public domain"),
    ("ukgov_construction", f"{SOP}/UK Government Construction Playbook & Guidance",
     "https://www.gov.uk/government/publications/the-construction-playbook", r"^https://www\.gov\.uk/government/"
     r"(publications|collections)/(the-construction-playbook|.*construction)", r"\.(pdf|docx?|xlsx?|odt)$", 120,
     "Open Government Licence v3.0"),
    ("hse_cdm", f"{SOP}/Safety Manuals & Programs/UK HSE construction (CDM 2015)",
     "https://www.hse.gov.uk/construction/cdm/2015/index.htm", r"^https://www\.hse\.gov\.uk/(construction|pubns)/",
     r"\.pdf$", 120, "Open Government Licence v3.0"),
    ("bsi_iso19650_open", f"{SOP}/BIM Standards & Guidance/buildingSMART",
     "https://technical.buildingsmart.org/standards/", r"^https://technical\.buildingsmart\.org/(standards|resources)",
     r"\.(pdf|zip|xlsx?)$", 100, "buildingSMART International (free publications)"),
]


def _links(page_html, base):
    for href in re.findall(r"""href=["']([^"'#]+)""", page_html, re.I):
        yield urljoin(base, html.unescape(href.strip()))


def crawl(sink, st, max_pages=60):
    """Follow each start page (and same-site pages matching its follow pattern, two levels deep) and download the
    linked data files, manuals and specifications."""
    s = session()
    s.headers["User-Agent"] = "Mozilla/5.0 (research collector; hassannoobie@gmail.com)"
    got_all = st.setdefault("crawl_got", {})
    n = 0
    for key, folder, start, follow, filere, cap, lic in CRAWLS:
        if sink.full():
            break
        stamp = st.get(f"crawl_{key}")
        if stamp and stamp > (dt.date.today() - dt.timedelta(days=30)).isoformat():
            continue
        got = set(got_all.setdefault(key, []))
        host = urlparse(start).netloc
        queue, seen_pages, took = [(start, 0)], {start}, 0
        while queue and took < cap and len(seen_pages) <= max_pages and not sink.full():
            page, depth = queue.pop(0)
            time.sleep(1)
            r = get(s, page, tries=2)
            if not r or "html" not in r.headers.get("Content-Type", "html"):
                continue
            for link in _links(r.text, page):
                path = urlparse(link).path
                if re.search(filere, path, re.I):
                    if link in got or took >= cap or sink.full():
                        continue
                    sub = urlparse(link).path.rsplit("/", 2)
                    name = safe(sub[-1] or "file", 140)
                    time.sleep(0.5)
                    if _download(s, link, 2 ** 30, sink, f"{folder}/{name}"):
                        took += 1
                        n += 1
                    got.add(link)
                elif depth < 2 and follow != "^$" and urlparse(link).netloc == host and re.search(follow, link) \
                        and link not in seen_pages and not re.search(FILE_EXT, link, re.I):
                    seen_pages.add(link)
                    queue.append((link, depth + 1))
        got_all[key] = sorted(got)
        if took:
            meta_note(sink, folder, {"source": start, "license": lic, "files": len(got)})
        if not queue or len(seen_pages) > max_pages:
            st[f"crawl_{key}"] = dt.date.today().isoformat()  # crawl finished: next pass next month
    return n


# Single reference documents (US federal safety, schedule and cost guides)
DOCUMENTS = [
    (f"{SITE}/Health & Safety", "OSHA Construction Industry Digest (OSHA 2202)",
     "https://www.osha.gov/sites/default/files/publications/osha2202.pdf", "US Government work, public domain"),
    (f"{SOP}/Safety Manuals & Programs", "OSHA Job Hazard Analysis (OSHA 3071)",
     "https://www.osha.gov/sites/default/files/publications/osha3071.pdf", "US Government work, public domain"),
    (f"{SOP}/Safety Manuals & Programs", "OSHA Fall Protection in Construction (OSHA 3146)",
     "https://www.osha.gov/sites/default/files/publications/OSHA3146.pdf", "US Government work, public domain"),
    (f"{SOP}/Safety Manuals & Programs", "OSHA Scaffolding guide (OSHA 3150)",
     "https://www.osha.gov/sites/default/files/publications/osha3150.pdf", "US Government work, public domain"),
    (f"{SOP}/Safety Manuals & Programs", "OSHA Excavations (OSHA 2226)",
     "https://www.osha.gov/sites/default/files/publications/osha2226.pdf", "US Government work, public domain"),
    (f"{SOP}/Safety Manuals & Programs", "OSHA Recommended Practices for Safety and Health Programs in Construction",
     "https://www.osha.gov/sites/default/files/OSHA3886.pdf", "US Government work, public domain"),
    (f"{PLAN}/Project Management", "GAO Schedule Assessment Guide (GAO-16-89G)",
     "https://www.gao.gov/assets/gao-16-89g.pdf", "US Government work, public domain"),
    (f"{COST}/Cost Data", "GAO Cost Estimating and Assessment Guide (GAO-20-195G)",
     "https://www.gao.gov/assets/gao-20-195g.pdf", "US Government work, public domain"),]


def documents(sink, st):
    """Single reference documents: OSHA construction safety guides, GAO schedule and cost estimating guides."""
    s = session()
    s.headers["User-Agent"] = "Mozilla/5.0 (research collector; hassannoobie@gmail.com)"
    done = st.setdefault("docs_done", [])
    n = 0
    for folder, title, url, lic in DOCUMENTS:
        if url in done or sink.full():
            continue
        time.sleep(1)
        if _download(s, url, 500 * 2 ** 20, sink, f"{folder}/{safe(title, 120)}.pdf"):
            meta_note(sink, f"{folder}/{title}", {"source": url, "license": lic})
            done.append(url)
            n += 1
    return n


SOURCES = {"fsds": fsds, "peers": peers, "contracts": contracts, "ecfr": ecfr, "caselaw": caselaw, "onet": onet,
           "eurostat": eurostat, "crawl": crawl, "documents": documents}
