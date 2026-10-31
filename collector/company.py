"""Fictional construction software company "Quarrystone Systems" - SYNTHETIC records for research.

Quarrystone sells a cloud platform for construction projects (Schedule, Estimate & Cost, Field, Closeout modules)
to contractors, developers, owners and public agencies in the Americas, Europe and Africa, with data hosted in the
customer's region. It also delivers implementation services (onboarding, P6 schedule migration, ERP integration,
field rollout). The world (customers, subscriptions, construction projects, staff) is simulated month by month from a
fixed seed, so reruns reproduce past months exactly and only add new ones.
"""
import datetime as dt
import io
import math
import random
import sys
import zipfile
from email.message import EmailMessage
from email.utils import format_datetime

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import site_data as SD
from . import staff_records as S
from .common import add_sheet, new_book, safe, save_book

CO = "Quarrystone Systems"
DOMAIN = "quarrystone.example"
ROOT = f"Fictional Company - {CO}"
F = {k: f"{ROOT}/{v}" for k, v in {
    "crm": "01 Customers & CRM", "legal": "02 Contracts & Legal", "impl": "03 Implementation Services",
    "eng": "04 Product & Engineering", "usage": "05 Platform Usage & Reliability",
    "cpd": "06 Customer Project Workspaces (sample data)", "support": "07 Customer Support",
    "fin": "08 Finance & Accounting", "hr": "09 HR & People", "mkt": "10 Sales & Marketing",
    "rep": "11 Management Reports", "pol": "12 Policies & SOPs", "sec": "13 Security & Compliance",
    "mail": "14 Emails & Meetings"}.items()}
BANNER = ("FICTIONAL - synthetic research data. Quarrystone Systems, its customers, their projects and all people "
          "are made up.")
START = (2017, 1)
SEED = 20170101
SOP_SCOPE = "Engineering, SRE, Security, Implementation, Customer Success, Support"
WORK_LABELS = ("Commits", "Issues resolved", "Support tickets")
PAY_COLS = ["Base", "Allowances", "Commission", "Overtime hours", "Bonus", "Gross", "Employer taxes & benefits",
            "Leave days"]
TRAINING_PROVIDER = "Keystone Learning Partners"

OFFICES = {  # office: (region, country, currency, pay multiplier, employer tax & benefits rate)
    "Denver": ("Americas", "United States", "USD", 1.0, 0.165),
    "Antwerp": ("Europe", "Belgium", "EUR", 0.84, 0.27),
    "Nairobi": ("Africa", "Kenya", "KES", 0.36, 0.06),
}
FX = {"USD": 1.0, "EUR": 1.09, "GBP": 1.27, "KES": 0.0077, "ZAR": 0.055, "AED": 0.272}
REGION_LAUNCH = {"Americas": (2017, 1), "Europe": (2018, 9), "Africa": (2021, 3)}  # data-residency regions
CITIES = {
    "Americas": [("Denver", "United States", "USD"), ("Chicago", "United States", "USD"),
                 ("Houston", "United States", "USD"), ("Atlanta", "United States", "USD"),
                 ("Phoenix", "United States", "USD"), ("Dallas", "United States", "USD"),
                 ("Seattle", "United States", "USD"), ("Boston", "United States", "USD"),
                 ("New York", "United States", "USD"), ("Los Angeles", "United States", "USD"),
                 ("Minneapolis", "United States", "USD"), ("Nashville", "United States", "USD"),
                 ("Salt Lake City", "United States", "USD"), ("Toronto", "Canada", "USD"),
                 ("Calgary", "Canada", "USD")],
    "Europe": [("Antwerp", "Belgium", "EUR"), ("Rotterdam", "Netherlands", "EUR"), ("Amsterdam", "Netherlands", "EUR"),
               ("Brussels", "Belgium", "EUR"), ("Hamburg", "Germany", "EUR"), ("Munich", "Germany", "EUR"),
               ("Lyon", "France", "EUR"), ("Madrid", "Spain", "EUR"), ("Milan", "Italy", "EUR"),
               ("Warsaw", "Poland", "EUR"), ("Copenhagen", "Denmark", "EUR"), ("London", "United Kingdom", "GBP"),
               ("Manchester", "United Kingdom", "GBP"), ("Dublin", "Ireland", "EUR"),
               ("Dubai", "United Arab Emirates", "AED")],
    "Africa": [("Nairobi", "Kenya", "KES"), ("Mombasa", "Kenya", "KES"), ("Kampala", "Uganda", "USD"),
               ("Kigali", "Rwanda", "USD"), ("Dar es Salaam", "Tanzania", "USD"), ("Addis Ababa", "Ethiopia", "USD"),
               ("Lagos", "Nigeria", "USD"), ("Accra", "Ghana", "USD"), ("Johannesburg", "South Africa", "ZAR"),
               ("Cape Town", "South Africa", "ZAR")],
}
VAT = {"Belgium": .21, "Netherlands": .21, "Germany": .19, "France": .20, "Spain": .21, "Italy": .22, "Poland": .23,
       "Denmark": .25, "United Kingdom": .20, "Ireland": .23, "United Arab Emirates": .05, "Kenya": .16,
       "Uganda": .18, "Rwanda": .18, "Tanzania": .18, "Ethiopia": .15, "Nigeria": .075, "Ghana": .15,
       "South Africa": .15}

NAMES = {
    "Americas": ("""James Mary Robert Patricia Michael Jennifer David Linda William Elizabeth Daniel Sarah Matthew
Jessica Anthony Karen Joshua Nancy Andrew Lisa Kevin Ashley Brian Emily Carlos Maria Luis Sofia Jose Ana Wei Mei
Priya Arjun Rahul Ananya Tyrone Keisha Marcus Aaliyah Ethan Olivia Noah Emma Liam Ava Mason Chloe Logan Grace""",
                 """Smith Johnson Williams Brown Jones Garcia Miller Davis Rodriguez Martinez Hernandez Lopez Wilson
Anderson Thomas Taylor Moore Jackson Martin Lee Thompson White Harris Clark Lewis Walker Hall Young Allen King
Patel Shah Chen Wang Nguyen Kim Singh Reddy Rivera Flores Washington Brooks Bennett Murphy Cooper Reed"""),
    "Europe": ("""Lucas Emma Noah Louise Liam Olivia Arthur Marie Jules Lotte Sem Anna Daan Julia Finn Sophie Lars
Eva Thomas Lena Pieter Femke Bram Sanne Jonas Mila Elias Clara Matteo Giulia Pablo Lucia Antoine Camille Jakub Zofia
Oliver Amelia Henrik Freja Sean Aoife Omar Yasmin Mehmet Elif Karim Leila""",
               """Peeters Janssens Maes Jacobs Mertens Willems De Vries Jansen Bakker Visser Smit Meijer De Jong
Mulder Bos Vos Muller Schmidt Schneider Fischer Weber Wagner Becker Hoffmann Dubois Martin Bernard Moreau Rossi
Bianchi Garcia Fernandez Nowak Kowalski Wisniewski Hansen Nielsen Murphy Kelly Walsh Yilmaz Kaya El Amrani Haddad"""),
    "Africa": ("""Wanjiru Kamau Achieng Otieno Njeri Mwangi Akinyi Odhiambo Wambui Kiprop Chebet Mutua Nyambura
Omondi Atieno Kariuki Muthoni Ochieng Jepkoech Kibet Amina Hassan Zawadi Baraka Neema Juma Grace Brian Faith Kevin
Mercy Dennis Esther Collins Joy Felix Aisha Abdi Halima Yusuf Chinedu Ngozi Kwame Akosua Thabo Lerato Sipho Naledi""",
               """Kamau Mwangi Otieno Odhiambo Njoroge Wanjiku Kiprotich Kipchumba Mutiso Ndungu Ochieng Onyango
Kimani Karanja Maina Gitau Wekesa Barasa Chege Muriuki Omondi Waweru Koech Rotich Langat Cheruiyot Okonkwo Adeyemi
Mensah Boateng Nkosi Dlamini Mokoena Mbeki Mugisha Uwimana Nyirenda Banda Tesfaye Bekele Abdullahi Mohamed"""),
}

ACCOUNTS = {
    "1000": ("Cash at bank", "Asset"), "1100": ("Accounts receivable", "Asset"), "1200": ("Prepaid expenses", "Asset"),
    "1500": ("Computer equipment", "Asset"), "1510": ("Accumulated depreciation", "Asset"),
    "1600": ("Capitalised software development", "Asset"), "1610": ("Accumulated amortisation", "Asset"),
    "2000": ("Accounts payable", "Liability"), "2100": ("VAT / sales tax payable", "Liability"),
    "2200": ("Accrued payroll taxes & benefits", "Liability"), "2400": ("Deferred subscription revenue", "Liability"),
    "3000": ("Share capital and premium", "Equity"), "3100": ("Retained earnings", "Equity"),
    "4000": ("Subscription revenue", "Revenue"), "4100": ("Implementation services revenue", "Revenue"),
    "4200": ("Training revenue", "Revenue"),
    "5000": ("Salaries & wages", "Expense"), "5050": ("Payroll taxes & benefits", "Expense"),
    "5100": ("Contractors", "Expense"), "5200": ("Cloud hosting", "Expense"),
    "5250": ("Third-party software in product (maps, OCR, e-signature)", "Expense"),
    "5300": ("Marketing & events", "Expense"), "5400": ("Rent & offices", "Expense"),
    "5500": ("Internal software & tools", "Expense"), "5600": ("Legal, audit & certification (SOC 2, ISO 27001)", "Expense"),
    "5700": ("Insurance", "Expense"), "5800": ("Depreciation & amortisation", "Expense"),
    "5900": ("Bad debt", "Expense"), "6000": ("Training & recruiting", "Expense"),
    "6100": ("Sales commissions", "Expense"), "6200": ("Staff travel & expense claims", "Expense"),
    "6300": ("Bank charges & FX differences", "Expense")}

