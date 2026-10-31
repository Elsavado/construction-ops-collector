"""Construction project records that the fictional company's customers keep on its platform (shared as anonymised
sample workspaces): Primavera-style schedules (.xer), progress updates, cost reports, change orders, payment
applications with retention, daily site logs, RFIs, submittals, inspections, punch lists, safety observations,
photo registers tied to drawing coordinates, drawing and model registers (ISO 19650 names), simple IFC models and
DXF floor plans, and handover packages. All synthetic."""
import datetime as dt
import math
import random

from .common import add_sheet, new_book, safe, save_book

# project types: (category, typical value USD millions (lo, hi), months (lo, hi), storeys (lo, hi))
PROJECT_TYPES = {
    "Office building": ("building", (12, 180), (14, 32), (4, 22)),
    "Hospital wing": ("building", (40, 320), (20, 40), (3, 9)),
    "Secondary school": ("building", (15, 70), (12, 24), (2, 4)),
    "Mixed-use residential tower": ("building", (30, 260), (18, 38), (8, 34)),
    "Apartment block": ("building", (8, 60), (12, 24), (4, 12)),
    "Logistics warehouse": ("building", (10, 90), (8, 16), (1, 2)),
    "Data center": ("building", (60, 450), (14, 30), (1, 4)),
    "Hotel": ("building", (25, 200), (16, 32), (5, 20)),
    "Airport terminal extension": ("building", (80, 600), (24, 48), (2, 4)),
    "University laboratory": ("building", (30, 150), (16, 30), (3, 7)),
    "Bridge rehabilitation": ("civil", (5, 80), (8, 26), (0, 0)),
    "Highway interchange": ("civil", (30, 350), (18, 42), (0, 0)),
    "Water treatment plant": ("civil", (20, 220), (18, 40), (0, 0)),
    "Rail station upgrade": ("civil", (25, 260), (18, 40), (0, 0)),
    "Solar farm and substation": ("civil", (15, 160), (9, 20), (0, 0)),
    "Wastewater pipeline": ("civil", (8, 90), (10, 28), (0, 0)),
}
PLACE_A = """Harbor River Cedar Granite North Lakeside Summit Meadow Willow Ridge Westfield Brookside Kingsway Elm
Parkview Station Union Crescent Foundry Mill Quarry Orchard Beacon Market Canal Dockside Hillcrest Eastgate Lindenhof
Ashford Riverside Larchmont Highgate Maple Juniper Ironworks Southbank Kestrel""".split()

FORMS = {  # region: contract forms
    "Americas": ["AIA A101 stipulated sum", "AIA A102 cost plus fee with GMP", "AIA A141 design-build",
                 "ConsensusDocs 200", "EJCDC C-520 (public works)"],
    "Europe": ["NEC4 ECC Option A (priced, activity schedule)", "NEC4 ECC Option C (target cost)",
               "JCT Design and Build 2016", "FIDIC Red Book 2017", "UAV-GC 2005 (Dutch integrated)"],
    "Africa": ["FIDIC Red Book 2017", "FIDIC Yellow Book 2017", "JBCC Principal Building Agreement",
               "PPADA public works contract", "NEC4 ECC Option B (priced, bill of quantities)"],
}
CSI = [("01", "General requirements", .09), ("02", "Existing conditions", .02), ("03", "Concrete", .14),
       ("04", "Masonry", .03), ("05", "Metals", .09), ("06", "Wood, plastics and composites", .02),
       ("07", "Thermal and moisture protection", .05), ("08", "Openings", .05), ("09", "Finishes", .08),
       ("10", "Specialties", .01), ("14", "Conveying equipment", .03), ("21", "Fire suppression", .02),
       ("22", "Plumbing", .04), ("23", "HVAC", .09), ("26", "Electrical", .09), ("27", "Communications", .02),
       ("28", "Electronic safety and security", .01), ("31", "Earthwork", .04), ("32", "Exterior improvements", .03),
       ("33", "Utilities", .03), ("99", "Contingency", .02)]
ELEMENTAL = [("0", "Facilitating works", .02), ("1", "Substructure", .10), ("2.1", "Frame", .13),
             ("2.2", "Upper floors", .05), ("2.3", "Roof", .04), ("2.4", "Stairs and ramps", .01),
             ("2.5", "External walls", .09), ("2.6", "Windows and external doors", .05),
             ("2.7", "Internal walls and partitions", .04), ("3", "Internal finishes", .07), ("4", "Fittings", .02),
             ("5", "Services", .23), ("8", "External works", .04), ("P", "Main contractor's preliminaries", .09),
             ("OH", "Overheads and profit", .05), ("R", "Risk allowance", .03)]
CIVIL = [("100", "Preliminaries and site establishment", .10), ("200", "Site clearance and demolition", .03),
         ("300", "Earthworks", .14), ("400", "Drainage and ducts", .09), ("500", "Piling and foundations", .12),
         ("600", "Structures and concrete", .18), ("700", "Pavements and surfacing", .10),
         ("800", "Mechanical and electrical", .11), ("900", "Traffic management and signage", .04),
         ("950", "Landscaping and reinstatement", .03), ("990", "Contingency", .06)]

