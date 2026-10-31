"""GitHub: technical repositories, Jupyter notebooks and open-source apps for a construction software company.

Only licensed repositories are taken. Everything is filed by topic, never by where it came from."""
import os
import re
import time

from .common import english, get, safe, session
from .public import PUB, _download

REPOS = f"{PUB}/15 GitHub Repositories"
NOTEBOOKS = f"{PUB}/16 Jupyter Notebooks"
APPS = f"{PUB}/17 Software & Apps"

REPO_TOPICS = {  # folder: GitHub topics
    "Construction Tech": ["construction", "construction-management", "construction-tech", "contech", "aec",
                          "construction-industry", "site-management", "inspection"],
    "BIM & openBIM": ["bim", "ifc", "openbim", "building-information-modeling", "ifcopenshell", "revit-api",
                      "revit-addin", "dynamo", "navisworks", "bcf"],
    "CAD & Drawings": ["cad", "autocad", "dxf", "dwg", "autolisp", "freecad", "librecad", "opencascade",
                       "parametric-design", "computational-design"],
    "3D, Point Clouds & Reality Capture": ["point-cloud", "photogrammetry", "lidar", "3d-reconstruction",
                                           "gaussian-splatting", "mesh-processing", "webgl", "threejs"],
    "Scheduling & Project Management": ["project-management", "gantt", "gantt-chart", "scheduling",
                                        "critical-path", "resource-planning", "kanban"],
    "Estimating, Cost & Procurement": ["cost-estimation", "estimating", "quantity-takeoff", "procurement",
                                       "invoicing", "budgeting"],
    "Facilities & Digital Twins": ["facility-management", "cmms", "digital-twin", "building-automation",
                                   "bacnet", "smart-building", "asset-management"],
    "Mobile & Offline-first": ["offline-first", "local-first", "crdt", "sync", "pwa", "react-native", "flutter"],
    "GIS & Mapping": ["gis", "geospatial", "cesium", "maplibre", "openlayers"],
    "Site Safety & Computer Vision": ["ppe-detection", "safety-helmet", "crack-detection", "construction-site",
                                      "defect-detection"],
    "ERP, Accounting & HR": ["erp", "accounting", "double-entry-accounting", "hrms", "payroll", "timesheet"],
    "CRM, Support & Documents": ["crm", "helpdesk", "document-management", "pdf-annotation", "e-signature"],
    "SaaS, DevOps & Security": ["multi-tenant", "saas", "devops", "observability", "infrastructure-as-code",
                                "authentication", "saml", "oidc"],
}

NOTEBOOK_TOPICS = {
    "Construction Cost & Delay": ["construction cost", "construction delay", "cost estimation", "project delay"],
    "Construction Safety & Vision": ["construction safety", "ppe detection", "hard hat", "crack detection",
                                     "construction site"],
    "Materials & Structures": ["concrete strength", "structural", "steel"],
    "BIM, CAD & 3D": ["ifc", "bim", "floor plan", "point cloud", "3d mesh", "cad"],
    "Building Energy & Facilities": ["building energy", "hvac", "energy consumption", "predictive maintenance"],
    "Scheduling & Project Analytics": ["project scheduling", "resource allocation", "critical path"],
    "Real Estate & Markets": ["house prices", "real estate", "housing"],
    "Finance & Accounting": ["financial statement analysis", "financial analysis", "invoice"],
    "Customer & HR Analytics": ["customer churn", "employee attrition", "saas metrics"],
}

