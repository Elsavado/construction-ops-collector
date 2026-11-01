"""3D models, CAD drawings and BIM files in every common format (.stl .obj .fbx .3ds .blend .glb .step .ifc .dwg
.dxf .rvt .rfa ...), filed by format under 05 CAD, BIM & 3D Models. Sources: licensed GitHub repositories, BIM sample
model sets, Poly Haven (CC0), Objaverse (by object category) and research CAD datasets (ModelNet, ABC, Fusion 360)."""
import gzip
import json
import os

from .common import get, safe, session
from .github import _gh, _licensed, _search
from .public import BIM, _download, meta_note

MODELS = f"{BIM}/3D Models"

FORMATS = {  # extension: folder
    "stl": "STL (3D printing)", "3mf": "STL (3D printing)", "obj": "OBJ", "mtl": "OBJ", "fbx": "FBX", "3ds": "3DS",
    "max": "3DS", "blend": "Blender (.blend)", "glb": "glTF & GLB", "gltf": "glTF & GLB", "dae": "Collada (.dae)",
    "step": "STEP & IGES (CAD solids)", "stp": "STEP & IGES (CAD solids)", "iges": "STEP & IGES (CAD solids)",
    "igs": "STEP & IGES (CAD solids)", "fcstd": "FreeCAD", "3dm": "Rhino (.3dm)", "skp": "SketchUp",
    "ifc": "IFC (BIM models)", "ifczip": "IFC (BIM models)", "ifcxml": "IFC (BIM models)", "bcf": "BCF (BIM issues)",
    "bcfzip": "BCF (BIM issues)", "dwg": "DWG & DXF (CAD drawings)", "dxf": "DWG & DXF (CAD drawings)",
    "dgn": "DGN (MicroStation)", "rvt": "Revit (RVT, RFA, RTE)", "rfa": "Revit (RVT, RFA, RTE)",
    "rte": "Revit (RVT, RFA, RTE)", "nwd": "Navisworks (NWD, NWC)", "nwc": "Navisworks (NWD, NWC)",
    "ply": "PLY & OFF meshes", "off": "PLY & OFF meshes", "usd": "USD", "usdz": "USD", "usda": "USD",
    "las": "Point clouds (LAS, E57)", "laz": "Point clouds (LAS, E57)", "e57": "Point clouds (LAS, E57)",
    "gbxml": "Energy models (gbXML)", "citygml": "CityGML", "gml": "CityGML",
}
TEXTURES = {"png", "jpg", "jpeg", "tga", "bmp", "tif", "tiff", "exr", "hdr", "dds"}
LFS_PTR = b"version https://git-lfs"


def _ext(path):
    return path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else ""


def _fetch_repo_files(s, sink, repo, branch, tree, dest_of, per_repo, max_mb):
    """Download model files (and textures beside them) from a repository tree. Git LFS files come from the
    media endpoint. Returns the number of model files saved."""
    blobs = [f for f in tree if f.get("type") == "blob" and f.get("size", 0) <= max_mb * 2 ** 20]
    model_dirs = {f["path"].rsplit("/", 1)[0] if "/" in f["path"] else "" for f in blobs if _ext(f["path"]) in FORMATS}
    picks = [f for f in blobs if _ext(f["path"]) in FORMATS][:per_repo]
    picks += [f for f in blobs if _ext(f["path"]) in TEXTURES
              and (f["path"].rsplit("/", 1)[0] if "/" in f["path"] else "") in model_dirs][:per_repo]
    got = 0
    for f in picks:
        if sink.full():
            break
        rel = dest_of(f["path"])
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{f['path']}"
        if not _download(s, url, max_mb * 2 ** 20, sink, rel):
            continue
        p = sink.path(rel)
        with open(p, "rb") as fh:
            head = fh.read(64)
        if head.startswith(LFS_PTR):  # pointer file: fetch the real content over it
            sink.pending -= os.path.getsize(p)
            sink.files -= 1
            _download(s, f"https://media.githubusercontent.com/media/{repo}/{branch}/{f['path']}", max_mb * 2 ** 20,
                      sink, rel)
        if _ext(f["path"]) in FORMATS:
            got += 1
    return got


def _format_dest(repo):
    def dest(path):
        e = _ext(path)
        fmt = FORMATS.get(e)
        if not fmt:  # texture: file it with the first model format in its folder
            fmt = "Textures & Materials"
        return f"{MODELS}/{fmt}/{safe(repo.replace('/', ' - '), 90)}/{path}"
    return dest