PHASES = {
    "building": [
        ("Preconstruction", ["Contract award and mobilisation", "Site set-up and hoarding", "Building permit issued",
                             "Utility diversions"]),
        ("Substructure", ["Excavation and shoring", "Piling", "Pile caps and ground beams", "Basement slab",
                          "Waterproofing"]),
        ("Superstructure", ["Core walls level {n}", "Columns and slab level {n}"]),
        ("Envelope", ["Roof structure", "Roofing membrane", "Facade panels", "Curtain wall", "Windows and doors"]),
        ("MEP rough-in", ["Mechanical rough-in level {n}", "Electrical rough-in level {n}", "Plumbing risers",
                          "Fire sprinkler mains"]),
        ("Interiors", ["Drywall and partitions level {n}", "Ceilings", "Flooring", "Joinery", "Painting"]),
        ("Fit-out and commissioning", ["Lifts installed", "HVAC commissioning", "Fire alarm testing",
                                       "Building management system", "Electrical testing"]),
        ("External works", ["Hard landscaping", "Soft landscaping", "Car park surfacing"]),
        ("Handover", ["Punch list / snagging", "O&M manuals and as-builts", "Training of operators",
                      "Certificate of occupancy", "Practical completion"]),
    ],
    "civil": [
        ("Preconstruction", ["Contract award and mobilisation", "Environmental permits", "Traffic management plan",
                             "Site compound"]),
        ("Enabling works", ["Site clearance", "Utility relocations", "Temporary works design"]),
        ("Earthworks", ["Topsoil strip section {n}", "Cut and fill section {n}", "Ground improvement"]),
        ("Drainage", ["Culverts section {n}", "Stormwater network", "Outfalls"]),
        ("Structures", ["Piling and foundations structure {n}", "Piers and abutments structure {n}",
                        "Deck / main slab structure {n}", "Bearings and joints"]),
        ("Systems", ["Mechanical installation", "Electrical and SCADA", "Commissioning and testing"]),
        ("Pavements and finishing", ["Sub-base", "Base course", "Surfacing", "Road markings and signage",
                                     "Barriers and fencing"]),
        ("Handover", ["Defects inspection", "As-built surveys", "O&M manuals", "Taking-over certificate"]),
    ],
}
TRADES = ["Labourers", "Carpenters", "Concrete finishers", "Steel fixers", "Ironworkers", "Electricians", "Plumbers",
          "HVAC fitters", "Drywall installers", "Painters", "Equipment operators", "Surveyors", "Scaffolders"]
EQUIP = ["Tower crane", "Mobile crane", "Excavator", "Backhoe loader", "Concrete pump", "Telehandler", "Scissor lift",
         "Dump truck", "Roller", "Generator", "Boom lift", "Piling rig"]
WEATHER = ["Clear", "Clear", "Partly cloudy", "Overcast", "Light rain", "Heavy rain", "Windy", "Hot", "Cold"]
DISCIPLINES = [("A", "Architectural"), ("S", "Structural"), ("M", "Mechanical"), ("E", "Electrical"),
               ("P", "Plumbing"), ("C", "Civil"), ("L", "Landscape"), ("FP", "Fire protection")]


def _rng(*key):
    return random.Random("-".join(str(k) for k in key))


def new_project(rng, cust, ym, pid, region, city):
    kind = rng.choice(list(PROJECT_TYPES))
    cat, (vlo, vhi), (mlo, mhi), (slo, shi) = PROJECT_TYPES[kind]
    value = round(math.exp(rng.uniform(math.log(vlo), math.log(vhi))) * 1e6, -3)
    months = rng.randint(mlo, mhi)
    return {"id": pid, "code": f"{cust['code']}-P{pid % 1000:03d}", "cust": cust["id"],
            "name": f"{rng.choice(PLACE_A)} {rng.choice(PLACE_A)} {kind}".replace("  ", " "), "type": kind,
            "cat": cat, "value": value, "start": ym, "months": months, "storeys": rng.randint(slo, shi) if shi else 0,
            "form": rng.choice(FORMS[region]), "retention": rng.choice([0.05, 0.05, 0.10, 0.03]),
            "region": region, "city": city, "spi": rng.uniform(0.86, 1.04), "cpi": rng.uniform(0.93, 1.03),
            "units": "Imperial" if region == "Americas" else "Metric",
            "abbr": "".join(w[0] for w in kind.split()[:2]).upper() + f"{pid % 100:02d}"}


# ---------------------------------------------------------------- schedule

def _passes(acts):
    by = {a["id"]: a for a in acts}
    for a in acts:  # forward pass (predecessors always come earlier in the list)
        es = 0
        for pid, typ, lag in a["preds"]:
            q = by[pid]
            es = max(es, (q["ef"] if typ == "FS" else q["es"]) + lag)
        a["es"], a["ef"] = es, es + a["dur"]
    finish = max(a["ef"] for a in acts)
    succ = {a["id"]: [] for a in acts}
    for a in acts:
        for pid, typ, lag in a["preds"]:
            succ[pid].append((a["id"], typ, lag))
    for a in reversed(acts):  # backward pass
        lf = finish
        for sid, typ, lag in succ[a["id"]]:
            s = by[sid]
            lf = min(lf, (s["ls"] if typ == "FS" else s["ls"] + a["dur"]) - lag)
        a["lf"], a["ls"] = lf, lf - a["dur"]
        a["tf"] = a["ls"] - a["es"]
    return finish


def build_schedule(p):
    """Activities with WBS, durations (working days), predecessors, early/late dates and total float. Each phase
    runs as two overlapping chains, phases overlap start-to-start, open ends tie into the completion milestone, and
    durations are scaled so the programme fits the project's planned months."""
    r = _rng("sched", p["code"])
    target = int(p["months"] * 21.5)
    reps = max(1, p["storeys"]) if p["cat"] == "building" else r.randint(2, 5)
    acts, phase_acts = [], []
    for wi, (phase, names) in enumerate(PHASES[p["cat"]], 1):
        items = []
        for nm in names:
            items += [nm.format(n=n) for n in range(1, min(reps, 14) + 1)] if "{n}" in nm else [nm]
        ids = []
        for j, nm in enumerate(items):
            aid = f"A{(len(acts) + 1) * 10:05d}"
            mile = nm.lower().startswith(("contract award", "building permit", "certificate", "practical completion",
                                          "taking-over"))
            dur = 0 if mile else max(2, int(r.uniform(8, 45)))
            preds = []
            if j == 0:
                if phase_acts:
                    prev = phase_acts[-1]
                    if phase == "Handover":
                        preds.append((prev[-1], "FS", 0))
                    else:
                        preds.append((prev[0], "SS", r.randint(10, 40)))
            elif j == 1:
                preds.append((ids[0], "SS" if not mile else "FS", 0 if mile else r.randint(2, 10)))
            else:
                preds.append((ids[j - 2], "FS", 0))
                if r.random() < .4 or mile:
                    preds.append((ids[j - 1], "FS" if mile else "SS", 0 if mile else r.randint(2, 8)))
            acts.append({"id": aid, "wbs": f"{p['abbr']}.{wi}", "phase": phase, "name": nm, "dur": dur,
                         "preds": preds})
            ids.append(aid)
        phase_acts.append(ids)
    has_succ = {q for a in acts for q, _, _ in a["preds"]}
    last = acts[-1]
    for a in acts[:-1]:  # open ends finish into the completion milestone
        if a["id"] not in has_succ and all(q != a["id"] for q, _, _ in last["preds"]):
            last["preds"].append((a["id"], "FS", 0))
    finish = _passes(acts)
    for _ in range(3):  # fit the programme to the planned duration
        f = target / max(finish, 1)
        for a in acts:
            if a["dur"]:
                a["dur"] = max(1, int(round(a["dur"] * f)))
            a["preds"] = [(q, t, int(round(lag * f))) for q, t, lag in a["preds"]]
        finish = _passes(acts)
    return acts, finish