APPS_LIST = {  # folder: GitHub repositories of open-source apps
    "CAD & Drafting": ["FreeCAD/FreeCAD", "LibreCAD/LibreCAD", "qcad/qcad", "openscad/openscad",
                       "solvespace/solvespace", "jscad/OpenJSCAD.org"],
    "BIM & IFC": ["IfcOpenShell/IfcOpenShell", "opensourceBIM/BIMserver", "xBimTeam/XbimWindowsUI",
                  "ThatOpen/engine_components", "specklesystems/speckle-server"],
    "3D, Meshes & Point Clouds": ["CloudCompare/CloudCompare", "cnr-isti-vclab/meshlab", "OpenDroneMap/ODM",
                                  "potree/potree", "PDAL/PDAL"],
    "Project Management & Scheduling": ["opf/openproject", "makeplane/plane", "kanboard/kanboard",
                                        "leantime/leantime", "frappe/gantt"],
    "Field Data Collection (offline)": ["getodk/collect", "kobotoolbox/kpi", "opendatakit/collect"],
    "Facilities & Maintenance (CMMS)": ["Grashjs/cmms", "snipe/snipe-it"],
    "ERP, Accounting & HR": ["frappe/erpnext", "frappe/hrms", "akaunting/akaunting", "invoiceninja/invoiceninja",
                             "firefly-iii/firefly-iii"],
    "CRM, Support & Documents": ["twentyhq/twenty", "chatwoot/chatwoot", "docusealco/docuseal",
                                 "paperless-ngx/paperless-ngx"],
    "Knowledge & Collaboration": ["outline/outline", "BookStackApp/BookStack", "mattermost/mattermost"],
    "Analytics & BI": ["metabase/metabase", "apache/superset"],
    "Developer Tools & Identity": ["go-gitea/gitea", "keycloak/keycloak", "goauthentik/authentik"],
}
ASSET_OK = re.compile(r"(windows|win64|win-x64|x64\.(msi|exe)|amd64|x86_64|linux64|\.msi$|setup.*\.exe$|\.deb$|"
                      r"\.rpm$|\.appimage$)", re.I)
ASSET_BAD = re.compile(r"(arm|aarch64|i386|i686|386|mips|ppc|s390|riscv|darwin|macos|\.sig$|\.asc$|\.sha\d*|"
                       r"checksums|sbom|\.pem$|\.minisig$|debug|symbols)", re.I)


def _gh():
    s = session()
    if os.environ.get("GITHUB_TOKEN"):
        s.headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    s.headers["Accept"] = "application/vnd.github+json"
    return s


def _search(s, q, page):
    time.sleep(2.2)  # search API: 30 requests a minute
    r = get(s, "https://api.github.com/search/repositories",
            params={"q": q, "sort": "stars", "order": "desc", "per_page": 30, "page": page})
    return r.json().get("items", []) if r else []


def _licensed(repo):
    lic = (repo.get("license") or {}).get("spdx_id")
    return lic and lic != "NOASSERTION"


def repos(sink, st, per_topic=3, max_kb=400 * 1024):
    """Default-branch archives of the most-starred licensed repositories per topic."""
    s = _gh()
    done = st.setdefault("gh_repos", {})
    pages = st.setdefault("gh_repo_page", {})
    n = 0
    for folder, topics in REPO_TOPICS.items():
        for t in topics:
            if sink.full():
                return n
            page = pages.get(t, 1)
            items = _search(s, f"topic:{t} archived:false", page)
            pages[t] = page + 1 if items else 1
            took = 0
            for repo in items:
                if took >= per_topic or sink.full():
                    break
                name = repo["full_name"]
                if name in done or not _licensed(repo) or repo.get("size", 0) > max_kb or repo.get("fork")                         or not english(repo.get("description")):
                    continue
                dest = f"{REPOS}/{folder}/{safe(name.replace('/', ' - '), 100)}.zip"
                if _download(s, f"https://api.github.com/repos/{name}/zipball", 2 * 2 ** 30, sink, dest):
                    sink.state.data.setdefault("catalog", {})[dest] = {
                        "source": repo["html_url"], "license": repo["license"]["spdx_id"],
                        "stars": repo.get("stargazers_count"), "description": (repo.get("description") or "")[:500]}
                    took += 1
                    n += 1
                done[name] = repo.get("pushed_at")
    return n