REPO_TOPICS = [  # GitHub topics of repositories that hold model files
    "3d-models", "3d-model", "stl", "stl-files", "3d-printing", "3d-printable", "printables", "obj", "wavefront-obj",
    "fbx", "blender-models", "blend-files", "blender-assets", "3ds", "3d-assets", "low-poly", "lowpoly",
    "gltf-models", "glb", "step-files", "cad-models", "freecad-models", "openscad-models", "ifc", "ifc-files",
    "ifc-models", "bim", "bim-models", "revit-family", "revit-families", "dwg", "dxf", "autocad", "sketchup",
    "architecture-models", "building-models", "furniture-models", "point-cloud-data", "photogrammetry",
    "autolisp", "autocad-lisp", "autocad-plugin", "cad-drawings", "cad-blocks", "dxf-files", "dwg-files",
    "librecad", "qcad", "freecad", "cad",
    "architecture-3d", "archviz", "architectural-visualization", "parametric-architecture", "parametric-design",
    "computational-design", "grasshopper3d", "house-design", "house-model", "building-3d", "3d-buildings",
    "sketchup-models", "futuristic", "sci-fi-assets", "construction-3d",
]


def ghmodels(sink, st, per_topic=4, per_repo=400, max_mb=100):
    """Model files from the most-starred licensed GitHub repositories for each 3D / CAD / BIM topic."""
    s = _gh()
    done = st.setdefault("ghm_repos", [])
    done_set = set(done)
    pages = st.setdefault("ghm_page", {})
    n = 0
    for t in REPO_TOPICS:
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
            if name in done_set or not _licensed(repo) or repo.get("fork"):
                continue
            done.append(name)
            done_set.add(name)
            tree = get(s, f"https://api.github.com/repos/{name}/git/trees/{repo['default_branch']}",
                       params={"recursive": "1"})
            files = tree.json().get("tree", []) if tree else []
            got = _fetch_repo_files(s, sink, name, repo["default_branch"], files, _format_dest(name), per_repo, max_mb)
            if got:
                sink.state.data.setdefault("catalog", {})[f"{MODELS}/{name}"] = {
                    "source": repo["html_url"], "license": repo["license"]["spdx_id"], "models": got, "topic": t}
                took += 1
                n += got
    return n


# Curated repositories: BIM sample models, CAD part libraries, public-domain spacecraft models
CURATED = {  # repo: (folder under 05 CAD, BIM & 3D Models, licence note)
    "buildingSMART/Sample-Test-Files": ("BIM Sample Models/buildingSMART sample & test files", "buildingSMART (free)"),
    "buildingSMART/IFC4.3.x-sample-models": ("BIM Sample Models/IFC 4.3 infrastructure samples", "CC BY 4.0"),
    "opensourceBIM/TestFiles": ("BIM Sample Models/BIMserver test files", "see repository"),
    "youshengCode/IfcSampleFiles": ("BIM Sample Models/IFC sample files", "see repository"),
    "IfcOpenShell/files": ("BIM Sample Models/IfcOpenShell test files", "see repository"),
    "xBimTeam/XbimEssentials": ("BIM Sample Models/xBIM test models", "CDDL"),
    "ThatOpen/engine_components": ("BIM Sample Models/That Open test models", "MIT"),
    "andrewisen/bim-whale-ifc-samples": ("BIM Sample Models/IFC samples (bim-whale)", "MIT"),
    "FreeCAD/FreeCAD-library": ("CAD Part Libraries/FreeCAD parts library", "CC BY 3.0"),
    "nasa/NASA-3D-Resources": ("3D Models/NASA 3D resources", "NASA media usage guidelines (public)"),
    "KhronosGroup/glTF-Sample-Assets": ("3D Models/glTF sample assets", "per-asset CC BY / CC0"),
    "KhronosGroup/glTF-Sample-Models": ("3D Models/glTF sample models", "per-asset CC BY / CC0"),
    "alecjacobson/common-3d-test-models": ("3D Models/Common 3D test models", "per-model (research)"),
    "mikedh/trimesh": ("3D Models/trimesh test models", "MIT"),
    "ezdxf/ezdxf": ("CAD Drawings/ezdxf sample drawings", "MIT"),
    "LibreCAD/LibreCAD": ("CAD Drawings/LibreCAD library and samples", "GPL-2.0"),
    "jscad/OpenJSCAD.org": ("CAD Drawings/JSCAD examples", "MIT"),
}