def wd_date(start, n):
    """Date n working days (Mon-Fri) after start."""
    d = start
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    full, rem = divmod(n, 5)
    d += dt.timedelta(weeks=full)
    while rem:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            rem -= 1
    return d


def xer(p, acts, start, cust_name, banner):
    """Primavera P6 XER export (tab-delimited tables PROJECT, PROJWBS, TASK, TASKPRED)."""
    out = [f"ERMHDR\t19.12\t{start}\tProject\tadmin\tadmin\tdbxDatabaseNoName\tProject Management\tUSD"]

    def table(name, fields, rows):
        out.append(f"%T\t{name}")
        out.append("%F\t" + "\t".join(fields))
        for row in rows:
            out.append("%R\t" + "\t".join(str(v) for v in row))

    pid = 1000 + p["id"]
    table("PROJECT", ["proj_id", "proj_short_name", "proj_name", "plan_start_date", "scd_end_date", "clndr_id",
                      "last_recalc_date", "notes"],
          [[pid, p["code"], p["name"], f"{start} 08:00", f"{wd_date(start, max(a['ef'] for a in acts))} 17:00", 1,
            f"{start} 08:00", f"{cust_name}; {banner}"]])
    phases = sorted({(a["wbs"], a["phase"]) for a in acts})
    table("PROJWBS", ["wbs_id", "proj_id", "wbs_short_name", "wbs_name", "parent_wbs_id"],
          [[pid * 100 + i, pid, w, ph, pid * 100] for i, (w, ph) in enumerate(phases, 1)])
    wid = {w: pid * 100 + i for i, (w, _) in enumerate(phases, 1)}
    table("TASK", ["task_id", "proj_id", "wbs_id", "task_code", "task_name", "task_type", "target_drtn_hr_cnt",
                   "early_start_date", "early_end_date", "late_start_date", "late_end_date", "total_float_hr_cnt",
                   "driving_path_flag"],
          [[pid * 1000 + i, pid, wid[a["wbs"]], a["id"], a["name"], "TT_Mile" if a["dur"] == 0 else "TT_Task",
            a["dur"] * 8, f"{wd_date(start, a['es'])} 08:00", f"{wd_date(start, a['ef'])} 17:00",
            f"{wd_date(start, a['ls'])} 08:00", f"{wd_date(start, a['lf'])} 17:00", a["tf"] * 8,
            "Y" if a["tf"] <= 0 else "N"] for i, a in enumerate(acts, 1)])
    tix = {a["id"]: pid * 1000 + i for i, a in enumerate(acts, 1)}
    rows, k = [], 1
    for a in acts:
        for q, typ, lag in a["preds"]:
            rows.append([pid * 10000 + k, tix[a["id"]], tix[q], pid, pid, f"PR_{typ}", lag * 8])
            k += 1
    table("TASKPRED", ["task_pred_id", "task_id", "pred_task_id", "proj_id", "pred_proj_id", "pred_type",
                       "lag_hr_cnt"], rows)
    out.append("%E")
    return "\r\n".join(out) + "\r\n"


# ---------------------------------------------------------------- simple BIM and CAD files