# role: (department, office preference, monthly base USD at Denver pay, headcount rule from (customers, seats/100, impl))
ROLES = {
    "Chief Executive Officer": ("Executive", "Denver", 22000, lambda c, s, i: 1),
    "Chief Technology Officer": ("Engineering", "Denver", 20000, lambda c, s, i: 1),
    "Chief Financial Officer": ("Finance", "Denver", 18500, lambda c, s, i: 1 if c > 20 else 0),
    "Chief Revenue Officer": ("Sales", "Denver", 18500, lambda c, s, i: 1 if c > 30 else 0),
    "VP Customer Success": ("Customer Success", "Nairobi", 15000, lambda c, s, i: 1 if c > 25 else 0),
    "Head of People": ("People", "Antwerp", 13000, lambda c, s, i: 1 if c > 15 else 0),
    "Regional General Manager Americas": ("Sales", "Denver", 16500, lambda c, s, i: 1 if c > 60 else 0),
    "Regional General Manager Europe": ("Sales", "Antwerp", 16500, lambda c, s, i: 1 if c > 40 else 0),
    "Regional General Manager Africa": ("Sales", "Nairobi", 16500, lambda c, s, i: 1 if c > 40 else 0),
    "Engineering Manager": ("Engineering", "Denver", 15000, lambda c, s, i: 1 + int(s) // 25),
    "Backend Engineer": ("Engineering", "Denver", 12000, lambda c, s, i: 3 + int(s) // 8),
    "Frontend Engineer": ("Engineering", "Denver", 11000, lambda c, s, i: 2 + int(s) // 12),
    "Mobile & Offline Engineer": ("Engineering", "Nairobi", 11500, lambda c, s, i: 2 + int(s) // 12),
    "Data Engineer": ("Engineering", "Antwerp", 12000, lambda c, s, i: 1 + int(s) // 25),
    "Site Reliability Engineer": ("Engineering", "Denver", 12500, lambda c, s, i: 1 + int(s) // 20),
    "Security Engineer": ("Security & Compliance", "Antwerp", 13000, lambda c, s, i: 1 + int(s) // 40),
    "QA Engineer": ("Engineering", "Nairobi", 8500, lambda c, s, i: 1 + int(s) // 15),
    "Product Manager": ("Product", "Denver", 12500, lambda c, s, i: 1 + int(s) // 20),
    "Product Designer": ("Product", "Antwerp", 10500, lambda c, s, i: 1 + int(s) // 30),
    "Technical Writer": ("Product", "Nairobi", 7500, lambda c, s, i: 1 if s > 10 else 0),
    "Solutions Engineer": ("Sales", "Denver", 12000, lambda c, s, i: 1 + c // 60),
    "Implementation Consultant": ("Implementation", "Denver", 10000, lambda c, s, i: 1 + i // 2),
    "Scheduling Specialist (P6)": ("Implementation", "Antwerp", 10500, lambda c, s, i: 1 + i // 5),
    "Data Migration & BIM Specialist": ("Implementation", "Antwerp", 10500, lambda c, s, i: (1 + i // 6) if i else 0),
    "Customer Trainer": ("Implementation", "Nairobi", 7000, lambda c, s, i: 1 + i // 6),
    "Customer Success Manager": ("Customer Success", "Nairobi", 9000, lambda c, s, i: 1 + c // 25),
    "Support Specialist": ("Customer Success", "Nairobi", 5600, lambda c, s, i: 2 + int(s) // 10),
    "Account Executive": ("Sales", "Denver", 10500, lambda c, s, i: 1 + c // 30),
    "Sales Development Representative": ("Sales", "Antwerp", 6500, lambda c, s, i: 1 + c // 50),
    "Marketing Manager": ("Marketing", "Antwerp", 10000, lambda c, s, i: 1),
    "Content & Community Manager": ("Marketing", "Nairobi", 7000, lambda c, s, i: 1 if c > 20 else 0),
    "Finance Manager": ("Finance", "Denver", 10500, lambda c, s, i: 1),
    "Accountant": ("Finance", "Nairobi", 6500, lambda c, s, i: 1 + c // 120),
    "People Partner": ("People", "Antwerp", 8000, lambda c, s, i: 1 + c // 150),
    "Recruiter": ("People", "Nairobi", 6500, lambda c, s, i: 1 if c > 30 else 0),
    "Legal Counsel": ("Legal", "Antwerp", 14000, lambda c, s, i: 1 if c > 40 else 0),
    "Compliance & Privacy Officer": ("Security & Compliance", "Antwerp", 11500, lambda c, s, i: 1 if c > 25 else 0),
}
HEADS = {"Executive": "Chief Executive Officer", "Engineering": "Chief Technology Officer",
         "Product": "Chief Technology Officer", "Finance": "Chief Financial Officer", "Sales": "Chief Revenue Officer",
         "Marketing": "Chief Revenue Officer", "Customer Success": "VP Customer Success",
         "Implementation": "VP Customer Success", "People": "Head of People", "Legal": "Chief Executive Officer",
         "Security & Compliance": "Chief Technology Officer"}
EXPENSES = {
    "Account Executive": [("Client entertainment", "Lunch with prospect", 60, 450, .5),
                          ("Travel", "Customer visit / site walk", 300, 2600, .35)],
    "Implementation Consultant": [("Travel", "On-site go-live support", 300, 2400, .4), ("Mileage", "Site visits", 30, 240, .4)],
    "Customer Trainer": [("Travel", "On-site field training", 200, 1600, .35)],
    "Customer Success Manager": [("Travel", "Quarterly business review on site", 200, 1800, .2)],
    "Solutions Engineer": [("Travel", "Product demo at customer office", 250, 2000, .3)],
    "Mobile & Offline Engineer": [("Hardware", "Rugged test tablet", 200, 900, .06), ("Travel", "Field testing on a live site", 60, 400, .1)],
    "Marketing Manager": [("Events", "Construction trade show booth", 400, 6000, .2), ("Travel", "Industry conference", 300, 2400, .2)],
    "Scheduling Specialist (P6)": [("Certification", "Planning & scheduling certification", 300, 900, .05)],
    "Security Engineer": [("Certification", "Security certification exam", 300, 900, .07)],
    "Recruiter": [("Events", "University career fair", 100, 700, .2)],
}
TRAINING = {
    "Backend Engineer": ["Secure coding (OWASP Top 10)", "Multi-tenant SaaS architecture", "PostgreSQL performance"],
    "Frontend Engineer": ["Accessibility (WCAG 2.2)", "Web performance"],
    "Mobile & Offline Engineer": ["Offline-first sync and CRDTs", "Mobile app security (MASVS)"],
    "Data Engineer": ["Data residency engineering", "IFC and openBIM data"],
    "Site Reliability Engineer": ["Incident command", "Infrastructure as code"],
    "Security Engineer": ["ISO 27001 lead implementer", "Threat modelling"],
    "Compliance & Privacy Officer": ["GDPR practitioner", "Kenya Data Protection Act", "SOC 2 audit readiness"],
    "Implementation Consultant": ["Construction project controls", "ISO 19650 information management"],
    "Scheduling Specialist (P6)": ["Primavera P6 advanced scheduling", "Delay analysis methods"],
    "Data Migration & BIM Specialist": ["IFC 4.3 and IDS", "BCF issue workflows", "Revit to IFC export"],
    "Customer Success Manager": ["Customer success fundamentals", "Construction technology adoption"],
    "Support Specialist": ["De-escalation", "Construction workflows for support"],
    "Product Manager": ["Product discovery", "Construction site safety awareness"],
    "Account Executive": ["Value selling to contractors", "Public procurement basics"],
}
COMMON_TRAINING = ["Security awareness", "Privacy & data protection", "Anti-bribery and corruption",
                   "Site safety induction (for site visits)"]

CUSTOMER_KINDS = [("General contractor", ["Construction", "Builders", "Contracting", "Construction Group"]),
                  ("Specialty contractor (MEP)", ["Mechanical", "Electrical Contractors", "Building Services"]),
                  ("Civil & infrastructure contractor", ["Civil Works", "Infrastructure", "Earthmoving"]),
                  ("Developer", ["Developments", "Properties", "Real Estate"]),
                  ("Owner / operator", ["Healthcare Estates", "Logistics Properties", "Data Centers", "Campus Estates"]),
                  ("Engineering & design firm", ["Engineering", "Consulting Engineers", "Design Partners"]),
                  ("Public agency", ["Regional Infrastructure Authority", "Housing Agency", "Transit Authority"]),
                  ("Homebuilder", ["Homes", "Residential"])]
CUST_A = """Atlas Brightline Copperleaf Northgate Silverpine Bluewater Redstone Ironbridge Clearwater Summit Pinecrest
Harborview Lakeshore Stonefield Oakridge Westbrook Eastwind Riverbend Highland Granite Meridian Keystone Sterling
Evergreen Cobalt Falcon Orion Pioneer Vantage Beacon Crescent Horizon Liberty Monarch Sapphire Willow Basalt Ashlar
Cornerstone Trowel Rebar Plumbline Bedrock Archway Gable Corbel Buttress Mortarline Kilnworth""".split()
MODULES = {"Schedule": 240, "Estimate & Cost": 300, "Field": 280, "Closeout": 180}  # USD per seat per year
TIERS = {"Team": (1.0, 0), "Business": (1.12, 0), "Enterprise": (1.0, 40000)}  # price multiplier, platform fee
IMPL_TYPES = ["Onboarding & configuration", "Primavera P6 schedule migration", "ERP cost integration",
              "Document migration & closeout set-up", "SSO & data residency set-up", "Field rollout & training",
              "BIM / IFC model coordination set-up"]


def ym_add(ym, n):
    t = ym[0] * 12 + ym[1] - 1 + n
    return (t // 12, t % 12 + 1)


def ym_s(ym):
    return f"{ym[0]}-{ym[1]:02d}"


def mdays(ym):
    nxt = ym_add(ym, 1)
    return (dt.date(nxt[0], nxt[1], 1) - dt.date(ym[0], ym[1], 1)).days


def months_between(a, b):
    return (b[0] - a[0]) * 12 + b[1] - a[1]


def pois(rng, mu):
    if mu <= 0:
        return 0
    if mu > 30:
        return max(0, int(round(rng.gauss(mu, math.sqrt(mu)))))
    L, k, p = math.exp(-mu), 0, 1.0
    while True:
        p *= rng.random()
        if p < L:
            return k
        k += 1


def r2(x):
    return round(x + 1e-9, 2)


def unique(rng, used, make, city):
    for _ in range(12):
        name = make()
        if name not in used:
            break
    else:
        name, k = f"{make()} {city}", 2
        while name in used:
            name, k = f"{make()} {city} {k}", k + 1
    used.add(name)
    return name


# ---------------------------------------------------------------- documents

def new_doc(title, subtitle=None):
    d = Document()
    d.styles["Normal"].font.name = "Calibri"
    d.styles["Normal"].font.size = Pt(10.5)
    d.core_properties.author = CO
    d.core_properties.comments = BANNER
    sec = d.sections[0]
    p = sec.header.paragraphs[0]
    p.text = f"{CO} | Confidential (fictional)"
    p.runs[0].font.size, p.runs[0].font.color.rgb = Pt(8), RGBColor(0x55, 0x55, 0x55)
    f = sec.footer.paragraphs[0]
    f.text = BANNER
    f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    f.runs[0].font.size = Pt(7)
    d.add_heading(title, 0)
    if subtitle:
        d.add_paragraph(subtitle).runs[0].italic = True
    return d


def doc_table(d, header, rows):
    t = d.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(header):
        t.rows[0].cells[i].text = str(h)
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = "" if v is None else (f"{v:,.2f}" if isinstance(v, float) else str(v))
    return t


def save_doc(sink, rel, d):
    p = sink.path(rel)
    d.save(p)
    sink.wrote(p)


def bullet(d, text):
    d.add_paragraph(text, style="List Bullet")


def gz_csv(sink, rel, header, rows_iter):
    import csv
    import gzip
    p = sink.path(rel)
    with gzip.open(p, "wt", encoding="utf-8", compresslevel=6, newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in rows_iter:
            w.writerow(row)
    sink.wrote(p)


# ---------------------------------------------------------------- world

class World:
    def __init__(self, end, scale=1.0, seed=SEED):
        rng = random.Random(seed)
        self.scale, self.end = scale, end
        self.customers, self.impl, self.staff, self.projects = [], [], [], []
        used, people = set(), set()
        self.people_used = people
        ym, i = START, 0
        while ym <= end:
            for _ in range(pois(rng, (2 if i == 0 else 0.7 + 0.028 * i) * scale)):
                self._customer(rng, ym, used)
            for c in self.customers:
                if c["end"] is not None or c["since"] >= ym:
                    continue
                if (months_between(c["since"], ym)) % 12 == 0:  # renewal month
                    p_churn = {"Team": .16, "Business": .08, "Enterprise": .04}[c["tier"]]
                    if rng.random() < p_churn:
                        c["end"] = ym
                        c["churn_reason"] = rng.choice(["Budget cut", "Moved to competitor", "Project pipeline ended",
                                                        "Acquired by another firm", "Low adoption on site",
                                                        "Consolidated onto ERP vendor suite"])
                        continue
                    c["seats"] = int(c["seats"] * rng.uniform(1.0, 1.4)) + rng.randint(0, 5)
                    if rng.random() < .35 and len(c["modules"]) < 4:
                        c["modules"].append(next(m for m in MODULES if m not in c["modules"]))
                    if c["tier"] == "Team" and c["seats"] > 40:
                        c["tier"] = "Business"
                    elif c["tier"] == "Business" and c["seats"] > 180 and rng.random() < .5:
                        c["tier"] = "Enterprise"
                    c["terms"].append([ym, c["seats"], list(c["modules"]), c["tier"]])
                if rng.random() < 0.012 * max(1, c["seats"] // 40):
                    self._cproject(rng, c, ym)
                if c["tier"] != "Team" and rng.random() < .01:
                    self._impl(rng, c, ym)
            c_n, s_n, i_n = self.load(ym)
            for e in self.staff:
                if e["left"] is None and e["role"] not in HEADS.values() and rng.random() < 0.011:
                    e["left"] = ym
                    e["leave_reason"] = rng.choice(["Resigned", "Resigned", "Resigned", "Relocated", "Laid off",
                                                    "Dismissed", "Contract ended"])
            for role, (dept, office, base, rule) in ROLES.items():
                need = rule(c_n, s_n, i_n)
                have = sum(1 for e in self.staff if e["role"] == role and e["left"] is None)
                for _ in range(max(0, need - have)):
                    self._hire(rng, role, dept, office, base, ym)
            ym, i = ym_add(ym, 1), i + 1
        for e in self.staff:
            e["manager"] = self._manager(e)

    def person(self, rng, region):
        first, last = NAMES[region]
        first, last = first.split(), last.split()
        while True:
            n = f"{rng.choice(first)} {rng.choice(last)}"
            if n not in self.people_used:
                self.people_used.add(n)
                return n

    def _customer(self, rng, ym, used):
        regions = [r for r, start in REGION_LAUNCH.items() if start <= ym] or ["Americas"]
        region = rng.choices(regions, [55, 30, 15][:len(regions)])[0]
        city, country, cur = rng.choice(CITIES[region])
        kind, suffixes = rng.choice(CUSTOMER_KINDS)
        name = unique(rng, used, lambda: f"{rng.choice(CUST_A)} {rng.choice(suffixes)}", city)
        tier = rng.choices(["Team", "Business", "Enterprise"], [55, 33, 12])[0]
        seats = {"Team": rng.randint(5, 25), "Business": rng.randint(20, 120), "Enterprise": rng.randint(100, 700)}[tier]
        mods = sorted(rng.sample(list(MODULES), rng.randint(1, 4) if tier != "Enterprise" else rng.randint(3, 4)),
                      key=list(MODULES).index)
        residency = region if REGION_LAUNCH[region] <= ym else "Europe"
        c = {"id": len(self.customers), "code": f"CU{len(self.customers) + 1:04d}", "name": name, "kind": kind,
             "region": region, "city": city, "country": country, "currency": cur, "tier": tier, "seats": seats,
             "modules": mods, "since": ym, "end": None, "churn_reason": "", "contact": self.person(rng, region),
             "domain": safe(name.split()[0].lower(), 20) + "-" + safe(name.split()[-1].lower(), 12) + ".example",
             "residency": residency, "terms": [[ym, seats, list(mods), tier]], "net": rng.choice([30, 30, 45, 60]),
             "sample": rng.random() < .3, "sso": tier == "Enterprise" or rng.random() < .2}
        self.customers.append(c)
        for _ in range(max(1, seats // 30)):
            self._cproject(rng, c, ym)
        if tier != "Team":
            self._impl(rng, c, ym, first=True)

    def _cproject(self, rng, c, ym):
        city = rng.choice(CITIES[c["region"]])[0]
        self.projects.append(SD.new_project(rng, c, ym, len(self.projects), c["region"], city))

    def _impl(self, rng, c, ym, first=False):
        typ = "Onboarding & configuration" if first else rng.choice(IMPL_TYPES[1:])
        months = rng.randint(2, 6)
        team = rng.randint(1, 4)
        model = rng.choice(["Fixed fee", "Time & materials"])
        rate = r2(rng.uniform(150, 210) * (1 if c["region"] == "Americas" else .9 if c["region"] == "Europe" else .7))
        self.impl.append({"id": len(self.impl), "code": f"IMP-{ym[0]}-{len(self.impl) + 1:04d}", "cust": c["id"],
                          "name": f"{c['name']} - {typ}", "type": typ, "start": ym_add(ym, 0 if first else 1),
                          "end": ym_add(ym, months), "team": team, "model": model, "rate": rate,
                          "budget": r2(team * 120 * months * rate * rng.uniform(.85, 1.1)),
                          "risk": rng.choice(["Low", "Low", "Medium", "High"])})

    def _hire(self, rng, role, dept, office, base, ym):
        if office == "Denver" and role not in ("Chief Executive Officer", "Chief Technology Officer",
                                               "Chief Financial Officer", "Chief Revenue Officer") and rng.random() < .2:
            office = rng.choice(["Antwerp", "Nairobi"])
        region = OFFICES[office][0]
        n = self.person(rng, region)
        first, last = n.split(" ", 1)
        self.staff.append({"id": f"E{len(self.staff) + 1:05d}", "name": n,
                           "email": f"{first.lower()}.{last.lower().replace(' ', '').replace('-', '')}@{DOMAIN}",
                           "role": role, "dept": dept, "office": office, "hired": ym, "left": None,
                           "leave_reason": "", "nationality": OFFICES[office][1], "crew": len(self.staff) % 4,
                           "base": r2(base * OFFICES[office][3] * rng.uniform(.9, 1.12) * 1.035 ** (ym[0] - 2017)),
                           "level": rng.choice(["I", "II", "II", "III", "Senior", "Staff"])})

    def _manager(self, e):
        head = HEADS.get(e["dept"])
        if e["role"] == "Chief Executive Officer":
            return ""
        if e["role"] in HEADS.values():
            return self.staff[0]["id"]
        return next((x["id"] for x in self.staff if x["role"] == head), self.staff[0]["id"])

    # queries
    def active_customers(self, ym):
        return [c for c in self.customers if c["since"] <= ym and (c["end"] is None or c["end"] > ym)]

    def term(self, c, ym):
        """The subscription term in force: [start, seats, modules, tier]."""
        return [t for t in c["terms"] if t[0] <= ym][-1]

    def annual_price(self, c, ym):
        start, seats, mods, tier = self.term(c, ym)
        mult, fee = TIERS[tier]
        per_seat = sum(MODULES[m] for m in mods) * mult * 1.04 ** (start[0] - 2017)
        disc = .85 if seats > 300 else .92 if seats > 100 else 1.0
        return r2((seats * per_seat * disc + fee * 1.04 ** (start[0] - 2017)))

    def active_impl(self, ym):
        live = {c["id"] for c in self.active_customers(ym)}
        return [p for p in self.impl if p["start"] <= ym <= p["end"] and p["cust"] in live]

    def active_projects(self, ym):
        live = {c["id"] for c in self.active_customers(ym)}
        return [p for p in self.projects if p["cust"] in live and p["start"] <= ym < ym_add(p["start"], p["months"])]

    def load(self, ym):
        cs = self.active_customers(ym)
        return len(cs), sum(self.term(c, ym)[1] for c in cs) / 100, len(self.active_impl(ym))

    def staff_at(self, ym, role=None):
        return [e for e in self.staff if e["hired"] <= ym and (e["left"] is None or e["left"] > ym)
                and (role is None or e["role"] == role)]

    def pay(self, e, ym):
        return r2(e["base"] * 1.035 ** (ym[0] - e["hired"][0]))


# ---------------------------------------------------------------- month

class Month:
    def __init__(self, w, ym, ledger, sink, detail=1.0):
        self.w, self.ym, self.L, self.sink, self.detail = w, ym, ledger, sink, detail
        self.rng = random.Random(f"{SEED}-{ym_s(ym)}")
        self.tag, self.y = ym_s(ym), str(ym[0])
        self.days = mdays(ym)
        self.d0 = dt.date(ym[0], ym[1], 1)
        self.eom = self.d0 + dt.timedelta(days=self.days - 1)
        self.staff = w.staff_at(ym)
        self.customers = w.active_customers(ym)
        self.cu_by = {c["id"]: c for c in w.customers}
        self.impls = w.active_impl(ym)
        self.C, self.F, self.BANNER = sys.modules[__name__], F, BANNER
        self.gl, self.emails, self.work_counts = [], [], {}
        self.live_projects = w.active_projects(ym)
        self.proj_count = {}
        for p in self.live_projects:
            self.proj_count[p["cust"]] = self.proj_count.get(p["cust"], 0) + 1

    def people(self, *roles):
        return [e for e in self.staff if e["role"] in roles] or self.staff[:1]

    def ts(self, day=None, hour=None):
        r = self.rng
        d = self.d0 + dt.timedelta(days=r.randrange(self.days) if day is None else day)
        return dt.datetime.combine(d, dt.time(r.randint(8, 19) if hour is None else hour, r.randrange(60), r.randrange(60)))

    def count(self, eid, k, n=1):
        self.work_counts.setdefault(eid, [0, 0, 0])[k] += n

    def post(self, date, ref, desc, lines):
        assert abs(sum(d - c for _, d, c in lines)) < 0.01, (ref, lines)
        for acct, dr, cr in lines:
            if dr or cr:
                self.gl.append([date, ref, acct, ACCOUNTS[acct][0], desc, r2(dr), r2(cr)])

    def mail(self, t, frm, to, subject, body):
        m = EmailMessage()
        m["From"], m["To"], m["Subject"] = frm, to, subject
        m["Date"] = format_datetime(t.replace(tzinfo=dt.timezone.utc))
        m["Message-ID"] = f"<{self.tag}.{len(self.emails) + 1}@{DOMAIN}>"
        m["X-Dataset-Notice"] = BANNER
        m.set_content(body)
        self.emails.append((t, subject, m.as_bytes()))

    def run(self):
        self.sales()
        self.contracts()
        self.implementation()
        self.engineering()
        self.usage()
        self.workspaces()
        self.support()
        self.security()
        self.marketing()
        self.hr()
        self.finance()
        S.collect(self)
        if self.ym[1] == 12:
            S.person_year(self.w, self.L, self.ym[0], self.sink, self.C, final=True)
        self.reports()
        self.meetings()
        self.write_mail()

    # ---------------- sales: new logos, renewals, churn, pipeline
    def sales(self):
        r, w = self.rng, self.w
        self.new = [c for c in w.customers if c["since"] == self.ym]
        self.renewals = [c for c in w.customers if c["since"] < self.ym and months_between(c["since"], self.ym) % 12 == 0
                         and (c["end"] is None or c["end"] > self.ym)]
        self.churned = [c for c in w.customers if c["end"] == self.ym]
        aes = self.people("Account Executive", "Chief Revenue Officer", "Chief Executive Officer")
        opp = []
        for c in w.customers:
            lead = months_between(self.ym, c["since"])
            if 0 <= lead <= 4:
                stage = "Closed won" if lead == 0 else ["Proposal", "Pilot on live project", "Discovery", "Qualified"][min(lead - 1, 3)]
                opp.append([c["name"], c["kind"], c["region"], c["city"], stage, c["tier"], ", ".join(c["modules"]),
                            c["seats"], w.annual_price(c, c["since"]),
                            {"Qualified": 15, "Discovery": 30, "Pilot on live project": 55, "Proposal": 70,
                             "Closed won": 100}[stage], aes[c["id"] % len(aes)]["name"]])
        for _ in range(pois(r, 8 + len(self.customers) / 25)):
            kind, suffixes = r.choice(CUSTOMER_KINDS)
            region = r.choice(list(CITIES))
            st = r.choice(["Qualified", "Discovery", "Pilot on live project", "Closed lost", "Closed lost"])
            seats = r.randint(10, 300)
            opp.append([f"{r.choice(CUST_A)} {r.choice(suffixes)} (prospect)", kind, region,
                        r.choice(CITIES[region])[0], st, r.choice(list(TIERS)),
                        ", ".join(r.sample(list(MODULES), r.randint(1, 4))), seats, r2(seats * r.uniform(500, 1100)),
                        0 if st == "Closed lost" else {"Qualified": 15, "Discovery": 30, "Pilot on live project": 55}[st],
                        r.choice(aes)["name"]])
        wb = new_book()
        add_sheet(wb, "Pipeline", ["Account", "Segment", "Region", "City", "Stage", "Tier", "Modules", "Seats",
                                   "ARR USD", "Probability %", "Owner"], opp, {"Account": 36, "Modules": 36})
        ws = wb["Pipeline"]
        n = ws.max_row
        ws.cell(n + 2, 8, "Weighted ARR")
        ws.cell(n + 2, 9, f"=SUMPRODUCT(I2:I{n},J2:J{n})/100")
        lost = [[c["code"], c["name"], c["tier"], ym_s(c["since"]), w.annual_price(c, ym_add(self.ym, -1)),
                 c["churn_reason"]] for c in self.churned]
        add_sheet(wb, "Churned", ["Customer", "Name", "Tier", "Since", "Lost ARR USD", "Reason"], lost, {"Name": 34})
        save_book(self.sink, f"{F['crm']}/Pipeline & renewals/{self.y}/Pipeline {self.tag}.xlsx", wb, "Pipeline", BANNER)

    # ---------------- contracts: subscription agreements, order forms, DPAs, renewals
    def contracts(self):
        w = self.w
        for c in self.new:
            base = f"{F['legal']}/Customer contracts/{safe(c['name'], 60)}"
            d = new_doc(f"Subscription Services Agreement - {c['name']}",
                        f"{CO} and {c['name']} | effective {self.d0:%d %B %Y}")
            for h, t in [("1. Services", "Access to the Quarrystone platform modules listed in each Order Form, "
                                         "including web and mobile (offline-capable) apps and the public API."),
                         ("2. Fees and invoicing", f"Subscriptions are invoiced annually in advance in {c['currency']}; "
                                                   f"payment within {c['net']} days."),
                         ("3. Customer data", "The Customer owns all project data. Data is stored in the "
                                              f"{c['residency']} hosting region and not moved without consent."),
                         ("4. Service levels", "99.9% monthly availability (Enterprise 99.95%); service credits as in "
                                               "the SLA schedule."),
                         ("5. Security", "Provider maintains ISO/IEC 27001 certification and a SOC 2 Type II report, "
                                         "available under NDA."),
                         ("6. Data protection", "The Data Processing Agreement applies (GDPR, UK GDPR, Kenya Data "
                                                "Protection Act 2019, and US state privacy laws as relevant)."),
                         ("7. Liability", "Each party's liability is capped at the fees paid in the 12 months before "
                                          "the claim, except for data protection breaches (3x)."),
                         ("8. Term", "Initial term of 12 months, renewing for 12 months unless either party gives "
                                     "60 days' notice."),
                         ("9. Exit", "On termination the Customer can export all data (CSV, XER, IFC, PDF) for 60 "
                                     "days; Provider then deletes it within 30 days and certifies deletion.")]:
                d.add_heading(h, 1)
                d.add_paragraph(t)
            doc_table(d, ["For", "Name", "Title"], [[CO, w.staff[0]["name"], "Chief Executive Officer"],
                                                   [c["name"], c["contact"], "Authorised signatory"]])
            save_doc(self.sink, f"{base}/Subscription Services Agreement.docx", d)
            d = new_doc(f"Data Processing Agreement - {c['name']}", f"Hosting region: {c['residency']}")
            doc_table(d, ["Item", "Detail"], [
                ["Controller", c["name"]], ["Processor", CO], ["Data subjects", "Customer staff, subcontractor staff, "
                                                                                "site visitors in photos and logs"],
                ["Personal data", "Names, emails, phone numbers, site sign-in records, photos, safety incident details"],
                ["Hosting region", c["residency"]], ["Sub-processors", "Cloud hosting provider, email delivery, "
                                                                       "maps, OCR, e-signature"],
                ["Transfers", "None outside the region except support access under SCCs"],
                ["Breach notice", "Within 48 hours of becoming aware"]])
            save_doc(self.sink, f"{base}/Data Processing Agreement.docx", d)
        for c in self.new + self.renewals:
            start, seats, mods, tier = w.term(c, self.ym)
            price = w.annual_price(c, self.ym)
            fx = FX[c["currency"]]
            d = new_doc(f"Order Form {c['code']}-{self.tag.replace('-', '')}",
                        f"{c['name']} | {'New subscription' if c in self.new else 'Renewal'}")
            doc_table(d, ["Item", "Detail"], [["Tier", tier], ["Modules", ", ".join(mods)], ["Named users", seats],
                                              ["Term", f"12 months from {self.d0:%d %b %Y}"],
                                              ["Annual fee", f"{c['currency']} {price / fx:,.2f}"],
                                              ["SSO (SAML / OIDC)", "Included" if c["sso"] else "Not included"],
                                              ["Hosting region", c["residency"]], ["Payment terms", f"Net {c['net']}"]])
            save_doc(self.sink, f"{F['legal']}/Customer contracts/{safe(c['name'], 60)}/Order form {self.tag}.docx", d)

    # ---------------- implementation services
    def implementation(self):
        r = self.rng
        cons = self.people("Implementation Consultant", "Scheduling Specialist (P6)", "Data Migration & BIM Specialist",
                           "Customer Trainer")
        self.billable, ts_rows, self.team = {}, [], {}
        for p in self.impls:
            team = random.Random(f"{SEED}-team-{p['id']}").sample(cons, min(len(cons), p["team"]))
            self.team[p["id"]] = team
            hours = 0.0
            for e in team:
                h = r2(max(0, r.gauss(96, 24)))
                hours += h
                ts_rows.append([self.tag, p["code"], p["name"], e["id"], e["name"], e["role"], h, "Yes"])
            months = months_between(p["start"], p["end"]) + 1
            amount = r2(hours * p["rate"]) if p["model"] == "Time & materials" else r2(p["budget"] / months)
            self.billable[p["id"]] = (amount, r2(hours))
            c = self.cu_by[p["cust"]]
            if p["start"] == self.ym:
                self.sow(p, c, team[0] if team else self.staff[0])
            self.status(p, c, hours)
        wb = new_book()
        add_sheet(wb, "Timesheets", ["Month", "Engagement", "Name", "Employee", "Consultant", "Role", "Hours",
                                     "Billable"], ts_rows, {"Name": 44, "Consultant": 22, "Role": 26})
        save_book(self.sink, f"{F['impl']}/{self.y}/Timesheets/Services timesheets {self.tag}.xlsx", wb, "Timesheets",
                  BANNER)

    def sow(self, p, c, lead):
        months = months_between(p["start"], p["end"]) + 1
        d = new_doc(f"Statement of Work {p['code']}", p["name"])
        doc_table(d, ["Item", "Detail"], [["Engagement", p["type"]], ["Pricing", p["model"]],
                                         ["Start", ym_s(p["start"])], ["End", ym_s(p["end"])],
                                         ["Consultants", p["team"]], ["Rate (USD/h)", p["rate"]],
                                         ["Budget (USD)", p["budget"]], ["Lead consultant", lead["name"]]])
        d.add_heading("Scope", 1)
        scope = {
            "Onboarding & configuration": ["Workspace and project templates", "Cost code structure (CSI / NRM / custom)",
                                           "Roles, permissions and approval workflows", "Admin training"],
            "Primavera P6 schedule migration": ["Export XER from P6 for live projects", "Map WBS, calendars and codes",
                                                "Validate logic and critical path after import", "Look-ahead set-up"],
            "ERP cost integration": ["Map cost codes and commitments to ERP", "Nightly actuals sync via API",
                                     "Change order and pay application export", "Reconciliation report"],
            "Document migration & closeout set-up": ["Migrate drawing and document registers", "ISO 19650 naming",
                                                     "Closeout checklist and O&M templates", "Owner handover portal"],
            "SSO & data residency set-up": ["SAML / OIDC SSO with customer IdP", "SCIM provisioning",
                                            "Data residency confirmation", "Security questionnaire support"],
            "Field rollout & training": ["Mobile app rollout to site teams", "Offline mode training",
                                         "Inspection and punch list templates", "Superintendent coaching on site"],
            "BIM / IFC model coordination set-up": ["IFC model upload and federation", "BCF issue workflow",
                                                    "Clash review cadence", "Linking photos and issues to models"],
        }[p["type"]]
        for x in scope:
            bullet(d, x)
        d.add_heading("Milestones", 1)
        doc_table(d, ["Milestone", "Month", "Payment %"],
                  [[m, ym_s(ym_add(p["start"], int((months - 1) * f))), pc] for m, f, pc in
                   [("Kick-off and plan", 0, 20), ("Configuration complete", .5, 40), ("Go-live", 1.0, 40)]])
        save_doc(self.sink, f"{F['impl']}/Statements of work/{p['code']} {safe(c['name'], 50)}.docx", d)

    def status(self, p, c, hours):
        r = self.rng
        done, total = months_between(p["start"], self.ym) + 1, months_between(p["start"], p["end"]) + 1
        rag = r.choices(["Green", "Amber", "Red"], [70, 22, 8] if p["risk"] != "High" else [45, 38, 17])[0]
        d = new_doc(f"Implementation status - {p['name']}", f"{self.d0:%B %Y} | {p['code']}")
        doc_table(d, ["Measure", "Value"], [["Overall status", rag], ["Month", f"{done} of {total}"],
                                            ["Hours this month", hours], ["Users activated", r.randint(5, 200)],
                                            ["Projects migrated", r.randint(0, 25)], ["Open issues", r.randint(0, 9)]])
        d.add_heading("Done this month", 1)
        for x in r.sample(["Imported 14 P6 schedules with logic intact", "Configured cost codes and approval chain",
                           "Trained superintendents on offline daily logs", "Connected SSO with customer IdP",
                           "Migrated 3,200 drawings with ISO 19650 names", "Set up inspection templates",
                           "Mapped ERP commitments", "Federated IFC models for the hospital project"], 3):
            bullet(d, x)
        d.add_heading("Risks", 1)
        for x in r.sample(["Customer IT approval for SSO pending", "Legacy cost codes inconsistent between projects",
                           "Site connectivity worse than expected", "Key customer sponsor on leave",
                           "Schedule calendars differ by region"], 2):
            bullet(d, x)
        save_doc(self.sink, f"{F['impl']}/{self.y}/Status reports/{self.tag}/{safe(p['code'] + ' ' + c['name'], 70)}.docx", d)

    # ---------------- engineering
    def engineering(self):
        r, k = self.rng, self.detail
        eng = self.people("Backend Engineer", "Frontend Engineer", "Mobile & Offline Engineer", "Data Engineer",
                          "Site Reliability Engineer", "Security Engineer", "QA Engineer")
        repos = ["platform-api", "web-app", "mobile-field-app", "offline-sync-engine", "schedule-service",
                 "cost-service", "closeout-service", "document-service", "ifc-viewer", "integrations-hub",
                 "auth-sso", "infrastructure", "data-residency-router", "reporting-warehouse"]
        types = ["Story", "Story", "Task", "Bug", "Bug", "Spike", "Epic"]
        msgs = ["Fix {x} in {y}", "Add {x} to {y}", "Refactor {x}", "Improve {x} performance", "Handle edge case in {x}",
                "Add tests for {x}", "Bump dependencies in {y}", "Migrate {x} to new schema"]
        things = ["XER import", "critical path calc", "retention calc", "change order approval", "pay application export",
                  "offline conflict merge", "photo upload queue", "drawing pin coordinates", "IFC parsing",
                  "BCF export", "multi-currency rounding", "VAT on invoices", "SAML assertion parsing", "SCIM sync",
                  "regional storage routing", "punch list filters", "inspection templates", "O&M manual compile",
                  "audit trail", "API rate limiter", "unit conversion (metric/imperial)", "calendar exceptions"]
        issues, commits, prs, builds = [], [], [], []
        for repo in repos:
            for _ in range(pois(r, 45 * k)):
                e = r.choice(eng)
                t = self.ts()
                status = r.choices(["Done", "In Progress", "In Review", "To Do", "Won't Do"], [58, 15, 10, 14, 3])[0]
                res = (t + dt.timedelta(hours=r.lognormvariate(3.5, 1))) if status == "Done" else None
                issues.append([f"QS-{r.randint(1000, 99999)}", repo, r.choice(types),
                               r.choice(["Highest", "High", "Medium", "Medium", "Low"]), status, e["name"],
                               r.choice(self.staff)["name"], t.strftime("%Y-%m-%d %H:%M"),
                               res.strftime("%Y-%m-%d %H:%M") if res else "", r.choice([1, 2, 3, 5, 8, 13]),
                               f"Sprint {self.ym[0] % 100}.{(self.ym[1] - 1) * 2 + r.randint(1, 2)}",
                               r.choice(msgs).format(x=r.choice(things), y=repo)])
                if status == "Done":
                    self.count(e["id"], 1)
            for _ in range(pois(r, 110 * k)):
                e = r.choice(eng)
                commits.append(["%040x" % r.getrandbits(160), repo, e["name"], e["email"], self.ts().isoformat(),
                                r.choice(msgs).format(x=r.choice(things), y=repo), r.randint(1, 14),
                                int(r.lognormvariate(3.5, 1.2)), int(r.lognormvariate(2.8, 1.2))])
                self.count(e["id"], 0)
            for _ in range(pois(r, 25 * k)):
                e = r.choice(eng)
                t = self.ts()
                prs.append([r.randint(1, 20000), repo, e["name"], ", ".join(x["name"] for x in r.sample(eng, min(2, len(eng)))),
                            t.strftime("%Y-%m-%d %H:%M"), (t + dt.timedelta(hours=r.lognormvariate(2.6, 1))).strftime("%Y-%m-%d %H:%M"),
                            r.randint(0, 25), int(r.lognormvariate(4.5, 1)), r.choice(["Merged", "Merged", "Merged", "Closed"])])
            for _ in range(pois(r, 70 * k)):
                builds.append([r.randint(10 ** 5, 10 ** 6), repo, r.choice(["main", "main", "release", "feature/x"]),
                               r.choices(["success", "failed", "cancelled"], [85, 12, 3])[0],
                               self.ts().strftime("%Y-%m-%d %H:%M:%S"), int(r.lognormvariate(5.8, .5)),
                               r.choice(["unit", "integration", "e2e", "mobile-build", "deploy-staging", "deploy-prod-us",
                                         "deploy-prod-eu", "deploy-prod-af"])])
        base = f"{F['eng']}/{self.y}/{self.tag}"
        gz_csv(self.sink, f"{base}/Issues export {self.tag}.csv.gz",
               ["Key", "Repository", "Type", "Priority", "Status", "Assignee", "Reporter", "Created", "Resolved",
                "Story points", "Sprint", "Summary"], issues)
        gz_csv(self.sink, f"{base}/Git commit log {self.tag}.csv.gz",
               ["Commit", "Repository", "Author", "Email", "Date", "Message", "Files changed", "Additions", "Deletions"],
               commits)
        wb = new_book()
        add_sheet(wb, "Pull requests", ["PR", "Repository", "Author", "Reviewers", "Opened", "Merged/closed",
                                        "Comments", "Lines changed", "Outcome"], prs, {"Reviewers": 40})
        save_book(self.sink, f"{base}/Pull requests {self.tag}.xlsx", wb, "Pull requests", BANNER)
        gz_csv(self.sink, f"{base}/CI builds {self.tag}.csv.gz",
               ["Build", "Repository", "Branch", "Status", "Started", "Duration seconds", "Stage"], builds)
        d = new_doc(f"Release notes {self.tag}", "Quarrystone platform")
        for x in r.sample(["Schedule: import Primavera P6 XER with resource assignments",
                           "Cost: retention release workflow per contract form", "Field: offline punch list with photo pins",
                           "Closeout: compile O&M manual as one PDF with bookmarks", "Faster IFC viewer for large models",
                           "Multi-currency budgets with locked FX rates", "Kenya VAT on invoices and pay applications",
                           "BCF 3.0 import and export", "SCIM user provisioning", "Daily log templates by region",
                           "Metric / imperial per project", "Audit trail export for owners"], 4):
            bullet(d, x)
        save_doc(self.sink, f"{F['eng']}/{self.y}/Release notes/Release notes {self.tag}.docx", d)
        oncall = self.people("Site Reliability Engineer", "Backend Engineer", "Security Engineer")
        incs = []
        for _ in range(pois(r, 2.2 + len(self.customers) / 120)):
            t = self.ts(hour=r.randrange(24))
            sev = r.choices(["SEV1", "SEV2", "SEV3", "SEV4"], [4, 18, 45, 33])[0]
            region = r.choice([x for x, s in REGION_LAUNCH.items() if s <= self.ym])
            svc = r.choice(repos[:10])
            dur = int(r.lognormvariate(3.6 if sev in ("SEV1", "SEV2") else 3, .8))
            cause = r.choice(["Bad deploy", "Database failover", "Expired certificate", "Object storage latency",
                              "Sync queue backlog after mobile release", "Third-party maps outage",
                              "Config change without review", "Disk full on log volume", "Runaway report query"])
            iid = f"INC-{self.tag.replace('-', '')}-{len(incs) + 1:03d}"
            incs.append([iid, sev, region, svc, t.strftime("%Y-%m-%d %H:%M"), dur, cause, r.choice(oncall)["name"],
                         "Yes" if sev in ("SEV1", "SEV2") else "No"])
            if sev in ("SEV1", "SEV2"):
                d = new_doc(f"Postmortem {iid}: {svc} ({region})", f"{sev} | {t:%d %b %Y %H:%M} UTC | {dur} minutes")
                d.add_heading("Summary", 1)
                d.add_paragraph(f"{svc} in the {region} region was degraded for {dur} minutes. Root cause: "
                                f"{cause.lower()}. Mobile users kept working offline; changes synced after recovery.")
                d.add_heading("Action items", 1)
                doc_table(d, ["Action", "Owner", "Due"], [[a, r.choice(oncall)["name"], (self.eom + dt.timedelta(days=14)).isoformat()]
                                                          for a in r.sample(["Add canary stage per region",
                                                                             "Alert on certificate expiry",
                                                                             "Back-pressure on sync queue",
                                                                             "Update runbook", "Load test report queries",
                                                                             "Failover drill each quarter"], 3)])
                save_doc(self.sink, f"{F['eng']}/{self.y}/Postmortems/{iid} {safe(svc, 40)}.docx", d)
        self.incidents = incs
        wb = new_book()
        add_sheet(wb, "Incidents", ["Incident", "Severity", "Region", "Service", "Started", "Minutes", "Cause",
                                    "On call", "Postmortem"], incs, {"Cause": 40})
        save_book(self.sink, f"{base}/Production incidents {self.tag}.xlsx", wb, "Incidents", BANNER)

    # ---------------- platform usage and reliability
    def usage(self):
        r, w, k = self.rng, self.w, self.detail
        rows = []
        for c in self.customers:
            start, seats, mods, tier = w.term(c, self.ym)
            act = int(seats * r.uniform(.45, .95))
            projs = self.proj_count.get(c["id"], 0)
            rows.append([self.tag, c["code"], c["name"], c["region"], c["residency"], tier, seats, act,
                         round(act / max(seats, 1), 3), projs,
                         int(act * r.uniform(30, 120)) if "Schedule" in mods else 0,
                         int(act * r.uniform(5, 30)) if "Estimate & Cost" in mods else 0,
                         int(act * r.uniform(40, 260)) if "Field" in mods else 0,
                         int(act * r.uniform(10, 60)) if "Field" in mods else 0,
                         int(act * r.uniform(0, 3)) if "Field" in mods else 0,
                         int(act * r.uniform(1, 40)) if "Closeout" in mods else 0,
                         int(act * r.uniform(50, 900)), round(projs * r.uniform(2, 40) + seats * .3, 1)])
        wb = new_book()
        add_sheet(wb, "Usage by customer", ["Month", "Customer", "Name", "Region", "Hosting region", "Tier", "Seats",
                                            "Monthly active users", "Activation", "Live projects",
                                            "Schedule activities updated", "Cost transactions", "Photos uploaded",
                                            "Offline sessions", "Sync conflicts (manual)", "Closeout documents",
                                            "API calls (thousands)", "Storage GB"], rows, {"Name": 34})
        save_book(self.sink, f"{F['usage']}/{self.y}/Usage by customer {self.tag}.xlsx", wb, "Usage", BANNER)
        self.mau = sum(x[7] for x in rows)
        regions = [x for x, s in REGION_LAUNCH.items() if s <= self.ym]
        sla = []
        for reg in regions:
            down = sum(i[5] for i in self.incidents if i[2] == reg and i[1] in ("SEV1", "SEV2"))
            avail = round(100 * (1 - down / (self.days * 1440)), 4)
            sla.append([self.tag, reg, avail, 99.9, "Met" if avail >= 99.9 else "Missed",
                        int(r.lognormvariate(5.3, .2)), int(r.lognormvariate(6.2, .3)), round(r.uniform(.01, .3), 3)])
        wb = new_book()
        add_sheet(wb, "Availability", ["Month", "Region", "Availability %", "SLA target %", "SLA", "p50 API ms",
                                       "p95 API ms", "Error rate %"], sla)
        save_book(self.sink, f"{F['usage']}/{self.y}/SLA and availability {self.tag}.xlsx", wb, "SLA", BANNER)
        if k > 0:
            sample = [c for c in self.customers if "Field" in w.term(c, self.ym)[2]][:int(40 * k)]

            def events():
                for c in sample:
                    for _ in range(int(200 * k)):
                        t = dt.datetime.combine(self.d0, dt.time()) + dt.timedelta(seconds=r.randrange(self.days * 86400))
                        off = r.randint(0, 3600 * 8) if r.random() < .3 else 0
                        yield [t.strftime("%Y-%m-%dT%H:%M:%SZ"), c["code"], f"D{r.getrandbits(32):08x}",
                               r.choice(["ios", "android", "android", "windows"]),
                               r.choice(["daily_log.save", "photo.capture", "punch.create", "inspection.complete",
                                         "rfi.create", "drawing.open", "sync.push", "sync.pull"]),
                               off, r.choices(["none", "auto_merged", "manual"], [94, 5, 1])[0] if off else "none",
                               c["residency"]]
            gz_csv(self.sink, f"{F['usage']}/{self.y}/Mobile sync events sample {self.tag}.csv.gz",
                   ["Timestamp", "Customer", "Device", "Platform", "Event", "Seconds offline before sync",
                    "Conflict", "Hosting region"], events())

    # ---------------- customer project workspaces (sample, anonymised by consent)
    def workspaces(self):
        live = [p for p in self.live_projects if self.cu_by[p["cust"]]["sample"]]
        for p in live[:int(30 * self.detail) or 0]:
            SD.SiteMonth(self, p, self.cu_by[p["cust"]]).run()

    # ---------------- support
    def support(self):
        r = self.rng
        agents = self.people("Support Specialist", "Customer Success Manager")
        rows = []
        cats = ["XER import failed", "Offline data not syncing", "Photo pins on wrong sheet", "Pay application totals",
                "Retention calculation question", "SSO login failure", "User invite not received", "IFC model too large",
                "Change order approval stuck", "Report export", "Mobile app crash", "API integration help",
                "Data residency question", "VAT / tax setting", "Closeout package compile error", "Feature request"]
        for _ in range(pois(r, self.mau / 60 if hasattr(self, "mau") else 20)):
            a = r.choice(agents)
            c = r.choice(self.customers) if self.customers else None
            if not c:
                break
            t = self.ts(hour=r.randrange(24))
            rows.append([f"SUP-{r.randrange(10 ** 7):07d}", t.strftime("%Y-%m-%d %H:%M"), c["code"], c["name"],
                         c["tier"], r.choice(cats), r.choice(["Email", "In-app chat", "Phone", "Web form"]),
                         r.choice(["Low", "Normal", "Normal", "High", "Urgent"]), a["name"],
                         int(r.lognormvariate(3.8 if c["tier"] == "Enterprise" else 4.3, .8)),
                         r2(r.lognormvariate(2.4, 1)), r.choices([5, 4, 3, 2, 1, None], [40, 27, 11, 6, 4, 12])[0]])
            self.count(a["id"], 2)
        rows.sort(key=lambda x: x[1])
        wb = new_book()
        add_sheet(wb, "Tickets", ["Ticket", "Opened", "Customer", "Name", "Tier", "Category", "Channel", "Priority",
                                  "Agent", "First response min", "Resolution hours", "CSAT"], rows,
                  {"Name": 30, "Category": 30, "Agent": 22})
        save_book(self.sink, f"{F['support']}/{self.y}/Support tickets {self.tag}.xlsx", wb, "Support", BANNER)
        self.tickets_n = len(rows)

    # ---------------- security & compliance evidence
    def security(self):
        r = self.rng
        base = f"{F['sec']}/{self.y}"
        vulns = [[f"VULN-{self.tag.replace('-', '')}-{i + 1:03d}", r.choice(["Critical", "High", "Medium", "Medium", "Low"]),
                  r.choice(["Container image", "Dependency", "Cloud config", "Web app (DAST)", "Mobile app"]),
                  r.choice(["Outdated TLS library", "Public storage bucket policy", "XSS in report viewer",
                            "Vulnerable npm package", "Missing rate limit", "Weak IAM policy", "Outdated base image"]),
                  r.choice(["Fixed", "Fixed", "Fixed", "In progress", "Risk accepted"]), r.randint(1, 45)]
                 for i in range(r.randint(8, 40))]
        wb = new_book()
        add_sheet(wb, "Vulnerabilities", ["Finding", "Severity", "Source", "Title", "Status", "Days open"], vulns,
                  {"Title": 34})
        save_book(self.sink, f"{base}/Vulnerability management {self.tag}.xlsx", wb, "Vulnerabilities", BANNER)
        if self.ym[1] % 3 == 0:
            rows = [[e["id"], e["name"], e["role"], sys_, r.choice(["Confirmed", "Confirmed", "Confirmed", "Removed"]),
                     next((x["name"] for x in self.staff if x["id"] == e.get("manager")), "CEO")]
                    for e in self.staff for sys_ in r.sample(["Production database (read)", "Cloud console",
                                                              "Customer support tool", "Billing system",
                                                              "Source code", "Admin panel"], 2)]
            wb = new_book()
            add_sheet(wb, "Access review", ["Employee", "Name", "Role", "System", "Decision", "Reviewer"], rows,
                      {"Name": 22, "Role": 28, "System": 28})
            save_book(self.sink, f"{base}/Quarterly access review Q{self.ym[1] // 3} {self.y}.xlsx", wb,
                      "Access review", BANNER)
            dsar = [[f"DSAR-{self.tag}-{i + 1}", r.choice(["Access", "Erasure", "Rectification"]),
                     r.choice(["GDPR", "Kenya DPA", "UK GDPR", "CCPA"]), r.randint(3, 28), "Completed"]
                    for i in range(r.randint(0, 6))]
            wb = new_book()
            add_sheet(wb, "Data subject requests", ["Request", "Type", "Law", "Days to complete", "Status"], dsar)
            save_book(self.sink, f"{base}/Data subject requests Q{self.ym[1] // 3} {self.y}.xlsx", wb, "DSAR", BANNER)
        if self.ym[1] == 11 and self.ym[0] >= 2019:
            for title, auditor in [("SOC 2 Type II report summary", "Hallmark Assurance LLP"),
                                   ("ISO/IEC 27001 surveillance audit report", "Certora Registrar")]:
                d = new_doc(f"{title} {self.y}", f"Auditor: {auditor} (fictional)")
                doc_table(d, ["Item", "Result"], [["Period", f"{self.ym[0] - 1}-12-01 to {self.y}-11-30"],
                                                  ["Opinion / result", r.choice(["Unqualified", "Certification maintained"])],
                                                  ["Exceptions / minor nonconformities", r.randint(0, 3)],
                                                  ["Scope", "Quarrystone platform, all hosting regions"]])
                save_doc(self.sink, f"{base}/Audits/{title} {self.y}.docx", d)

    # ---------------- marketing
    def marketing(self):
        r = self.rng
        rows = []
        for ch in ("Search ads", "LinkedIn", "Trade shows", "Webinars", "Content / SEO", "Partner referrals",
                   "Industry associations"):
            spend = r2(r.uniform(2000, 30000) * (1 + len(self.customers) / 200))
            leads = int(spend / r.uniform(90, 600))
            rows.append([self.tag, ch, spend, leads, int(leads * r.uniform(.1, .35)), int(leads * r.uniform(.01, .06))])
        self.mkt_spend = sum(x[2] for x in rows)
        wb = new_book()
        add_sheet(wb, "Campaigns", ["Month", "Channel", "Spend USD", "Leads", "Qualified", "Opportunities"], rows)
        save_book(self.sink, f"{F['mkt']}/{self.y}/Marketing performance {self.tag}.xlsx", wb, "Marketing", BANNER)

    # ---------------- HR and payroll (three offices)
    def hr(self):
        r = self.rng
        pay, self.pay_lines = [], {}
        self.payroll = self.taxes = self.commission = 0.0
        new_arr = sum(self.w.annual_price(c, self.ym) for c in self.new)
        aes = [e for e in self.staff if e["role"] in ("Account Executive", "Chief Revenue Officer")]
        for e in self.staff:
            region, country, cur, mult, tax_rate = OFFICES[e["office"]]
            base = self.w.pay(e, self.ym)
            allow = r2(base * (.06 if e["office"] == "Nairobi" else .03))
            comm = r2(new_arr * .1 / len(aes)) if e in aes and new_arr else 0.0
            bonus = r2(base * r.uniform(.05, .12)) if self.ym[1] == 3 and r.random() < .7 else 0.0
            leave = r.choices([0, 0, 0, 1, 2, 5], [45, 20, 10, 10, 8, 7])[0]
            gross = r2(base + allow + comm + bonus)
            tax = r2(gross * tax_rate)
            self.payroll += gross
            self.taxes += tax
            self.commission += comm
            self.pay_lines[e["id"]] = (base, allow, comm, 0, bonus, gross, tax, leave)
            pay.append([e["id"], e["name"], e["office"], e["dept"], e["role"], cur, r2(base / FX[cur]),
                        r2(gross / FX[cur]), base, allow, comm, bonus, gross, tax])
        wb = new_book()
        add_sheet(wb, "Payroll", ["Employee", "Name", "Office", "Department", "Role", "Pay currency", "Base (local)",
                                  "Gross (local)", "Base USD", "Allowances USD", "Commission USD", "Bonus USD",
                                  "Gross USD", "Employer taxes & benefits USD"], pay, {"Name": 22, "Role": 30})
        ws = wb["Payroll"]
        n = ws.max_row
        ws.cell(n + 1, 1, "TOTAL")
        for col in "IJKLMN":
            ws[f"{col}{n + 1}"] = f"=SUM({col}2:{col}{n})"
        save_book(self.sink, f"{F['hr']}/{self.y}/Payroll register {self.tag}.xlsx", wb, "Payroll", BANNER)
        self.payroll, self.taxes = r2(self.payroll), r2(self.taxes)
        for e in self.w.staff:
            if e["hired"] == self.ym:
                S.joiner_docs(self, e)
            elif e["left"] == self.ym:
                S.leaver_docs(self, e)

    # ---------------- finance: subscriptions billed annually in advance, revenue recognised monthly
    def finance(self):
        r, L, w = self.rng, self.L, self.w
        eom = self.eom
        S.expenses(self)
        for when, amt, what in [((2017, 1), 4000000, "Seed round"), ((2019, 6), 18000000, "Series A"),
                                ((2022, 3), 55000000, "Series B")]:
            if self.ym == when:
                self.post(self.d0, f"EQ-{self.tag}", f"{what} equity financing", [("1000", amt, 0), ("3000", 0, amt)])
        invoices = []
        subs = L.setdefault("subs", [])
        for c in self.new + self.renewals:
            price = w.annual_price(c, self.ym)
            vat = r2(price * VAT.get(c["country"], 0)) if c["country"] in ("Kenya", "Uganda", "Rwanda", "Tanzania",
                                                                            "Ethiopia", "Nigeria", "Ghana",
                                                                            "South Africa", "Belgium") else 0.0
            no = self._inv_no()
            due = self.d0 + dt.timedelta(days=c["net"])
            self.post(self.d0, no, f"Annual subscription {c['name']}", [("1100", price + vat, 0), ("2400", 0, price),
                                                                        ("2100", 0, vat)])
            subs.append({"cust": c["id"], "left": 12, "monthly": r2(price / 12), "total": price, "done": 0.0})
            self._ar(no, c, due, price + vat)
            invoices.append([no, self.d0.isoformat(), c["code"], c["name"], "Subscription (12 months)", c["currency"],
                             r2(price / FX[c["currency"]]), r2(vat / FX[c["currency"]]), price + vat, due.isoformat()])
            self.invoice_pdf(no, self.d0, due, c, f"{w.term(c, self.ym)[3]} subscription - "
                                                  f"{', '.join(w.term(c, self.ym)[2])} - {w.term(c, self.ym)[1]} users",
                             price, vat)
        rec = 0.0
        for s in subs:
            if s["left"] <= 0:
                continue
            amt = r2(s["total"] - s["done"]) if s["left"] == 1 else s["monthly"]
            s["done"] = r2(s["done"] + amt)
            s["left"] -= 1
            rec += amt
        rec = r2(rec)
        if rec:
            self.post(eom, f"REVREC-{self.tag}", "Subscription revenue recognised", [("2400", rec, 0), ("4000", 0, rec)])
        L["subs"] = [s for s in subs if s["left"] > 0]
        for p in self.impls:
            amount, hours = self.billable[p["id"]]
            c = self.cu_by[p["cust"]]
            no = self._inv_no()
            due = eom + dt.timedelta(days=c["net"])
            self.post(eom, no, f"Services {p['code']}", [("1100", amount, 0), ("4100", 0, amount)])
            self._ar(no, c, due, amount)
            invoices.append([no, eom.isoformat(), c["code"], c["name"], f"{p['type']} ({p['model']}, {hours} h)",
                             c["currency"], r2(amount / FX[c["currency"]]), 0.0, amount, due.isoformat()])
            self.invoice_pdf(no, eom, due, c, f"{p['type']} - {p['code']} ({p['model']}, {hours:,.1f} h)", amount, 0.0)
        still = []
        for inv in L.get("ar", []):
            if inv["paid"] and inv["paid"] <= eom.isoformat():
                self.post(dt.date.fromisoformat(max(inv["paid"], self.d0.isoformat())), "RCPT " + inv["no"],
                          f"Receipt {inv['cust']}", [("1000", inv["total"], 0), ("1100", 0, inv["total"])])
            elif not inv["paid"] and dt.date.fromisoformat(inv["due"]) + dt.timedelta(days=240) <= eom:
                self.post(eom, "WO " + inv["no"], f"Bad debt {inv['cust']}", [("5900", inv["total"], 0),
                                                                             ("1100", 0, inv["total"])])
            else:
                still.append(inv)
        L["ar"] = still
        vat_bal = L.setdefault("bal", {}).get("2100", 0)
        if vat_bal < 0:
            self.post(eom, f"VAT-{self.tag}", "VAT / sales tax returns paid", [("2100", -vat_bal, 0), ("1000", 0, -vat_bal)])
        self.post(eom, f"PAYROLL-{self.tag}", "Payroll (Denver, Antwerp, Nairobi)", [("5000", self.payroll - self.commission, 0),
                                                                                     ("6100", self.commission, 0),
                                                                                     ("1000", 0, self.payroll)])
        self.post(eom, f"PTAX-{self.tag}", "Employer payroll taxes, social security and benefits",
                  [("5050", self.taxes, 0), ("1000", 0, self.taxes)])
        cn, sn, imp = w.load(self.ym)
        staff = len(self.staff)
        regions = [x for x, s in REGION_LAUNCH.items() if s <= self.ym]
        costs = [("5200", f"Cloud hosting - {reg}", 6000 + sn * 900 / len(regions)) for reg in regions] + [
            ("5250", "Maps, OCR and e-signature APIs", 1500 + sn * 140), ("5300", "Marketing campaigns and events", self.mkt_spend),
            ("5400", "Offices Denver, Antwerp, Nairobi", 18000 + staff * 420), ("5500", "Internal software and tools", staff * 260 + 4000),
            ("5600", "Legal, audit and certification", 15000 + (60000 if self.ym[1] == 11 else 0)),
            ("5700", "Insurance (cyber, PI, D&O)", 6000 + staff * 50), ("5100", "Contract developers and translators", imp * r.uniform(2000, 9000)),
            ("6000", "Recruiting and training", staff * r.uniform(60, 180)), ("6300", "Bank charges and FX", 800 + cn * 6)]
        vendors = {"5200": "Stratus Cloud", "5250": "Mapline APIs", "5300": "Buildreach Media", "5400": "Tri-City Workspaces",
                   "5500": "Toolstack Software", "5600": "Ledgerwise Advisory", "5700": "Anchorpoint Insurance",
                   "5100": "Northbridge Dev Partners", "6000": "Talentway Recruiting", "6300": "Meridian Bank"}
        bills = []
        for acct, desc, amt in costs:
            amt = r2(amt)
            if amt <= 0:
                continue
            L["bill_no"] = L.get("bill_no", 0) + 1
            no = f"BILL-{L['bill_no']:06d}"
            bdate = self.d0 + dt.timedelta(days=r.randrange(self.days))
            bills.append([no, bdate.isoformat(), vendors[acct], desc, ACCOUNTS[acct][0], amt])
            self.post(bdate, no, f"{vendors[acct]}: {desc}", [(acct, amt, 0), ("2000", 0, amt)])
            self.post(min(eom, bdate + dt.timedelta(days=30)), "PMT " + no, f"Payment {vendors[acct]}",
                      [("2000", amt, 0), ("1000", 0, amt)])
        if self.ym[1] in (1, 7):
            capex = r2(staff * 1700)
            self.post(self.d0, f"CAPEX-{self.tag}", "Laptops, test phones and rugged tablets",
                      [("1500", capex, 0), ("1000", 0, capex)])
        cap = r2(sum(self.pay_lines[e["id"]][0] for e in self.staff if e["dept"] == "Engineering") * .25)
        if cap:
            self.post(eom, f"CAPDEV-{self.tag}", "Capitalised software development (25% of engineering salaries)",
                      [("1600", cap, 0), ("5000", 0, cap)])
        bal = L.setdefault("bal", {})
        dep = r2(bal.get("1500", 0) / 36)
        amort = r2(bal.get("1600", 0) / 60)
        if dep or amort:
            self.post(eom, f"DEP-{self.tag}", "Depreciation and amortisation",
                      [("5800", dep + amort, 0), ("1510", 0, dep), ("1610", 0, amort)])
        for _, _, a, _, _, dr, cr in self.gl:
            bal[a] = r2(bal.get(a, 0) + dr - cr)
        base = f"{F['fin']}/{self.y}"
        wb = new_book()
        add_sheet(wb, "Journal", ["Date", "Reference", "Account", "Account name", "Description", "Debit", "Credit"],
                  [[str(x[0])] + x[1:] for x in sorted(self.gl, key=lambda x: str(x[0]))],
                  {"Description": 48, "Account name": 36})
        ws = wb["Journal"]
        n = ws.max_row
        ws[f"F{n + 1}"], ws[f"G{n + 1}"] = f"=SUM(F2:F{n})", f"=SUM(G2:G{n})"
        save_book(self.sink, f"{base}/General ledger/General ledger {self.tag}.xlsx", wb, "GL", BANNER)
        tb = [[a, ACCOUNTS[a][0], ACCOUNTS[a][1], max(bal.get(a, 0), 0), max(-bal.get(a, 0), 0)] for a in sorted(ACCOUNTS)]
        wb = new_book()
        add_sheet(wb, "Trial balance", ["Account", "Name", "Type", "Debit", "Credit"], tb, {"Name": 44})
        ws = wb["Trial balance"]
        n = ws.max_row
        ws[f"D{n + 1}"], ws[f"E{n + 1}"] = f"=SUM(D2:D{n})", f"=SUM(E2:E{n})"
        ws.cell(n + 2, 2, "Difference")
        ws[f"D{n + 2}"] = f"=D{n + 1}-E{n + 1}"
        save_book(self.sink, f"{base}/Trial balance/Trial balance {self.tag}.xlsx", wb, "TB", BANNER)
        wb = new_book()
        add_sheet(wb, "Customer invoices", ["Invoice", "Date", "Customer", "Name", "Description", "Currency",
                                            "Net (invoice currency)", "VAT (invoice currency)", "Total USD", "Due"],
                  invoices, {"Name": 30, "Description": 44})
        add_sheet(wb, "Vendor bills", ["Bill", "Date", "Vendor", "Description", "Expense account", "Amount USD"], bills,
                  {"Vendor": 26, "Description": 36, "Expense account": 36})
        save_book(self.sink, f"{base}/Billing/Invoices and bills {self.tag}.xlsx", wb, "Billing", BANNER)
        aging = []
        for inv in L["ar"]:
            days = (eom - dt.date.fromisoformat(inv["due"])).days
            aging.append([inv["no"], inv["cust"], inv["due"], inv["total"], max(days, 0),
                          "Current" if days <= 0 else "1-30" if days <= 30 else "31-60" if days <= 60 else
                          "61-90" if days <= 90 else "90+"])
        wb = new_book()
        add_sheet(wb, "AR aging", ["Invoice", "Customer", "Due", "Open USD", "Days overdue", "Bucket"], aging,
                  {"Customer": 30})
        save_book(self.sink, f"{base}/Receivables/AR aging {self.tag}.xlsx", wb, "AR aging", BANNER)
        pl = {a: r2(-sum(dr - cr for _, _, aa, _, _, dr, cr in self.gl if aa == a)) for a in ACCOUNTS
              if ACCOUNTS[a][1] in ("Revenue", "Expense")}
        L.setdefault("pl", {})[self.tag] = pl
        self.pl = pl
        if self.ym[1] == 12:
            self.year_end()

    def _inv_no(self):
        self.L["inv_no"] = self.L.get("inv_no", 0) + 1
        return f"QS-INV-{self.L['inv_no']:06d}"

    def _ar(self, no, c, due, total):
        r = self.rng
        delay = r.choices([0, 5, 20, 45, 90, None], [42, 26, 17, 9, 5, 1])[0]
        paid = None if delay is None else due + dt.timedelta(days=delay)
        self.L.setdefault("ar", []).append({"no": no, "cust": c["name"], "due": due.isoformat(), "total": r2(total),
                                            "paid": paid.isoformat() if paid else None})

    def invoice_pdf(self, no, date, due, c, line, net, vat):
        path = self.sink.path(f"{F['fin']}/{self.y}/Invoices/{self.tag}/{no} {safe(c['name'], 50)}.pdf")
        st = getSampleStyleSheet()
        doc = SimpleDocTemplate(path, pagesize=A4, title=f"Invoice {no}", author=CO, subject=BANNER)
        cur, fx = c["currency"], FX[c["currency"]]
        rows = [["Description", f"Amount {cur}"], [line, f"{net / fx:,.2f}"]]
        if vat:
            rows.append([f"VAT {VAT.get(c['country'], 0) * 100:.0f}%", f"{vat / fx:,.2f}"])
        elif c["region"] == "Europe" and c["country"] != "Belgium":
            rows.append(["VAT reverse charge (Article 196, Directive 2006/112/EC)", "0.00"])
        rows.append(["Total due", f"{(net + vat) / fx:,.2f}"])
        t = Table(rows, colWidths=[370, 110])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3B4A3F")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -2), 0.4, colors.grey),
                               ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")]))
        entity = {"Americas": f"{CO} Inc., Denver", "Europe": f"{CO} BV, Antwerp", "Africa": f"{CO} Kenya Ltd, Nairobi"}
        doc.build([Paragraph(f"<b>{entity[c['region']]}</b>", st["Title"]), Paragraph(f"INVOICE {no}", st["Heading2"]),
                   Paragraph(f"Bill to: {c['name']}, {c['city']}, {c['country']}<br/>Attn: {c['contact']}<br/>"
                             f"Date: {date:%d %b %Y} &nbsp; Due: {due:%d %b %Y} &nbsp; Customer: {c['code']}", st["Normal"]),
                   Spacer(1, 14), t, Spacer(1, 14), Paragraph(f"Pay by bank transfer quoting {no}. {BANNER}", st["Italic"])])
        self.sink.wrote(path)

    def year_end(self):
        L, y = self.L, self.ym[0]
        months = [f"{y}-{m:02d}" for m in range(1, 13) if f"{y}-{m:02d}" in L["pl"]]
        wb = new_book()
        ws = wb.create_sheet("Income statement")
        ws.append([f"{CO} - Income statement {y} (USD, fictional)"])
        ws.append(["Account", "Name"] + months + ["Full year"])
        last = chr(ord("C") + len(months) - 1)
        for kind, sign in (("Revenue", 1), ("Expense", -1)):
            for a in sorted(ACCOUNTS):
                if ACCOUNTS[a][1] == kind:
                    ws.append([a, ACCOUNTS[a][0]] + [sign * L["pl"][m].get(a, 0) for m in months])
                    ws[f"{chr(ord(last) + 1)}{ws.max_row}"] = f"=SUM(C{ws.max_row}:{last}{ws.max_row})"
        ws.column_dimensions["B"].width = 44
        bs = wb.create_sheet("Balance sheet")
        bs.append([f"{CO} - Balance sheet at 31 Dec {y} (USD, fictional; before year-end close)"])
        for a in sorted(ACCOUNTS):
            if ACCOUNTS[a][1] in ("Asset", "Liability", "Equity"):
                bs.append([a, ACCOUNTS[a][0], ACCOUNTS[a][1], L["bal"].get(a, 0) * (1 if ACCOUNTS[a][1] == "Asset" else -1)])
        bs.column_dimensions["B"].width = 44
        save_book(self.sink, f"{F['fin']}/{y}/Financial statements {y}.xlsx", wb, "Financial statements", BANNER)
        wb = new_book()
        ws = wb.create_sheet("Budget")
        ws.append([f"{CO} - Operating budget {y + 1} (USD, fictional)"])
        ws.append(["Growth assumption", 0.3])
        ws.append(["Account", "Name", f"{y} actual"] + [dt.date(y + 1, m, 1).strftime("%b") for m in range(1, 13)] + ["Total"])
        for a in sorted(ACCOUNTS):
            if ACCOUNTS[a][1] in ("Revenue", "Expense"):
                act = r2(sum(abs(L["pl"][m].get(a, 0)) for m in months))
                row = ws.max_row + 1
                ws.append([a, ACCOUNTS[a][0], act] + [f"=$C{row}*(1+$B$2)/12" for _ in range(12)] + [f"=SUM(D{row}:O{row})"])
        ws.column_dimensions["B"].width = 44
        save_book(self.sink, f"{F['fin']}/{y + 1}/Budget {y + 1}.xlsx", wb, "Budget", BANNER)

    # ---------------- reports, meetings, mail
    def reports(self):
        r, w = self.rng, self.w
        arr = sum(w.annual_price(c, self.ym) for c in self.customers)
        prev = self.L.get("arr_prev", arr)
        self.L["arr_prev"] = arr
        rev = sum(v for a, v in self.pl.items() if ACCOUNTS[a][1] == "Revenue")
        exp = -sum(v for a, v in self.pl.items() if ACCOUNTS[a][1] == "Expense")
        sc = getattr(self, "site_counts", {})
        wb = new_book()
        add_sheet(wb, "Company KPIs", ["Measure", "Value"], [
            ["Month", self.tag], ["Customers", len(self.customers)], ["New customers", len(self.new)],
            ["Churned customers", len(self.churned)], ["ARR USD", r2(arr)], ["ARR change USD", r2(arr - prev)],
            ["Monthly active users", getattr(self, "mau", 0)], ["Live construction projects on platform",
                                                                len(self.live_projects)],
            ["Implementation engagements", len(self.impls)], ["Headcount", len(self.staff)],
            ["Revenue USD (month)", r2(rev)], ["Expenses USD (month)", r2(exp)], ["Net USD", r2(rev - exp)],
            ["Production incidents", len(self.incidents)], ["Support tickets", self.tickets_n],
            ["Sample workspace photos synced", sc.get("photos", 0)], ["Cash at bank USD", self.L["bal"].get("1000", 0)]],
            {"Measure": 40})
        save_book(self.sink, f"{F['rep']}/{self.y}/KPI dashboard {self.tag}.xlsx", wb, "KPIs", BANNER)
        if self.ym[1] % 3 == 0:
            q = self.ym[1] // 3
            d = new_doc(f"Board update Q{q} {self.y}", f"{CO} | quarter ending {self.d0:%B %Y}")
            rows = []
            for mm in [ym_s(ym_add(self.ym, -k)) for k in (2, 1, 0)]:
                pl = self.L["pl"].get(mm, {})
                a = sum(v for k, v in pl.items() if ACCOUNTS[k][1] == "Revenue")
                b = -sum(v for k, v in pl.items() if ACCOUNTS[k][1] == "Expense")
                rows.append([mm, r2(a), r2(b), r2(a - b)])
            doc_table(d, ["Month", "Revenue", "Expenses", "Net"], rows)
            doc_table(d, ["Measure", "Value"], [["ARR USD", r2(arr)], ["Customers", len(self.customers)],
                                                ["Headcount", len(self.staff)]])
            d.add_heading("Highlights", 1)
            for x in r.sample(["Two enterprise contractors signed in Europe", "Africa hosting region at record usage",
                               "SOC 2 Type II renewed without exceptions", "P6 migration time cut by half",
                               "Offline sync conflicts below 1 in 1,000 edits", "Public agency framework win",
                               "Net revenue retention above 115%"], 3):
                bullet(d, x)
            d.add_heading("Risks", 1)
            for x in r.sample(["Construction slowdown in two markets", "Longer public procurement cycles",
                               "Competition from ERP suites", "FX exposure on KES and EUR revenue",
                               "Senior engineer attrition"], 2):
                bullet(d, x)
            save_doc(self.sink, f"{F['rep']}/{self.y}/Board updates/Board update {self.y} Q{q}.docx", d)

    def meetings(self):
        r = self.rng
        heads = [e for e in self.staff if e["role"] in HEADS.values()]
        if not heads:
            return
        base = f"{F['mail']}/{self.y}"
        name_of = {e["role"]: e["name"] for e in heads}
        ceo = heads[0]["name"]
        for day in range(0, self.days, 7):
            date = self.d0 + dt.timedelta(days=day)
            lines = [(ceo, "Morning all. Pipeline, delivery, platform, people."),
                     (name_of.get("Chief Revenue Officer", ceo), f"{len(self.new)} new customers so far this month, "
                                                                f"{len(self.renewals)} renewals due."),
                     (name_of.get("VP Customer Success", ceo), r.choice(["Two go-lives next week in Nairobi and Lyon.",
                                                                         "One enterprise account at risk; QBR booked.",
                                                                         "Field adoption is up after the offline release."])),
                     (name_of.get("Chief Technology Officer", ceo),
                      f"{sum(1 for i in self.incidents if i[1] in ('SEV1', 'SEV2'))} serious incidents this month; "
                      "the sync queue fix ships Thursday."),
                     (name_of.get("Head of People", ceo), r.choice(["Three engineering offers out in Nairobi.",
                                                                    "Review cycle starts next week.",
                                                                    "Antwerp hiring is on plan."])),
                     (ceo, "Thanks. Actions in the doc.")]
            S.zoom_export(self, f"{base}/Zoom Meetings/{date} 1500 Leadership weekly", "Leadership weekly",
                          dt.datetime.combine(date, dt.time(15, 0)), [(e["name"], e["email"], False) for e in heads],
                          lines, ceo, r.randint(30, 50))
        for p in self.impls[:12]:
            team = self.team.get(p["id"], [])[:4]
            if not team:
                continue
            c = self.cu_by[p["cust"]]
            start = dt.datetime.combine(self.d0 + dt.timedelta(days=min(self.days - 1, 8 + p["id"] % 15)), dt.time(14, 0))
            lines = [(team[0]["name"], f"Weekly check-in for {p['type'].lower()}."),
                     (c["contact"], r.choice(["Our superintendents like the offline daily log.",
                                              "Can we import the hospital schedule before month end?",
                                              "IT still needs the SSO metadata from you."])),
                     (team[-1]["name"], r.choice(["I'll send the metadata today.", "Yes, we validated the logic already.",
                                                  "We'll run another field training on site."])),
                     (team[0]["name"], "Notes and actions are in the shared workspace.")]
            S.meet_export(self, f"{base}/Google Meet/{start:%Y-%m-%d} Implementation check-in {safe(p['code'], 20)}",
                          f"Implementation check-in {p['code']}", start,
                          [(e["name"], e["email"], False) for e in team] + [(c["contact"], f"pm@{c['domain']}", True)],
                          lines, r.randint(25, 45))
        if self.ym[1] % 3 == 0:
            csms = self.people("Customer Success Manager")
            for c in [x for x in self.customers if x["tier"] == "Enterprise"][:20]:
                csm = csms[c["id"] % len(csms)]
                start = dt.datetime.combine(self.d0 + dt.timedelta(days=10 + c["id"] % 15), dt.time(16, 0))
                lines = [(csm["name"], f"Thanks for joining, {c['contact'].split()[0]}. Quarterly business review."),
                         (csm["name"], f"Your teams are running {self.proj_count.get(c['id'], 0)} "
                                       "live projects on the platform."),
                         (c["contact"], r.choice(["Pay applications are much faster now.",
                                                  "We want the closeout module for the next two projects.",
                                                  "Our subcontractors struggle with logins."])),
                         (csm["name"], r.choice(["We'll set up a subcontractor guest workflow.",
                                                 "I'll send a closeout proposal this week.",
                                                 "Great, I'll share the benchmark report."]))]
                S.zoom_export(self, f"{base}/Zoom Meetings/{start:%Y-%m-%d} 1600 QBR {safe(c['name'], 50)}",
                              "Quarterly business review", start,
                              [(csm["name"], csm["email"], False), (c["contact"], f"pm@{c['domain']}", True)], lines,
                              csm["name"], r.randint(35, 55))
        for c in self.renewals[:40]:
            self.mail(self.ts(), f"renewals@{DOMAIN}", f"finance@{c['domain']}", f"Your Quarrystone renewal ({c['code']})",
                      f"Hello {c['contact'].split()[0]},\n\nYour subscription renews this month. The order form and "
                      f"invoice are attached in the portal.\n\nThanks,\n{CO} Customer Success\n")
        for c in self.new[:40]:
            self.mail(self.ts(), f"onboarding@{DOMAIN}", f"pm@{c['domain']}", f"Welcome to Quarrystone, {c['name']}",
                      f"Hi {c['contact'].split()[0]},\n\nYour workspace is ready in the {c['residency']} region. "
                      f"Your onboarding consultant will contact you this week.\n\n{CO}\n")

    def write_mail(self):
        for i in self.incidents:
            if i[1] in ("SEV1", "SEV2"):
                self.mail(self.ts(), f"status@{DOMAIN}", f"customers-{i[2].lower()}@{DOMAIN}",
                          f"[{i[1]}] Service degradation in {i[2]} - resolved",
                          f"{i[3]} was degraded for {i[5]} minutes. Mobile apps kept working offline. Root cause: "
                          f"{i[6].lower()}.\n")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for k, (t, subj, raw) in enumerate(sorted(self.emails, key=lambda x: x[0]), 1):
                z.writestr(f"{k:05d} {safe(subj, 70)}.eml", raw)
        self.sink.write_bytes(f"{F['mail']}/{self.y}/Email exports/Mailbox export {self.tag}.zip", buf.getvalue())


# ---------------------------------------------------------------- HR documents by office

def joiner_docs(m, e):
    region, country, cur, mult, tax = OFFICES[e["office"]]
    base = S.person_dir(m.F, e)
    pay = m.w.pay(e, m.ym)
    local = pay / FX[cur]
    mgr = next((x for x in m.w.staff if x["id"] == e["manager"]), None)
    terms = {"Denver": [["Base salary", f"USD {local * 12:,.0f} per year, paid semi-monthly"],
                        ["Benefits", "Medical, dental and vision; 401(k) with 4% match"],
                        ["Paid time off", "20 days plus 10 public holidays"], ["Employment", "At will"]],
             "Antwerp": [["Gross salary", f"EUR {local:,.0f} per month, 13.92 months per year"],
                         ["Benefits", "Meal vouchers, hospitalisation insurance, group pension, company laptop"],
                         ["Holidays", "20 statutory days plus 12 ADV days"],
                         ["Contract", "Permanent (onbepaalde duur), joint committee 200"]],
             "Nairobi": [["Basic salary", f"KES {local:,.0f} per month"],
                         ["Benefits", "Medical cover (staff and family), NSSF, SHIF and Housing Levy contributions"],
                         ["Annual leave", "21 working days"], ["Probation", "6 months"]]}[e["office"]]
    d = new_doc(f"Offer of employment - {e['name']}", f"{CO} | {e['office']} | {m.d0 - dt.timedelta(days=21):%d %B %Y}")
    d.add_paragraph(f"Dear {e['name'].split()[0]},")
    d.add_paragraph(f"We are pleased to offer you the position of {e['role']} in our {e['dept']} team in "
                    f"{e['office']}, starting on {m.d0:%d %B %Y}. You will report to "
                    f"{mgr['name'] if mgr else 'the Chief Executive Officer'}.")
    doc_table(d, ["Item", "Terms"], terms)
    save_doc(m.sink, f"{base}/01 Contract & Onboarding/Offer letter.docx", d)
    d = new_doc(f"Employment contract - {e['name']}", f"Employee {e['id']} | governed by the law of {country}")
    for h, t in [("1. Position", f"{e['role']} ({e['dept']}), based in {e['office']} with hybrid working."),
                 ("2. Start date", f"{m.d0:%d %B %Y}."),
                 ("3. Customer data", "Customer project data is confidential and accessed only for support with the "
                                      "customer's permission, logged in the audit trail."),
                 ("4. Site visits", "When visiting construction sites the employee follows the site induction and "
                                    "wears the required PPE."),
                 ("5. Intellectual property", "Work product created in employment belongs to the company."),
                 ("6. Termination", {"Denver": "Employment is at will.",
                                     "Antwerp": "Notice periods follow the Belgian Employment Contracts Act.",
                                     "Nairobi": "Notice of one month, or as set out in the Employment Act 2007."}[e["office"]])]:
        d.add_heading(h, 1)
        d.add_paragraph(t)
    doc_table(d, ["Signed for the company", "Employee"], [[m.w.staff[0]["name"], e["name"]]])
    save_doc(m.sink, f"{base}/01 Contract & Onboarding/Employment contract.docx", d)
    items = ["SSO account and MFA enrolled", f"Mailbox {e['email']}", "Laptop issued, disk encrypted, MDM enrolled",
             "Security awareness and privacy training assigned", "Access from role template only"]
    if e["dept"] == "Engineering":
        items += ["Source code access", "Staging environment access", "Production access: none (just-in-time only)"]
    if e["dept"] in ("Implementation", "Customer Success"):
        items += ["Support tool access", "Customer workspace access via audited support mode", "PPE kit for site visits"]
    doc_table(d := new_doc(f"IT onboarding checklist - {e['name']}"), ["Step", "Done by", "Date"],
              [[x, "IT", (m.d0 + dt.timedelta(days=i % 3)).isoformat()] for i, x in enumerate(items)])
    save_doc(m.sink, f"{base}/01 Contract & Onboarding/IT onboarding checklist.docx", d)


def leaver_docs(m, e):
    region, country, cur, mult, tax = OFFICES[e["office"]]
    base = S.person_dir(m.F, e)
    pay = m.w.pay(e, m.ym)
    months = months_between(e["hired"], m.ym)
    last = m.d0 - dt.timedelta(days=1)
    leave_days = random.Random(e["id"]).randint(0, 12)
    severance = {"Denver": pay * .5 * (months // 12) / 4 if e["leave_reason"] == "Laid off" else 0,
                 "Antwerp": 0.0,  # notice is worked or paid as indemnity, below
                 "Nairobi": pay * 15 / 30 * (months // 12) if e["leave_reason"] == "Laid off" else 0}[e["office"]]
    notice_pay = pay * min(3, 1 + months // 36) if e["office"] == "Antwerp" and e["leave_reason"] == "Laid off" else 0
    d = new_doc(f"Confirmation of end of employment - {e['name']}", f"{CO} | {last:%d %B %Y}")
    d.add_paragraph(f"This confirms that your employment as {e['role']} ends on {last:%d %B %Y} "
                    f"({e['leave_reason'].lower()}). Your final pay is set out in the attached statement.")
    save_doc(m.sink, f"{base}/07 Exit/Exit letter.docx", d)
    wb = new_book()
    ws = add_sheet(wb, "Final pay", ["Item", "Value"], [
        ["Employee", f"{e['id']} {e['name']}"], ["Office", e["office"]], ["Hired", ym_s(e["hired"])],
        ["Last day", last.isoformat()], ["Months of service", months], ["Monthly pay USD", pay],
        ["Unused leave days", leave_days], ["Leave payout USD", r2(pay / 21.7 * leave_days)],
        ["Severance USD", r2(severance)], ["Notice indemnity USD", r2(notice_pay)]])
    ws["A12"], ws["B12"] = "Total payable USD", "=B9+B10+B11"
    save_book(m.sink, f"{base}/07 Exit/Final pay statement.xlsx", wb, "Final pay", BANNER)
    d = new_doc(f"IT offboarding checklist - {e['name']}")
    doc_table(d, ["Step", "Status"], [[x, "Done"] for x in [
        "SSO account disabled at 17:00 on last day", "Sessions and API tokens revoked", "MFA devices removed",
        "Laptop returned and wiped", "Customer workspace support access removed", "Shared vault entries rotated",
        "Mailbox delegated to manager for 90 days"]])
    save_doc(m.sink, f"{base}/07 Exit/IT offboarding checklist.docx", d)


def snapshots(w, ym, sink):
    rows = [[c["code"], c["name"], c["kind"], c["region"], c["city"], c["country"], c["currency"], c["residency"],
             ym_s(c["since"]), w.term(c, ym)[3], w.term(c, ym)[1], ", ".join(w.term(c, ym)[2]),
             w.annual_price(c, ym) if not (c["end"] and c["end"] <= ym) else 0.0,
             "Churned" if c["end"] and c["end"] <= ym else "Active", c["contact"], f"pm@{c['domain']}"]
            for c in w.customers if c["since"] <= ym]
    wb = new_book()
    add_sheet(wb, "Customers", ["Code", "Customer", "Segment", "Region", "City", "Country", "Billing currency",
                                "Hosting region", "Since", "Tier", "Seats", "Modules", "ARR USD", "Status", "Contact",
                                "Email"], rows, {"Customer": 32, "Segment": 28, "Modules": 36, "Email": 34})
    projs = [[p["code"], p["name"], w.customers[p["cust"]]["name"], p["type"], p["region"], p["city"], p["form"],
              p["value"], ym_s(p["start"]), p["months"], p["retention"], p["units"]]
             for p in w.projects if p["start"] <= ym]
    add_sheet(wb, "Projects on platform", ["Project", "Name", "Customer", "Type", "Region", "City", "Contract form",
                                           "Contract value USD", "Start", "Months", "Retention", "Units"], projs,
              {"Name": 40, "Customer": 32, "Contract form": 36})
    save_book(sink, f"{F['crm']}/Customer and project register (as of {ym_s(ym)}).xlsx", wb, "Register", BANNER)
    staff = [[e["id"], e["name"], e["email"], e["role"], e["level"], e["dept"], e["office"], e["manager"], ym_s(e["hired"]),
              ym_s(e["left"]) if e["left"] and e["left"] <= ym else "", w.pay(e, ym)] for e in w.staff if e["hired"] <= ym]
    wb = new_book()
    add_sheet(wb, "Employees", ["Employee", "Name", "Email", "Role", "Level", "Department", "Office", "Manager",
                                "Hired", "Left", "Base USD/month"], staff, {"Name": 22, "Email": 36, "Role": 32})
    save_book(sink, f"{F['hr']}/Employee roster (as of {ym_s(ym)}).xlsx", wb, "Roster", BANNER)


def build(sink, st, max_months=24, scale=1.0, detail=1.0):
    from . import company_docs as D
    today = dt.date.today()
    last_full = ym_add((today.year, today.month), -1)
    done = tuple(st["done"]) if st.get("done") else None
    nxt = ym_add(done, 1) if done else START
    if nxt > last_full:
        return 0
    end = min(last_full, ym_add(nxt, max_months - 1))
    w = World(last_full, scale)
    ledger = st.setdefault("ledger", {})
    if not st.get("static"):
        D.static_docs(w, sink, sys.modules[__name__])
        st["static"] = True
    n, ym = 0, nxt
    while ym <= end and not sink.full():
        Month(w, ym, ledger, sink, detail).run()
        st["done"] = list(ym)
        n += 1
        ym = ym_add(ym, 1)
    if n:
        last = tuple(st["done"])
        snapshots(w, last, sink)
        if last[1] != 12:
            S.person_year(w, ledger, last[0], sink, sys.modules[__name__], final=False)
    return n