def curated(sink, st, per_repo=3000, max_mb=200):
    """Whole model sets from curated BIM, CAD and 3D repositories (every model file, filed under the set's name)."""
    s = _gh()
    done = st.setdefault("cur_done", {})
    n = 0
    for repo, (folder, lic) in CURATED.items():
        if sink.full():
            break
        r = get(s, f"https://api.github.com/repos/{repo}")
        if not r:
            continue
        info = r.json()
        if done.get(repo) == info.get("pushed_at"):
            continue
        branch = info["default_branch"]
        tree = get(s, f"https://api.github.com/repos/{repo}/git/trees/{branch}", params={"recursive": "1"})
        files = tree.json().get("tree", []) if tree else []
        got = _fetch_repo_files(s, sink, repo, branch, files, lambda p: f"{BIM}/{folder}/{p}", per_repo, max_mb)
        if not sink.full():
            done[repo] = info.get("pushed_at")
        if got:
            meta_note(sink, f"{BIM}/{folder}", {"source": info["html_url"], "license": lic, "models": got})
            n += got
    return n


def polyhaven(sink, st, res="2k"):
    """Poly Haven 3D models (CC0): .blend, .fbx and .gltf with their textures, one folder per model."""
    s = session()
    r = get(s, "https://api.polyhaven.com/assets", params={"t": "models"})
    assets = r.json() if r else {}
    done = st.setdefault("ph_done", [])
    done_set = set(done)
    n = 0
    for aid, info in sorted(assets.items()):
        if aid in done_set or sink.full():
            continue
        fr = get(s, f"https://api.polyhaven.com/files/{aid}")
        files = fr.json() if fr else {}
        cat = safe((info.get("categories") or ["misc"])[0].title(), 40)
        dest = f"{MODELS}/Poly Haven (CC0)/{cat}/{safe(info.get('name') or aid, 80)}"
        got = 0
        for fmt in ("blend", "fbx", "gltf"):
            entry = (files.get(fmt) or {}).get(res) or (files.get(fmt) or {}).get("1k") or {}
            entry = entry.get(fmt) or {}
            if not entry.get("url"):
                continue
            if _download(s, entry["url"], 500 * 2 ** 20, sink, f"{dest}/{fmt}/{entry['url'].rsplit('/', 1)[-1]}"):
                got += 1
            for inc_path, inc in (entry.get("include") or {}).items():
                _download(s, inc["url"], 200 * 2 ** 20, sink, f"{dest}/{fmt}/{inc_path}")
        if got:
            n += 1
        done.append(aid)
        done_set.add(aid)
    if n:
        meta_note(sink, f"{MODELS}/Poly Haven (CC0)", {"source": "https://polyhaven.com/models", "license": "CC0"})
    return n


HF = "https://huggingface.co/datasets/allenai/objaverse/resolve/main"
# Construction, building and site objects first; then every other category
PRIORITY = ("crane", "bulldozer", "tractor", "truck", "dump_truck", "forklift", "ladder", "hammer", "toolbox",
            "drill", "saw", "shovel", "wrench", "screwdriver", "helmet", "traffic_cone", "barrel", "pipe", "brick",
            "door", "window", "staircase", "fence", "bench", "chair", "table", "desk", "sofa", "bed", "cabinet",
            "bookcase", "lamp", "toilet", "sink", "bathtub", "faucet", "refrigerator", "stove", "oven", "washer",
            "radiator", "fan", "air_conditioner", "streetlight", "bridge", "tower", "house", "building", "car")


def objaverse(sink, st, per_run=6000):
    """Objaverse 1.0 objects (.glb) in the LVIS-annotated categories, filed by category; openly licensed only
    (CC BY, CC BY-SA, CC0); licence of every object is in the run catalog."""
    s = session()
    cache = st.setdefault("obja", {})
    if "lvis" not in cache:
        r = get(s, f"{HF}/lvis-annotations.json.gz")
        p = get(s, f"{HF}/object-paths.json.gz")
        if not r or not p:
            return 0
        lvis = json.loads(gzip.decompress(r.content))
        paths = json.loads(gzip.decompress(p.content))
        order = [c for c in PRIORITY if c in lvis] + sorted(c for c in lvis if c not in PRIORITY)
        cache["lvis"] = [[c, [[u, paths[u]] for u in lvis[c] if u in paths]] for c in order]
        cache["pos"] = [0, 0]
    shards = {}
    lic_ok = ("by", "by-sa", "cc0", "public")
    ci, oi = cache["pos"]
    n = 0
    while ci < len(cache["lvis"]) and n < per_run and not sink.full():
        cat, objs = cache["lvis"][ci]
        while oi < len(objs) and n < per_run and not sink.full():
            uid, path = objs[oi]
            oi += 1
            shard = path.split("/")[1]
            if shard not in shards:
                m = get(s, f"{HF}/metadata/{shard}.json.gz")
                shards[shard] = json.loads(gzip.decompress(m.content)) if m else {}
            md = shards[shard].get(uid) or {}
            lic = (md.get("license") or "").lower()
            if "nc" in lic.split("-") or "nd" in lic.split("-") or not any(x in lic for x in lic_ok):
                continue
            if _download(s, f"{HF}/{path}", 300 * 2 ** 20, sink,
                         f"{MODELS}/Objects by Category (Objaverse)/{safe(cat.replace('_', ' ').title(), 60)}/"
                         f"{safe(md.get('name') or uid, 70)} {uid[:8]}.glb"):
                sink.state.data.setdefault("catalog", {}).setdefault("objaverse", {})[uid] = [
                    md.get("viewerUrl") or md.get("uri"), lic, (md.get("user") or {}).get("username")]
                n += 1
        if oi >= len(objs):
            ci, oi = ci + 1, 0
    cache["pos"] = [ci, oi]
    return n