def ifc_model(p, cust_name, org, banner):
    """A small IFC4 model: site, building, storeys, a rectangular slab and four walls per storey."""
    r = _rng("ifc", p["code"])
    w_, d_ = r.choice([(30, 18), (42, 24), (60, 30), (24, 16), (80, 40)])
    h = 3.6
    lines, n = [], [0]

    def e(txt):
        n[0] += 1
        lines.append(f"#{n[0]}={txt};")
        return n[0]

    def guid():
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
        return "".join(r.choice(chars) for _ in range(22))

    person = e("IFCPERSON($,'Coordinator','BIM',$,$,$,$,$)")
    org_ = e(f"IFCORGANIZATION($,'{org}',$,$,$)")
    po = e(f"IFCPERSONANDORGANIZATION(#{person},#{org_},$)")
    app = e(f"IFCAPPLICATION(#{org_},'1.0','Synthetic model generator','SYNTH')")
    own = e(f"IFCOWNERHISTORY(#{po},#{app},$,.ADDED.,$,$,$,0)")
    o = e("IFCCARTESIANPOINT((0.,0.,0.))")
    zdir, xdir = e("IFCDIRECTION((0.,0.,1.))"), e("IFCDIRECTION((1.,0.,0.))")
    ax = e(f"IFCAXIS2PLACEMENT3D(#{o},#{zdir},#{xdir})")
    ctx = e(f"IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#{ax},$)")
    body = e(f"IFCGEOMETRICREPRESENTATIONSUBCONTEXT('Body','Model',*,*,*,*,#{ctx},$,.MODEL_VIEW.,$)")
    u1, u2, u3 = e("IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)"), e("IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.)"), \
        e("IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.)")
    units = e(f"IFCUNITASSIGNMENT((#{u1},#{u2},#{u3}))")
    proj = e(f"IFCPROJECT('{guid()}',#{own},'{p['code']}','{p['name']} - {banner}',$,$,$,(#{ctx}),#{units})")
    lp0 = e(f"IFCLOCALPLACEMENT($,#{ax})")
    site = e(f"IFCSITE('{guid()}',#{own},'Site',$,$,#{lp0},$,$,.ELEMENT.,$,$,$,$,$)")
    bldg = e(f"IFCBUILDING('{guid()}',#{own},'{p['name'][:60]}',$,$,#{lp0},$,$,.ELEMENT.,$,$,$)")
    e(f"IFCRELAGGREGATES('{guid()}',#{own},$,$,#{proj},(#{site}))")
    e(f"IFCRELAGGREGATES('{guid()}',#{own},$,$,#{site},(#{bldg}))")
    storeys = []

    def box(x, y, z, lx, ly, lz):
        pt = e(f"IFCCARTESIANPOINT(({x:.3f},{y:.3f},{z:.3f}))")
        pl = e(f"IFCAXIS2PLACEMENT3D(#{pt},#{zdir},#{xdir})")
        lp = e(f"IFCLOCALPLACEMENT(#{lp0},#{pl})")
        c2 = e(f"IFCCARTESIANPOINT(({lx / 2:.3f},{ly / 2:.3f}))")
        p2 = e(f"IFCAXIS2PLACEMENT2D(#{c2},$)")
        prof = e(f"IFCRECTANGLEPROFILEDEF(.AREA.,$,#{p2},{lx:.3f},{ly:.3f})")
        sol = e(f"IFCEXTRUDEDAREASOLID(#{prof},#{ax},#{zdir},{lz:.3f})")
        rep = e(f"IFCSHAPEREPRESENTATION(#{body},'Body','SweptSolid',(#{sol}))")
        shape = e(f"IFCPRODUCTDEFINITIONSHAPE($,$,(#{rep}))")
        return lp, shape

    for lv in range(max(1, min(p["storeys"] or 2, 12))):
        z = lv * h
        sp = e(f"IFCCARTESIANPOINT((0.,0.,{z:.3f}))")
        spl = e(f"IFCAXIS2PLACEMENT3D(#{sp},#{zdir},#{xdir})")
        slp = e(f"IFCLOCALPLACEMENT(#{lp0},#{spl})")
        st = e(f"IFCBUILDINGSTOREY('{guid()}',#{own},'Level {lv:02d}',$,$,#{slp},$,$,.ELEMENT.,{z:.3f})")
        storeys.append(st)
        elems = []
        lp, sh = box(0, 0, z, w_, d_, 0.25)
        elems.append(e(f"IFCSLAB('{guid()}',#{own},'Slab L{lv:02d}',$,$,#{lp},#{sh},$,.FLOOR.)"))
        for k, (x, y, lx, ly) in enumerate([(0, 0, w_, 0.3), (0, d_ - 0.3, w_, 0.3), (0, 0, 0.3, d_),
                                            (w_ - 0.3, 0, 0.3, d_)]):
            lp, sh = box(x, y, z + 0.25, lx, ly, h - 0.25)
            elems.append(e(f"IFCWALL('{guid()}',#{own},'External wall L{lv:02d}-{k + 1}',$,$,#{lp},#{sh},$,.STANDARD.)"))
        rooms = r.randint(2, 6)
        for k in range(rooms):
            elems.append(e(f"IFCSPACE('{guid()}',#{own},'{lv:02d}{k + 1:02d}','"
                           f"{r.choice(['Office', 'Meeting room', 'Plant room', 'Corridor', 'Store', 'WC', 'Ward', 'Classroom'])}'"
                           f",$,$,$,$,.ELEMENT.,.INTERNAL.,$)"))
        e(f"IFCRELCONTAINEDINSPATIALSTRUCTURE('{guid()}',#{own},$,$,({','.join(f'#{x}' for x in elems)}),#{st})")
    e(f"IFCRELAGGREGATES('{guid()}',#{own},$,$,#{bldg},({','.join(f'#{x}' for x in storeys)}))")
    head = ["ISO-10303-21;", "HEADER;",
            f"FILE_DESCRIPTION(('ViewDefinition [ReferenceView]','{banner}'),'2;1');",
            f"FILE_NAME('{p['code']}.ifc','{dt.date.today()}T00:00:00',('BIM Coordinator'),('{org}'),"
            f"'Synthetic','Synthetic model generator','');", "FILE_SCHEMA(('IFC4'));", "ENDSEC;", "DATA;"]
    return "\n".join(head + lines + ["ENDSEC;", "END-ISO-10303-21;"]) + "\n"


def dxf_plan(p, banner):
    """DXF (R12 ASCII) general-arrangement floor plan: grid lines, walls, room labels and a title block."""
    r = _rng("dxf", p["code"])
    nx, ny = r.randint(4, 9), r.randint(3, 6)
    bay = 7.5 if p["units"] == "Metric" else 25.0
    out = ["0", "SECTION", "2", "ENTITIES"]

    def line(x1, y1, x2, y2, layer):
        out.extend(["0", "LINE", "8", layer, "10", f"{x1:.3f}", "20", f"{y1:.3f}", "30", "0.0",
                    "11", f"{x2:.3f}", "21", f"{y2:.3f}", "31", "0.0"])

    def text(x, y, h, s, layer):
        out.extend(["0", "TEXT", "8", layer, "10", f"{x:.3f}", "20", f"{y:.3f}", "30", "0.0", "40", f"{h:.2f}",
                    "1", s])

    W, H = nx * bay, ny * bay
    for i in range(nx + 1):
        line(i * bay, -bay * .3, i * bay, H + bay * .3, "S-GRID")
        text(i * bay - .5, H + bay * .4, bay * .08, chr(65 + i), "S-GRID-IDEN")
    for j in range(ny + 1):
        line(-bay * .3, j * bay, W + bay * .3, j * bay, "S-GRID")
        text(-bay * .6, j * bay - .3, bay * .08, str(j + 1), "S-GRID-IDEN")
    for x1, y1, x2, y2 in [(0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)]:
        line(x1, y1, x2, y2, "A-WALL-EXTR")
    for i in range(1, nx):
        if r.random() < .5:
            line(i * bay, 0, i * bay, H * r.uniform(.4, 1), "A-WALL-INTR")
    for k in range(r.randint(4, 10)):
        x, y = r.uniform(.1, .85) * W, r.uniform(.1, .85) * H
        text(x, y, bay * .06, r.choice(["OFFICE", "MEETING", "PLANT", "STORE", "WC", "LOBBY", "STAIR", "LIFT"]) +
             f" {k + 1:02d}", "A-AREA-IDEN")
    text(0, -bay * 1.2, bay * .1, f"{p['code']} {p['name'][:50]} - GA PLAN LEVEL 00", "A-ANNO-TTLB")
    text(0, -bay * 1.5, bay * .06, banner[:120], "A-ANNO-TTLB")
    out.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(out) + "\n"