def notebooks(sink, st, per_query=3, per_repo=60, max_mb=25):
    """Jupyter notebooks (.ipynb) from licensed notebook repositories, with their folder structure."""
    s = _gh()
    done = st.setdefault("nb_repos", [])
    done_set = set(done)
    pages = st.setdefault("nb_page", {})
    n = 0
    for folder, queries in NOTEBOOK_TOPICS.items():
        for q in queries:
            if sink.full():
                return n
            page = pages.get(q, 1)
            items = _search(s, f'{q} language:jupyter-notebook archived:false', page)
            pages[q] = page + 1 if items else 1
            took = 0
            for repo in items:
                if took >= per_query or sink.full():
                    break
                name = repo["full_name"]
                about = " ".join([name, repo.get("description") or "", " ".join(repo.get("topics") or [])]).lower()
                if name in done_set or not _licensed(repo) or not all(w in about for w in q.lower().split())                         or not english(repo.get("description")):
                    continue
                done.append(name)
                done_set.add(name)
                tree = get(s, f"https://api.github.com/repos/{name}/git/trees/{repo['default_branch']}",
                           params={"recursive": "1"})
                files = [f for f in (tree.json().get("tree", []) if tree else [])
                         if f.get("type") == "blob" and f["path"].lower().endswith(".ipynb")
                         and f.get("size", 0) <= max_mb * 2 ** 20]
                got = 0
                for f in files[:per_repo]:
                    url = f"https://raw.githubusercontent.com/{name}/{repo['default_branch']}/{f['path']}"
                    if _download(s, url, max_mb * 2 ** 20, sink,
                                 f"{NOTEBOOKS}/{folder}/{safe(name.replace('/', ' - '), 90)}/{f['path']}"):
                        got += 1
                if got:
                    sink.state.data.setdefault("catalog", {})[f"{NOTEBOOKS}/{folder}/{name}"] = {
                        "source": repo["html_url"], "license": repo["license"]["spdx_id"], "notebooks": got}
                    took += 1
                    n += got
    return n


def apps(sink, st, app_cap=2 * 2 ** 30):
    """Latest release of each app: Windows / Linux x64 installers and packages, else the release source archive.
    A new release replaces nothing; it is added under its own version folder."""
    s = _gh()
    done = st.setdefault("app_release", {})
    n = 0
    for folder, names in APPS_LIST.items():
        for name in names:
            if sink.full():
                return n
            r = get(s, f"https://api.github.com/repos/{name}/releases/latest")
            rel = r.json() if r else None
            if not rel or not rel.get("tag_name"):
                tags = get(s, f"https://api.github.com/repos/{name}/tags", params={"per_page": 1})
                tag = (tags.json() or [{}])[0].get("name") if tags else None
                if not tag:
                    continue
                rel = {"tag_name": tag, "assets": [], "zipball_url": f"https://api.github.com/repos/{name}/zipball/{tag}"}
            tag = rel["tag_name"]
            if done.get(name) == tag:
                continue
            app = name.split("/")[1]
            dest = f"{APPS}/{folder}/{safe(app, 60)}/{safe(tag, 40)}"
            assets = [a for a in rel.get("assets", []) if ASSET_OK.search(a["name"]) and not ASSET_BAD.search(a["name"])]
            total, got = 0, 0
            for a in sorted(assets, key=lambda a: a["size"]):
                total += a["size"]
                if total > app_cap or sink.full():
                    break
                if _download(s, a["browser_download_url"], app_cap, sink, f"{dest}/{a['name']}"):
                    got += 1
            if _download(s, rel.get("zipball_url") or f"https://api.github.com/repos/{name}/zipball/{tag}", app_cap,
                         sink, f"{dest}/{safe(app, 60)}-{safe(tag, 40)}-source.zip"):
                got += 1
            if got:
                done[name] = tag
                sink.state.data.setdefault("catalog", {})[dest] = {"source": f"https://github.com/{name}",
                                                                   "release": tag, "files": got}
                n += 1
    return n


SOURCES = {"ghrepos": repos, "notebooks": notebooks, "apps": apps}
