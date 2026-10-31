"""Openly licensed courses: complete MIT OpenCourseWare course packages (lecture notes, assignments, exams, videos
where included; CC BY-NC-SA 4.0) for civil engineering, architecture, planning, management and engineering systems."""
import re
import time

from .common import get, safe, session
from .public import COURSE, _download, meta_note

# MIT department id: folder
DEPARTMENTS = {"1": "Civil & Environmental Engineering", "4": "Architecture", "11": "Urban Studies & Planning",
               "15": "Management (Sloan)", "ESD": "Engineering Systems", "IDS": "Data, Systems & Society",
               "2": "Mechanical Engineering", "16": "Aeronautics & Astronautics"}
# Words that mark a course as relevant to construction, design, CAD/BIM, project and business operations
RELEVANT = re.compile(r"construct|build|design|architect|structur|project|cad|comput|model|drawing|survey|geotech|"
                      r"concrete|steel|material|infrastructure|transport|energy|urban|planning|real estate|finance|"
                      r"accounting|operations|management|negotiat|contract|law|systems|sustainab|environment|"
                      r"manufactur|product|visual|digital|fabricat|graphic|engineering", re.I)


def mit_ocw(sink, st, per_run=40, cap=3 * 2 ** 30):
    """Complete course packages from MIT OpenCourseWare, one zip per course, by department."""
    s = session()
    done = st.setdefault("ocw_done", [])
    done_set = set(done)
    offs = st.setdefault("ocw_offset", {})
    n = 0
    for dept, label in DEPARTMENTS.items():
        while n < per_run and not sink.full():
            off = offs.get(dept, 0)
            r = get(s, "https://api.learn.mit.edu/api/v1/courses/",
                    params={"platform": "ocw", "department": dept, "limit": 50, "offset": off})
            res = r.json().get("results", []) if r else []
            if not res:
                offs[dept] = 0
                break
            offs[dept] = off + len(res)
            for c in res:
                url, title = c.get("url") or "", c.get("title") or ""
                if url in done_set or n >= per_run or sink.full():
                    continue
                text = f"{title} {c.get('description') or ''}"
                if not RELEVANT.search(text):
                    done.append(url)
                    done_set.add(url)
                    continue
                time.sleep(1)
                page = get(s, url)
                zips = re.findall(r'href="([^"]+\.zip)"', page.text) if page else []
                if not zips:
                    continue
                z = zips[0] if zips[0].startswith("http") else "https://ocw.mit.edu" + zips[0]
                dest = f"{COURSE}/MIT OpenCourseWare/{label}/{safe(title, 90)}"
                if _download(s, z, cap, sink, f"{dest}/{z.rsplit('/', 1)[-1]}"):
                    meta_note(sink, dest, {"source": url, "title": title, "license": "CC BY-NC-SA 4.0 (MIT OCW)",
                                           "features": c.get("course_feature"),
                                           "description": (c.get("description") or "")[:2000]})
                    n += 1
                done.append(url)
                done_set.add(url)
    return n


SOURCES = {"ocw": mit_ocw}