def doc_number(p, org, disc, typ, n, level="ZZ", volume="ZZ"):
    """ISO 19650 container name: Project-Originator-Volume-Level-Type-Role-Number."""
    return f"{p['abbr']}-{org}-{volume}-{level}-{typ}-{disc}-{n:04d}"


# ---------------------------------------------------------------- month of site records

class SiteMonth:
    def __init__(self, m, p, cust):
        self.m, self.p, self.c = m, p, cust
        self.r = _rng("site", p["code"], m.tag)
        self.start = dt.date(p["start"][0], p["start"][1], 1)
        self.acts, self.finish = build_schedule(p)
        self.base = f"{m.F['cpd']}/{safe(cust['name'], 50)}/{safe(p['code'] + ' ' + p['name'], 80)}"
        self.org = "".join(w[0] for w in cust["name"].split()[:3]).upper()[:3] or "GCX"
        k = (m.ym[0] - p["start"][0]) * 12 + m.ym[1] - p["start"][1]
        self.k, self.n_months = k, p["months"]
        self.codes = CSI if p["region"] == "Americas" and p["cat"] == "building" else \
            ELEMENTAL if p["cat"] == "building" else CIVIL
        self.cur = {"Americas": "USD", "Europe": "EUR", "Africa": "USD"}[p["region"]]

    def drawing_register(self):
        """The project's drawings (same list every month: photo pins refer to these sheets)."""
        p, r = self.p, _rng("dwg", self.p["code"])
        drawings = []
        for disc, dname in DISCIPLINES:
            if p["cat"] == "civil" and disc in ("A", "L", "FP") and r.random() < .5:
                continue
            for i in range(1, r.randint(6, 30)):
                lvl = r.choice(["ZZ", "00", "01", "02", "B1", "RF"]) if p["cat"] == "building" else "ZZ"
                drawings.append([doc_number(p, self.org, disc, "DR", i, lvl), dname,
                                 r.choice(["General arrangement", "Sections", "Details", "Schedules", "Setting out",
                                           "Elevations", "Reflected ceiling plan", "Single line diagram"]),
                                 lvl, "P01", r.choice(["S2 Suitable for information", "S3 Suitable for review",
                                                      "S4 Suitable for stage approval", "A1 Accepted for construction"]),
                                 self.start.isoformat(), r.choice(["1:50", "1:100", "1:200", "1:500", "1:20"])])
        return drawings

    def wd(self, n):
        return wd_date(self.start, n)

    def planned_pct(self, a, date):
        s, f = self.wd(a["es"]), self.wd(a["ef"])
        if date < s:
            return 0.0
        if date >= f or a["dur"] == 0:
            return 100.0
        return round(100 * (date - s).days / max((f - s).days, 1), 1)

    def run(self):
        m, p = self.m, self.p
        if self.k == 0:
            self.kickoff()
        self.progress()
        self.daily_logs()
        self.site_records()
        self.cost()
        if self.k >= self.n_months - 2:
            self.handover(final=self.k == self.n_months - 1)
        if self.k >= self.n_months - 1:
            m.L.get("site", {}).pop(p["code"], None)  # finished: drop its running state

    # project set-up: schedule, budget, registers, models
    def kickoff(self):
        m, p, c = self.m, self.p, self.c
        sink = m.sink
        sink.write_text(f"{self.base}/01 Schedule/{p['code']} baseline programme.xer",
                        xer(p, self.acts, self.start, c["name"], m.BANNER))
        sink.write_text(f"{self.base}/04 Drawings & Models/Models/{doc_number(p, self.org, 'A', 'M3', 1)}.ifc",
                        ifc_model(p, c["name"], c["name"], m.BANNER))
        sink.write_text(f"{self.base}/04 Drawings & Models/Drawings/{doc_number(p, self.org, 'A', 'DR', 1, '00')}.dxf",
                        dxf_plan(p, m.BANNER))
        r = self.r
        drawings = self.drawing_register()
        models = [[doc_number(p, self.org, d, "M3", 1), dn, "IFC4" if d != "C" else "IFC4.3",
                   r.choice(["LOD 300", "LOD 350", "LOD 400"]), "Work in progress", self.start.isoformat()]
                  for d, dn in DISCIPLINES[:5]]
        wb = new_book()
        add_sheet(wb, "Drawing register", ["Document number (ISO 19650)", "Discipline", "Title", "Level", "Revision",
                                           "Status code", "Issued", "Scale"], drawings,
                  {"Document number (ISO 19650)": 34, "Status code": 30})
        add_sheet(wb, "Model register", ["Container", "Discipline", "Schema", "Level of development", "State",
                                         "Created"], models, {"Container": 34})
        save_book(m.sink, f"{self.base}/04 Drawings & Models/Information register (TIDP-MIDP).xlsx", wb, "Register",
                  m.BANNER)
        rows = []
        for code, name, share in self.codes:
            amt = round(p["value"] * share * r.uniform(.85, 1.15), 2)
            rows.append([code, name, amt])
        wb = new_book()
        ws = add_sheet(wb, "Baseline budget", ["Cost code", "Description", f"Budget {self.cur}"], rows,
                       {"Description": 40})
        n = ws.max_row
        ws.cell(n + 1, 2, "TOTAL")
        ws[f"C{n + 1}"] = f"=SUM(C2:C{n})"
        save_book(m.sink, f"{self.base}/02 Cost/{p['code']} baseline budget.xlsx", wb, "Budget", m.BANNER)

    # schedule update with actual progress
    def progress(self):
        m, p, r = self.m, self.p, self.r
        date = m.eom
        rows = []
        lag = (1 - p["spi"]) * 0.6
        for a in self.acts:
            plan = self.planned_pct(a, date)
            act = max(0.0, min(100.0, plan * (1 - lag) + r.uniform(-4, 4))) if plan else 0.0
            if plan >= 100 and r.random() < .8:
                act = 100.0
            rows.append([m.tag, a["id"], a["wbs"], a["phase"], a["name"], a["dur"], self.wd(a["es"]).isoformat(),
                         self.wd(a["ef"]).isoformat(), a["tf"], "Yes" if a["tf"] <= 0 else "No", plan, round(act, 1),
                         round(act - plan, 1)])
        wb = new_book()
        add_sheet(wb, "Progress update", ["Data date", "Activity", "WBS", "Phase", "Activity name",
                                          "Original duration (d)", "Baseline start", "Baseline finish",
                                          "Total float (d)", "Critical", "Planned %", "Actual %", "Variance %"], rows,
                  {"Activity name": 38, "Phase": 24})
        save_book(m.sink, f"{self.base}/01 Schedule/{m.y}/Progress update {m.tag}.xlsx", wb, "Progress", m.BANNER)
        tot = sum(a["dur"] for a in self.acts) or 1
        self.pct_plan = sum(x[10] * x[5] for x in rows) / tot
        self.pct_act = sum(x[11] * x[5] for x in rows) / tot
        self.live = [x for x in rows if 0 < x[11] < 100] or rows[:3]

    def daily_logs(self):
        m, p, r = self.m, self.p, self.r
        rows, crews = [], []
        size = max(8, int(p["value"] / 1.2e6))
        for d in range(m.days):
            day = m.d0 + dt.timedelta(days=d)
            if day.weekday() == 6 or (day.weekday() == 5 and r.random() < .7):
                continue
            wx = r.choice(WEATHER)
            lost = r.choice([0, 0, 0, 2, 4, 8]) if wx in ("Heavy rain", "Windy") else 0
            work = r.sample(self.live, min(3, len(self.live)))
            heads = 0
            for t in r.sample(TRADES, r.randint(3, 7)):
                n = max(1, int(size / 6 * r.uniform(.3, 1.6)))
                heads += n
                crews.append([day.isoformat(), t, r.choice(["Own forces", f"{r.choice(PLACE_A)} Subcontracting",
                                                            f"{r.choice(PLACE_A)} {t.split()[0]} Ltd"]), n,
                              round(n * (8 - lost / 2) * r.uniform(.9, 1.1), 1)])
            rows.append([day.isoformat(), wx, r.randint(-5, 36) if p["units"] == "Metric" else r.randint(23, 97),
                         heads, ", ".join(r.sample(EQUIP, 3)), "; ".join(w[4] for w in work), lost,
                         r.choice(["", "", "", "Late concrete delivery", "Crane down for inspection",
                                   "Waiting for RFI response", "Utility strike - no injury", "Inspector visit",
                                   "Material shortage", "Access road closed"]),
                         r.choice(["Site manager", "Superintendent", "Site engineer"]),
                         "Mobile (offline, synced later)" if r.random() < .35 else "Mobile (online)"])
        wb = new_book()
        add_sheet(wb, "Daily log", ["Date", "Weather", "Temp", "Workers on site", "Main equipment", "Work done",
                                    "Hours lost (weather)", "Delays and events", "Author", "Entry source"], rows,
                  {"Work done": 60, "Delays and events": 30, "Main equipment": 36})
        add_sheet(wb, "Labour", ["Date", "Trade", "Company", "Workers", "Hours"], crews, {"Company": 30})
        save_book(m.sink, f"{self.base}/03 Site/{m.y}/Daily site logs {m.tag}.xlsx", wb, "Daily log", m.BANNER)
        self.workdays = len(rows)

    def site_records(self):
        m, p, r = self.m, self.p, self.r
        tag = m.tag.replace("-", "")
        rfis, subs, insp, punch, safety, photos = [], [], [], [], [], []
        discs = [d for d, _ in DISCIPLINES]
        for i in range(r.randint(2, 14)):
            opened = m.d0 + dt.timedelta(days=r.randrange(m.days))
            ans = opened + dt.timedelta(days=int(r.lognormvariate(1.8, .6)))
            rfis.append([f"RFI-{tag}-{i + 1:03d}", opened.isoformat(), r.choice(discs),
                         r.choice(["Clash between duct and beam at grid C/4", "Confirm slab edge setting-out",
                                   "Missing door hardware schedule", "Conflict between spec and drawing finish",
                                   "Embed plate details for facade brackets", "Rebar congestion at column head",
                                   "Drainage invert level discrepancy", "Fire stopping detail at riser"]),
                         r.choice(["Architect", "Structural engineer", "MEP engineer", "Client"]),
                         ans.isoformat() if ans <= m.eom else "", "Answered" if ans <= m.eom else "Open",
                         r.choice(["No", "No", "Yes - cost", "Yes - time", "Yes - cost and time"])])
        for i in range(r.randint(3, 18)):
            subs.append([f"SUB-{tag}-{i + 1:03d}", r.choice([c[1] for c in self.codes]),
                         r.choice(["Shop drawings", "Product data", "Samples", "Method statement", "Test certificates",
                                   "Calculations"]), (m.d0 + dt.timedelta(days=r.randrange(m.days))).isoformat(),
                         r.choice(["Approved", "Approved as noted", "Revise and resubmit", "Under review", "Rejected"])])
        for i in range(r.randint(4, 20)):
            d = m.d0 + dt.timedelta(days=r.randrange(m.days))
            res = r.choices(["Pass", "Pass with comments", "Fail"], [70, 20, 10])[0]
            insp.append([f"ITP-{tag}-{i + 1:03d}", d.isoformat(),
                         r.choice(["Pre-pour inspection", "Rebar inspection", "Waterproofing test", "Pressure test",
                                   "Fire stopping inspection", "Drywall pre-close", "Electrical continuity test",
                                   "Concrete cube test", "Compaction test", "Weld inspection"]),
                         r.choice(self.live)[4], res, r.choice(["Site engineer", "Third-party inspector",
                                                                "Client representative", "Building control"]),
                         "Yes" if res == "Fail" else "No"])
        if self.pct_act > 55:
            for i in range(r.randint(5, 60)):
                d = m.d0 + dt.timedelta(days=r.randrange(m.days))
                lvl = f"Level {r.randint(0, max(p['storeys'], 1)):02d}" if p["cat"] == "building" else f"Section {r.randint(1, 6)}"
                punch.append([f"PL-{tag}-{i + 1:04d}", d.isoformat(), lvl,
                              r.choice(["Paint touch-up", "Damaged ceiling tile", "Missing skirting", "Door closer adjust",
                                        "Sealant gap at window", "Socket not labelled", "Loose handrail",
                                        "Scratched glazing", "Leaking trap", "Grout missing"]),
                              r.choice([t for t in TRADES]), r.choice(["Open", "Open", "Ready for inspection", "Closed"]),
                              (d + dt.timedelta(days=r.randint(3, 21))).isoformat()])
        for i in range(r.randint(3, 25)):
            d = m.d0 + dt.timedelta(days=r.randrange(m.days))
            sev = r.choices(["Observation", "Near miss", "First aid", "Medical treatment", "Lost time"],
                            [60, 22, 12, 5, 1])[0]
            safety.append([f"HS-{tag}-{i + 1:03d}", d.isoformat(), sev,
                           r.choice(["Missing edge protection", "Unsecured ladder", "Worker without hard hat",
                                     "Housekeeping - trip hazard", "Excavation without shoring", "Overhead load path",
                                     "Hot works permit missing", "Good practice: exclusion zone set up",
                                     "Hand laceration", "Slip on wet surface", "Dust exposure", "Struck by falling object"]),
                           r.choice(TRADES), r.choice(["Toolbox talk", "Area closed and fixed", "Permit issued",
                                                       "Disciplinary warning", "Investigation opened"]),
                           "Yes" if sev in ("Medical treatment", "Lost time") else "No"])
        sheets = [x[0] for x in self.drawing_register()]
        for i in range(r.randint(40, 260)):
            t = dt.datetime.combine(m.d0 + dt.timedelta(days=r.randrange(m.days)), dt.time(r.randint(7, 17),
                                                                                         r.randrange(60)))
            off = r.random() < .3
            sync = t + dt.timedelta(minutes=r.randint(1, 600) if off else r.randint(0, 2))
            photos.append([f"IMG_{tag}_{i + 1:05d}.jpg", t.isoformat(), r.choice(sheets), round(r.uniform(.02, .98), 4),
                           round(r.uniform(.02, .98), 4), r.choice(["Progress", "Progress", "Defect", "Safety",
                                                                   "Inspection", "Delivery"]),
                           "Yes" if off else "No", sync.isoformat(),
                           r.choices(["None", "Auto-merged", "Manual review"], [93, 6, 1])[0] if off else "None"])
        wb = new_book()
        add_sheet(wb, "RFIs", ["RFI", "Opened", "Discipline", "Question", "To", "Answered", "Status", "Impact"], rfis,
                  {"Question": 44})
        add_sheet(wb, "Submittals", ["Submittal", "Package", "Type", "Submitted", "Status"], subs, {"Package": 32})
        add_sheet(wb, "Inspections & tests", ["Inspection", "Date", "Type", "Activity", "Result", "Inspector",
                                              "NCR raised"], insp, {"Activity": 36, "Type": 26})
        if punch:
            add_sheet(wb, "Punch list", ["Item", "Raised", "Location", "Description", "Trade", "Status", "Due"], punch,
                      {"Description": 30})
        add_sheet(wb, "Health & safety", ["Record", "Date", "Category", "Description", "Trade", "Action", "Reportable"],
                  safety, {"Description": 36, "Action": 24})
        save_book(m.sink, f"{self.base}/03 Site/{m.y}/Site registers {m.tag}.xlsx", wb, "Site registers", m.BANNER)
        wb = new_book()
        add_sheet(wb, "Photo register", ["File", "Captured", "Drawing sheet", "X (0-1 of sheet)", "Y (0-1 of sheet)",
                                         "Category", "Captured offline", "Synced", "Sync conflict"], photos,
                  {"Drawing sheet": 34})
        save_book(m.sink, f"{self.base}/03 Site/{m.y}/Photo register {m.tag}.xlsx", wb, "Photos", m.BANNER)
        m.site_counts = getattr(m, "site_counts", {"rfi": 0, "photos": 0, "offline": 0, "conflicts": 0, "lti": 0})
        m.site_counts["rfi"] += len(rfis)
        m.site_counts["photos"] += len(photos)
        m.site_counts["offline"] += sum(1 for x in photos if x[6] == "Yes")
        m.site_counts["conflicts"] += sum(1 for x in photos if x[8] != "None")
        m.site_counts["lti"] += sum(1 for x in safety if x[2] == "Lost time")

    def cost(self):
        m, p, r = self.m, self.p, self.r
        st = m.L.setdefault("site", {}).setdefault(p["code"], {"changes": [], "billed": 0.0, "co_no": 0})
        for _ in range(r.randint(0, 4)):
            st["co_no"] += 1
            amt = round(p["value"] * r.uniform(-.002, .012), 2)
            st["changes"].append([f"CO-{st['co_no']:04d}", m.tag, r.choice([c[0] for c in self.codes]),
                                  r.choice(["Client-requested scope change", "Unforeseen ground conditions",
                                            "Design development", "Value engineering saving",
                                            "Authority requirement", "Provisional sum adjustment"]), amt,
                                  r.choice(["Approved", "Approved", "Pending", "Rejected"]),
                                  r.choice([0, 0, 0, 5, 10, 15])])
        frac = self.pct_act / 100
        rows = []
        for i, (code, name, share) in enumerate(self.codes, 2):
            bud = round(p["value"] * share, 2)
            chg = round(sum(c[4] for c in st["changes"] if c[2] == code and c[5] == "Approved"), 2)
            committed = round((bud + chg) * min(1, frac * 1.6 + .15) * r.uniform(.95, 1.02), 2)
            actual = round((bud + chg) * frac / p["cpi"] * r.uniform(.96, 1.04), 2)
            rows.append([code, name, bud, chg, f"=C{i}+D{i}", committed, actual,
                         round((bud + chg) / p["cpi"] * r.uniform(.98, 1.03), 2), f"=E{i}-H{i}"])
        wb = new_book()
        ws = add_sheet(wb, "Cost report", ["Cost code", "Description", "Original budget", "Approved changes",
                                           "Revised budget", "Committed", "Actual to date", "Forecast at completion",
                                           "Variance"], rows, {"Description": 36})
        n = ws.max_row
        ws.cell(n + 1, 2, "TOTAL")
        for col in "CDEFGHI":
            ws[f"{col}{n + 1}"] = f"=SUM({col}2:{col}{n})"
        add_sheet(wb, "Change orders", ["Change", "Month", "Cost code", "Reason", f"Amount {self.cur}", "Status",
                                        "Time impact (days)"], st["changes"], {"Reason": 34})
        save_book(m.sink, f"{self.base}/02 Cost/{m.y}/Cost report {m.tag}.xlsx", wb, "Cost report", m.BANNER)
        # payment application / interim certificate
        contract = p["value"] + sum(c[4] for c in st["changes"] if c[5] == "Approved")
        lines = []
        for i, (code, name, share) in enumerate(self.codes, 2):
            sv = round(contract * share, 2)
            prev = round(sv * min(1, max(0, frac - .05 * r.random())) * .97, 2) if self.k else 0.0
            this = max(0.0, round(sv * frac - prev, 2))
            lines.append([code, name, sv, prev, this, round(sv * .004 * r.random(), 2), f"=D{i}+E{i}+F{i}",
                          f"=IF(C{i}=0,0,G{i}/C{i})", f"=C{i}-G{i}", f"=G{i}*{p['retention']}"])
        wb = new_book()
        is_us = p["region"] == "Americas"
        ws = add_sheet(wb, "Continuation sheet" if is_us else "Valuation",
                       ["Item", "Description", "Scheduled value", "Previous applications", "This period",
                        "Materials stored", "Total completed and stored", "% complete", "Balance to finish",
                        "Retainage"], lines, {"Description": 36})
        n = ws.max_row
        ws.cell(n + 1, 2, "TOTALS")
        for col in "CDEFGIJ":
            ws[f"{col}{n + 1}"] = f"=SUM({col}2:{col}{n})"
        ws.cell(n + 3, 2, "Amount due this application (less retainage)")
        ws[f"G{n + 3}"] = f"=E{n + 1}+F{n + 1}-E{n + 1}*{p['retention']}-F{n + 1}*{p['retention']}"
        title = (f"Application for payment No. {self.k + 1} (AIA G702/G703 style)" if is_us
                 else f"Interim payment certificate No. {self.k + 1} ({p['form'].split()[0]})")
        save_book(m.sink, f"{self.base}/02 Cost/{m.y}/{title.split(' (')[0]} {m.tag}.xlsx", wb, title, m.BANNER)

    def handover(self, final):
        m, p, r = self.m, self.p, self.r
        systems = (["Air handling unit", "Chiller", "Boiler", "Fire alarm panel", "Sprinkler valve set", "Lift",
                    "Generator", "UPS", "Distribution board", "Booster pump", "BMS controller", "Access control panel",
                    "LED luminaire", "Fan coil unit", "Water heater"] if p["cat"] == "building" else
                   ["Pump station", "Valve chamber", "SCADA RTU", "Transformer", "Switchgear", "Bridge bearing",
                    "Expansion joint", "Street light", "CCTV camera", "Variable message sign", "Flow meter"])
        assets = []
        for i in range(r.randint(40, 400)):
            sysn = r.choice(systems)
            inst = m.d0 - dt.timedelta(days=r.randint(10, 200))
            assets.append([f"{p['abbr']}-AS-{i + 1:05d}", sysn, f"{sysn} type {r.choice('ABCDEF')}",
                           f"Level {r.randint(0, max(p['storeys'], 1)):02d}" if p["cat"] == "building" else
                           f"Zone {r.randint(1, 8)}",
                           f"{r.choice(PLACE_A)} {r.choice(['Industries', 'Systems', 'Controls', 'Engineering'])}",
                           f"M{r.randint(100, 9999)}", f"SN{r.getrandbits(32):08X}", inst.isoformat(),
                           (inst + dt.timedelta(days=365 * r.choice([1, 2, 5, 10]))).isoformat(),
                           r.choice(["Monthly", "Quarterly", "Six-monthly", "Annual"])])
        docs = [[doc_number(p, self.org, r.choice(["M", "E", "P", "FP", "A"]), "OM", i + 1),
                 r.choice(["Operation and maintenance manual", "Warranty certificate", "Test and commissioning record",
                           "As-built drawing", "Fire strategy", "Health and safety file", "Spare parts list",
                           "Training record"]), r.choice(["Received", "Received", "Under review", "Outstanding"]),
                 (m.d0 + dt.timedelta(days=r.randrange(m.days))).isoformat()] for i in range(r.randint(20, 120))]
        wb = new_book()
        add_sheet(wb, "Asset register (COBie style)", ["Component", "System", "Type", "Space / location",
                                                      "Manufacturer", "Model", "Serial number", "Installed",
                                                      "Warranty end", "Maintenance frequency"], assets,
                  {"System": 22, "Type": 26, "Manufacturer": 26})
        add_sheet(wb, "Handover documents", ["Document (ISO 19650)", "Type", "Status", "Date"], docs,
                  {"Document (ISO 19650)": 34, "Type": 34})
        save_book(m.sink, f"{self.base}/05 Handover/Handover registers {m.tag}.xlsx", wb, "Handover", m.BANNER)
        if final:
            C = m.C
            d = C.new_doc(f"Practical completion / taking-over certificate - {p['name']}",
                          f"{p['code']} | {p['form']} | {m.eom:%d %B %Y}")
            C.doc_table(d, ["Item", "Detail"], [["Project", p["name"]], ["Owner / contractor", self.c["name"]],
                                                ["Contract form", p["form"]], ["Completion date", m.eom.isoformat()],
                                                ["Retention released now", f"{p['retention'] * 50:.1f}% of contract sum"],
                                                ["Defects liability period", "12 months"],
                                                ["Outstanding punch items", r.randint(0, 40)]])
            d.add_paragraph("The works are certified complete except for the minor items listed in the attached punch "
                            "list, which the contractor will finish within 28 days.")
            C.save_doc(m.sink, f"{self.base}/05 Handover/Completion certificate.docx", d)