# Research CAD / mesh datasets (direct archives). Very large files stream straight to Drive.
DATASETS = [
    ("modelnet40", f"{MODELS}/Research Datasets/ModelNet40 (Princeton)", "http://modelnet.cs.princeton.edu/ModelNet40.zip",
     "ModelNet40.zip", "Princeton ModelNet (research use)"),
    ("modelnet10", f"{MODELS}/Research Datasets/ModelNet10 (Princeton)",
     "http://3dvision.princeton.edu/projects/2014/3DShapeNets/ModelNet10.zip", "ModelNet10.zip",
     "Princeton ModelNet (research use)"),
    ("f360_recon", f"{MODELS}/Research Datasets/Fusion 360 Gallery - reconstruction",
     "https://fusion-360-gallery-dataset.s3.us-west-2.amazonaws.com/reconstruction/r1.0.1/r1.0.1.zip",
     "r1.0.1.zip", "Fusion 360 Gallery Dataset licence (non-commercial research)"),
    ("f360_seg", f"{MODELS}/Research Datasets/Fusion 360 Gallery - segmentation",
     "https://fusion-360-gallery-dataset.s3.us-west-2.amazonaws.com/segmentation/s2.0.1/s2.0.1.zip",
     "s2.0.1.zip", "Fusion 360 Gallery Dataset licence (non-commercial research)"),
]
ABC_LISTS = {"step": "https://deep-geometry.github.io/abc-dataset/data/step_v00.txt",
             "meta": "https://deep-geometry.github.io/abc-dataset/data/meta_v00.txt"}


def _head_size(s, url):
    try:
        return int(s.head(url, timeout=60, allow_redirects=True).headers.get("Content-Length") or 0)
    except Exception:
        return 0


def cad_datasets(sink, st, abc_chunks=6):
    """ModelNet, Fusion 360 Gallery and the ABC dataset (1M CAD models from Onshape, STEP chunks + metadata)."""
    s = session()
    n = 0
    for key, folder, url, name, lic in DATASETS:
        if st.get(f"cad_{key}") or sink.full():
            continue
        size = _head_size(s, url)
        ok = sink.copyurl(url, f"{folder}/{name}", size) if size > 3 * 2 ** 30 else \
            _download(s, url, 3 * 2 ** 30, sink, f"{folder}/{name}")
        if ok:
            st[f"cad_{key}"] = True
            meta_note(sink, folder, {"source": url, "license": lic})
            n += 1
    pos = st.setdefault("abc_pos", {})
    for kind, list_url in ABC_LISTS.items():
        r = get(s, list_url)
        lines = [ln.split() for ln in (r.text.splitlines() if r else []) if ln.strip()]
        took = 0
        while pos.get(kind, 0) < len(lines) and took < abc_chunks and not sink.full():
            parts = lines[pos.get(kind, 0)]
            url, fname = parts[0], (parts[1] if len(parts) > 1 else parts[0].rsplit("/", 1)[-1])
            size = _head_size(s, url)
            rel = f"{MODELS}/Research Datasets/ABC dataset (Onshape CAD)/{kind.upper()}/{safe(fname, 120)}"
            ok = sink.copyurl(url, rel, size) if size > 3 * 2 ** 30 else _download(s, url, 3 * 2 ** 30, sink, rel)
            pos[kind] = pos.get(kind, 0) + 1
            if ok:
                took += 1
                n += 1
        if took:
            meta_note(sink, f"{MODELS}/Research Datasets/ABC dataset (Onshape CAD)", {
                "source": "https://deep-geometry.github.io/abc-dataset/", "license": "Onshape Terms of Use 1(g)(ii) (public)"})
    return n


SOURCES = {"ghmodels": ghmodels, "curated": curated, "polyhaven": polyhaven, "objaverse": objaverse,
           "caddatasets": cad_datasets}
