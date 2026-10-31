"""Static documents of the fictional company: policies (ISO 27001 / SOC 2 aligned), standard operating procedures
for every department, customer playbooks, templates, job descriptions, README and data dictionary."""
import random

from .common import add_sheet, new_book, save_book

POLICIES = {
    "Information Security Policy (ISO 27001)": ["Scope and objectives", "Roles and responsibilities", "Risk management",
                                                "Access control", "Cryptography", "Secure development", "Logging and monitoring",
                                                "Supplier security", "Incident management", "Business continuity",
                                                "Compliance and audit"],
    "Acceptable Use Policy": ["Company devices", "Personal devices", "Email and chat", "Customer data", "Prohibited use"],
    "Access Control Policy": ["Least privilege", "Role templates", "Just-in-time production access", "Quarterly reviews",
                              "Leavers"],
    "Data Classification and Handling": ["Public", "Internal", "Confidential", "Customer project data", "Retention"],
    "Data Residency Policy": ["Hosting regions (Americas, Europe, Africa)", "Region selection at contract",
                              "Support access across regions", "Backups stay in region", "Sub-processor locations"],
    "Privacy Policy (GDPR, UK GDPR, Kenya DPA, US state laws)": ["Data we process", "Lawful basis", "Data subject rights",
                                                                "International transfers", "Retention", "Contact and DPO"],
    "Data Retention and Deletion Policy": ["Customer data after termination", "Backups", "Logs", "Finance records",
                                           "HR records", "Deletion certificates"],
    "Business Continuity and Disaster Recovery Policy": ["Recovery objectives (RPO 15 min, RTO 4 h)", "Region failover",
                                                         "Offline-first mobile continuity", "Testing", "Communication"],
    "Vendor and Sub-processor Management Policy": ["Due diligence", "Contract clauses", "Annual review", "Offboarding"],
    "Change Management Policy": ["Standard, normal and emergency changes", "Peer review", "Release windows per region",
                                 "Rollback"],
    "Secure Software Development Policy": ["Threat modelling", "Code review", "Dependency scanning", "Secrets handling",
                                           "Penetration testing"],
    "Anti-Bribery and Corruption Policy": ["Gifts and hospitality", "Public officials and tenders", "Agents",
                                           "Facilitation payments", "Reporting"],
    "Code of Conduct": ["Respect", "Conflicts of interest", "Fair competition", "Speaking up", "Discipline"],
    "Expense and Travel Policy": ["What we reimburse", "Site visits and PPE", "Approval", "Receipts", "Per diems by office"],
    "Remote and Hybrid Work Policy": ["Eligibility", "Equipment", "Security at home", "Working hours across time zones"],
    "Health and Safety Policy (office and site visits)": ["Site inductions", "PPE", "Lone working", "Driving",
                                                          "Incident reporting"],
    "Information Management Policy (ISO 19650 for customer projects)": ["Common data environment states",
                                                                        "Container naming", "Status codes",
                                                                        "Revision control", "Audit trail"],
}
POLICY_TEXT = ["{co} applies this to all employees, contractors and systems in scope.",
               "The policy owner reviews it every year and after any material change.",
               "Evidence is kept for at least three years and is available to auditors and customers under NDA.",
               "Exceptions need written approval from the policy owner and expire after twelve months.",
               "Training on this topic is part of onboarding and is refreshed every year.",
               "Breaches are reported to the policy owner within one business day.",
               "Controls in this policy map to ISO/IEC 27001:2022 Annex A and the SOC 2 Trust Services Criteria."]

# title: (owner role, purpose, [(section, [steps])], records, kpis)
SOPS = {
    # ---- sales & customer lifecycle
    "SOP-SAL-01 Lead qualification": ("Chief Revenue Officer", "Qualify inbound and outbound leads consistently.", [
        ("Procedure", ["Log every lead in the CRM within one business day with source and region.",
                       "Score fit: segment, annual construction volume, number of live projects, current tools.",
                       "Book a discovery call within five days for scores above 60.",
                       "Record pains in the customer's words (e.g. late pay applications, lost site photos).",
                       "Hand qualified leads to an Account Executive with notes."])],
        "CRM lead record, discovery notes", "Lead response time; qualified-to-opportunity rate"),
    "SOP-SAL-02 Pilot on a live project": ("Solutions Engineer", "Run a time-boxed pilot that proves value on site.", [
        ("Preparation", ["Agree success criteria with the customer sponsor (e.g. daily logs submitted on 90% of days).",
                         "Choose one live project and one site team; confirm connectivity and devices.",
                         "Create a pilot workspace in the customer's hosting region."]),
        ("Execution", ["Kick-off on site; train the superintendent and two foremen.",
                       "Weekly check-in call; track usage in the pilot dashboard.",
                       "Fix blockers within 48 hours; escalate product gaps to Product."]),
        ("Close", ["Present results against the criteria.", "Convert to an order form or close the pilot and delete data."])],
        "Pilot plan, weekly usage report, close-out deck", "Pilot conversion rate; pilot length"),
    "SOP-SAL-03 Quote, order form and approvals": ("Finance Manager", "Price and approve deals within policy.", [
        ("Procedure", ["Build the quote from the price book (modules x seats x tier).",
                       "Discounts above 15% need CRO approval; above 25% need CEO and CFO approval.",
                       "Confirm billing currency, VAT treatment and hosting region.",
                       "Legal reviews non-standard terms (liability, data residency, audit rights).",
                       "Send the order form for e-signature; attach DPA and SLA."])],
        "Quote, approval log, signed order form", "Average discount; approval cycle time"),
    "SOP-SAL-04 Public tender response": ("Regional General Manager Europe", "Respond to public procurement tenders.", [
        ("Procedure", ["Register the tender and deadline; run a bid/no-bid review within 3 days.",
                       "Assign a bid manager; build the compliance matrix from the tender documents.",
                       "Collect security, privacy and accessibility evidence (ISO 27001, SOC 2, WCAG).",
                       "Legal checks contract terms and anti-corruption requirements.",
                       "Submit through the portal at least 24 hours before the deadline; archive the submission."])],
        "Bid/no-bid record, compliance matrix, submission receipt", "Win rate; on-time submissions"),
    "SOP-CS-01 Customer onboarding": ("VP Customer Success", "Get every new customer live and adopting within 60 days.", [
        ("Week 0", ["Welcome email with workspace link in the customer's hosting region.",
                    "Assign implementation consultant and customer success manager.", "Kick-off call: goals, projects, users."]),
        ("Weeks 1-4", ["Configure templates, cost codes, approval workflows and roles.",
                       "Import schedules (XER/MPP) and drawing registers.", "Train admins, then site teams on site."]),
        ("Weeks 5-8", ["Go-live on the first project.", "Weekly adoption review (active users, daily logs, photos).",
                       "Hand over from implementation to customer success with a success plan."])],
        "Onboarding checklist, success plan", "Time to first value; 60-day activation"),
    "SOP-CS-02 Quarterly business review": ("Customer Success Manager", "Review value and plan the next quarter.", [
        ("Procedure", ["Prepare usage, support and project metrics from the customer dashboard.",
                       "Agree outcomes reached and new goals.", "Identify expansion (modules, seats, projects).",
                       "Record risks in the health score and the account plan."])],
        "QBR deck, meeting notes, updated health score", "QBR coverage; health score trend"),
    "SOP-CS-03 Renewal management": ("Customer Success Manager", "Renew every healthy customer on time.", [
        ("Procedure", ["120 days before renewal: health review and risk flag.",
                       "90 days: renewal proposal with any price change.", "60 days: contract notice deadline check.",
                       "30 days: send order form; finance prepares invoice.",
                       "On churn: run the exit survey and start SOP-CS-05."])],
        "Renewal tracker, order form", "Gross revenue retention; net revenue retention"),
    "SOP-CS-04 Customer escalation": ("VP Customer Success", "Handle escalations quickly and visibly.", [
        ("Procedure", ["Log the escalation with impact on live projects (e.g. pay application deadline).",
                       "Name an owner within one hour; daily updates to the customer.",
                       "Engage engineering via the incident or priority-bug process.",
                       "Close with a written summary and prevention actions."])],
        "Escalation log", "Time to owner; escalations per 100 customers"),
    "SOP-CS-05 Customer offboarding and data return": ("Compliance & Privacy Officer",
                                                       "Return and delete customer data at contract end.", [
        ("Procedure", ["Confirm termination date and data export needs.",
                       "Provide full export: CSV, XER, IFC, PDF document packages, photo archive.",
                       "Keep read-only access for 60 days.", "Delete production data within 30 days after that; backups "
                                                             "expire within 35 days.",
                       "Issue a deletion certificate signed by the Compliance & Privacy Officer."])],
        "Export log, deletion certificate", "Exports completed on time; deletion SLA"),
    # ---- implementation
    "SOP-IMP-01 Primavera P6 schedule import": ("Scheduling Specialist (P6)", "Import P6 schedules without losing logic.", [
        ("Procedure", ["Ask the customer for an XER export including calendars, codes and resources.",
                       "Check the XER: open ends, negative lags, constraints, out-of-sequence progress.",
                       "Import into a staging project; compare activity count, finish date and critical path to P6.",
                       "Map activity codes to platform WBS and look-ahead filters.",
                       "Sign off with the customer planner; publish to the live project."])],
        "Import validation report", "Imports matching P6 finish date"),
    "SOP-IMP-02 Cost code and budget set-up": ("Implementation Consultant", "Set up budgets that match how the customer reports.", [
        ("Procedure", ["Choose the structure: CSI MasterFormat (US), NRM / elemental (UK, EU), or the customer's own.",
                       "Load the baseline budget and lock it; approved changes go through change orders only.",
                       "Configure retention rules per contract form (e.g. 5% until practical completion).",
                       "Set currency per project; lock FX rates for multi-currency budgets.",
                       "Test a pay application end to end before go-live."])],
        "Budget import file, test pay application", "Budget variance at go-live"),
    "SOP-IMP-03 Field rollout and offline training": ("Customer Trainer", "Make site teams confident with the mobile app.", [
        ("Procedure", ["Check device list, OS versions and site connectivity.",
                       "Train on site: daily log, photos on drawings, inspections, punch list.",
                       "Practise offline: airplane mode, capture, reconnect, review sync status and conflicts.",
                       "Nominate a site champion; schedule a two-week follow-up."])],
        "Training register, follow-up notes", "Daily log completion; offline sync success"),
    "SOP-IMP-04 BIM model and BCF set-up": ("Data Migration & BIM Specialist", "Federate models and issues for coordination.", [
        ("Procedure", ["Agree the BIM execution plan (BEP) and ISO 19650 naming with the customer.",
                       "Upload IFC models per discipline; check schema, georeferencing and storeys.",
                       "Run a first clash review; publish issues as BCF topics assigned by discipline.",
                       "Link site photos and punch items to model elements.",
                       "Set the weekly coordination meeting cadence."])],
        "BEP, model register, BCF issue log", "Open clashes trend; issue response time"),
    "SOP-IMP-05 ERP integration": ("Implementation Consultant", "Sync commitments and actuals with the customer's ERP.", [
        ("Procedure", ["Map vendors, cost codes, jobs and tax codes.", "Configure the nightly sync through the API.",
                       "Reconcile a closed month: platform vs ERP within 0.5%.",
                       "Hand over the monitoring dashboard and error alerts."])],
        "Mapping sheet, reconciliation report", "Sync failures per month"),
    # ---- product & engineering
    "SOP-ENG-01 Code review and merge": ("Engineering Manager", "Keep the main branch releasable.", [
        ("Procedure", ["Open a pull request linked to its issue.", "One reviewer; two for auth, billing, sync and "
                                                                   "data-residency code.",
                       "CI must pass: unit, integration, security and licence scans.", "Squash-merge; delete the branch."])],
        "Pull request history", "Review time; change failure rate"),
    "SOP-ENG-02 Release to production (per region)": ("Site Reliability Engineer", "Release safely in each region.", [
        ("Procedure", ["Cut the release on Tuesday; run regression and load tests.",
                       "Deploy to Africa region canary first (lowest traffic), then Europe, then Americas.",
                       "Watch error rate, latency and sync queue depth for 60 minutes per stage.",
                       "Mobile releases: staged rollout 5% / 25% / 100% with crash-rate gates.",
                       "Roll back in one command if SLOs breach."])],
        "Release record, deployment log", "Deployment frequency; rollback rate"),
    "SOP-ENG-03 On-call and incident command": ("Site Reliability Engineer", "Restore service fast and learn from it.", [
        ("Procedure", ["Acknowledge pages within 5 minutes.", "SEV1/SEV2: open the incident channel and a video bridge.",
                       "Assign incident commander, communicator and scribe.",
                       "Update the status page every 30 minutes, per affected region.",
                       "Postmortem within 5 business days with owners and due dates."])],
        "Incident record, postmortem", "Time to acknowledge; time to restore"),
    "SOP-ENG-04 Offline sync conflict review": ("Engineering Manager", "Make sure no site data is lost when devices reconnect.", [
        ("Procedure", ["Daily report of manual-review conflicts per customer.",
                       "Engineer on duty checks each conflict; merges keep both versions in history.",
                       "Contact the site user if a decision is needed; never discard data silently.",
                       "Weekly trend review; file bugs for repeating patterns."])],
        "Conflict review log", "Conflicts per 1,000 offline edits"),
    "SOP-ENG-05 Data residency verification": ("Data Engineer", "Prove customer data stays in its region.", [
        ("Procedure", ["Monthly automated scan of storage, databases, backups and logs by region tag.",
                       "Investigate any object outside its tenant's region the same day.",
                       "Check sub-processor locations against the published list.",
                       "Publish the attestation to the trust portal."])],
        "Residency scan report", "Residency exceptions (target zero)"),
    "SOP-ENG-06 Backup and restore test": ("Site Reliability Engineer", "Know that restores work.", [
        ("Procedure", ["Point-in-time backups every 15 minutes; daily snapshots kept 35 days, in region.",
                       "Weekly restore of a random tenant to an isolated environment; verify record counts.",
                       "Quarterly full region failover drill.", "Record results and fix failures within 5 days."])],
        "Restore test log", "Restore success; measured RTO and RPO"),
    "SOP-ENG-07 Customer API and webhooks support": ("Solutions Engineer", "Help customers integrate reliably.", [
        ("Procedure", ["Issue API keys per integration with least scopes.", "Share the sandbox and the API changelog.",
                       "Monitor webhook failures; notify the customer after 50 consecutive failures.",
                       "Deprecate endpoints with 6 months' notice."])],
        "API key register", "Webhook delivery success"),
    # ---- security & compliance
    "SOP-SEC-01 Quarterly access review": ("Security Engineer", "Remove access nobody needs.", [
        ("Procedure", ["Export access to production, cloud console, billing, support tool and source code.",
                       "Managers confirm each grant within 10 days.", "Remove unconfirmed access within 5 days.",
                       "Store the evidence for SOC 2 and ISO 27001 audits."])],
        "Access review workbook", "Review completion; stale accounts removed"),
    "SOP-SEC-02 Vulnerability management": ("Security Engineer", "Fix vulnerabilities on time.", [
        ("Procedure", ["Scan containers, dependencies, cloud configuration and web apps weekly.",
                       "Fix critical in 7 days, high in 30, medium in 90.", "Track exceptions with owner and expiry.",
                       "Annual third-party penetration test of web, mobile and API."])],
        "Vulnerability register, pen test report", "SLA compliance by severity"),
    "SOP-SEC-03 Security questionnaire response": ("Compliance & Privacy Officer", "Answer customer security reviews quickly.", [
        ("Procedure", ["Start from the approved answer library (SIG Lite / CAIQ style).",
                       "Share SOC 2 report and ISO certificate under NDA through the trust portal.",
                       "Engineering confirms any new technical answers.", "Return within 10 business days; log the review."])],
        "Questionnaire log", "Turnaround time"),
    "SOP-SEC-04 Personal data breach response": ("Compliance & Privacy Officer", "Meet legal notice deadlines.", [
        ("Procedure", ["Assess within 24 hours: what data, which customers, which regions.",
                       "Notify affected customers (controllers) within 48 hours.",
                       "Support customers with regulator notices: GDPR 72 hours, Kenya ODPC 72 hours, US state rules.",
                       "Record in the breach register even when not notifiable."])],
        "Breach register", "Notices within deadline"),
    "SOP-PRIV-01 Data subject request handling": ("Compliance & Privacy Officer", "Answer DSARs for our own data.", [
        ("Procedure", ["Verify identity.", "For customer project data, route the request to the customer (controller).",
                       "For our own data (staff, prospects), export or delete within 30 days.", "Log the outcome."])],
        "DSAR log", "Requests closed within 30 days"),
    # ---- support
    "SOP-SUP-01 Ticket triage and SLAs": ("VP Customer Success", "Respond and resolve on time.", [
        ("Procedure", ["Classify: urgent (site blocked), high, normal, low.",
                       "First response: urgent 1 h, high 4 h, normal 1 business day.",
                       "Use support mode to view the customer workspace; it is logged and visible to admins.",
                       "Escalate bugs with reproduction steps, device and sync status.", "Close with a CSAT survey."])],
        "Ticket history", "First response time; CSAT"),
    "SOP-SUP-02 Pay application deadline support": ("Support Specialist", "Never let a customer miss a payment deadline.", [
        ("Procedure", ["Tickets mentioning pay applications, valuations or certificates go to urgent.",
                       "Check retention settings, change orders and previous applications.",
                       "If a product bug blocks submission, provide an export (XLSX/PDF) the same day.",
                       "Follow up after the payment date."])],
        "Ticket history", "Deadline misses (target zero)"),
    # ---- finance
    "SOP-FIN-01 Month-end close": ("Finance Manager", "Close the books in five working days.", [
        ("Day 1", ["Recognise subscription revenue from the deferred revenue schedule.",
                   "Invoice implementation services from approved timesheets.", "Accrue unbilled vendor costs."]),
        ("Day 2-3", ["Reconcile bank accounts in USD, EUR and KES.", "Reconcile AR and AP sub-ledgers.",
                     "Post payroll for Denver, Antwerp and Nairobi.", "Revalue foreign currency balances."]),
        ("Day 4-5", ["Review trial balance; investigate variances above 10%.", "Capitalise eligible development costs.",
                     "Prepare management accounts and the KPI pack."])],
        "Close checklist, reconciliations, trial balance", "Days to close"),
    "SOP-FIN-02 Billing and collections": ("Accountant", "Bill correctly and collect on time.", [
        ("Procedure", ["Subscriptions invoiced annually in advance on the start or renewal date.",
                       "VAT: charge local VAT in Belgium and Africa; EU B2B cross-border reverse charge; US no sales tax on "
                       "current nexus.", "Reminders at 7, 21 and 45 days overdue; CSM informed at 21 days.",
                       "Suspend non-payers only after CFO approval and 10 days' notice.",
                       "Write off after 240 days with CFO approval."])],
        "Invoice register, dunning log", "DSO; bad debt %"),
    "SOP-FIN-03 Revenue recognition": ("Chief Financial Officer", "Recognise revenue in line with IFRS 15 / ASC 606.", [
        ("Procedure", ["Subscriptions: ratably over the term from deferred revenue.",
                       "Implementation fixed fee: over time by milestones; T&M: as hours are delivered.",
                       "Training: when delivered.", "Review contracts with non-standard terms each quarter."])],
        "Revenue schedule", "Audit adjustments"),
    "SOP-FIN-04 Vendor onboarding and payment": ("Finance Manager", "Pay the right vendors once.", [
        ("Procedure", ["Collect bank details on letterhead; verify by call-back.",
                       "Security review for vendors that process data (sub-processors).",
                       "Three-way match for purchase orders above USD 5,000.", "Payment runs weekly, dual approval."])],
        "Vendor master, approvals", "Duplicate payments (target zero)"),
    "SOP-FIN-05 Expense claims": ("Accountant", "Reimburse staff quickly and correctly.", [
        ("Procedure", ["Submit within 30 days with receipts.", "Manager approves; finance checks policy.",
                       "Reimburse in the employee's pay currency with the next payment run."])],
        "Expense register", "Days to reimburse"),
    # ---- people
    "SOP-HR-01 Hiring": ("Head of People", "Hire fairly and fast.", [
        ("Procedure", ["Approved headcount and job description before posting.", "Structured interviews with scorecards.",
                       "Work sample for engineering and implementation roles.", "References and right-to-work checks per "
                                                                                "country.", "Offer within 48 hours of the "
                                                                                            "final interview."])],
        "Requisition, scorecards, offer", "Time to hire; offer acceptance"),
    "SOP-HR-02 Employee onboarding": ("People Partner", "Make new starters productive in 30 days.", [
        ("Procedure", ["Equipment shipped one week before start.", "Accounts from the role template.",
                       "Buddy and 30/60/90-day goals.", "Security, privacy and site-safety training in week one.",
                       "Customer site visit within the first month for customer-facing roles."])],
        "Onboarding checklist", "30-day completion"),
    "SOP-HR-03 Leaver process": ("People Partner", "Exit people respectfully and securely.", [
        ("Procedure", ["Confirm last day and reason.", "Final pay per country rules (US, Belgium, Kenya).",
                       "IT offboarding at 17:00 on the last day.", "Exit interview; update the roster."])],
        "Exit checklist, final pay statement", "Offboarding on time"),
    "SOP-HR-04 Performance review": ("Head of People", "Give clear feedback twice a year.", [
        ("Procedure", ["Self-review, manager review and peer input.", "Calibrate ratings by department.",
                       "Agree development goals and training.", "Link pay changes to the annual review only."])],
        "Review records", "Completion rate"),
    # ---- facilities & travel
    "SOP-OPS-01 Customer site visit safety": ("Head of People", "Keep staff safe on construction sites.", [
        ("Procedure", ["Book the visit with the customer site manager.", "Complete the site induction; sign in and out.",
                       "Wear PPE: hard hat, boots, high-visibility vest, eye protection.",
                       "Never enter excavations, scaffolds or crane zones without escort.",
                       "Report any incident or near miss within 24 hours."])],
        "Visit log, induction record", "Incidents during visits (target zero)"),
}

PLAYBOOKS = {
    "Customer playbook - Daily logs and site diaries": ["Fill the log before leaving site; offline is fine.",
                                                        "Record weather, labour by trade, equipment, work done, delays.",
                                                        "Attach photos and pin them to the drawing sheet.",
                                                        "Use delays to support extension-of-time claims."],
    "Customer playbook - Pay applications and retention": ["Lock the schedule of values before the first application.",
                                                           "Approved change orders flow into the contract sum.",
                                                           "Retention follows the contract (e.g. 5% until completion, "
                                                           "half released at practical completion).",
                                                           "Export as AIA G702/G703 (US) or interim certificate (NEC/FIDIC)."],
    "Customer playbook - Inspections, ITPs and punch lists": ["Build inspection and test plans from templates.",
                                                              "Hold points block the next activity until signed.",
                                                              "Failed inspections raise a non-conformance report.",
                                                              "Punch items need a photo before and after."],
    "Customer playbook - Handover and closeout": ["Start the O&M register at 70% progress.",
                                                  "Collect warranties and test certificates per system.",
                                                  "Asset register in COBie style for the owner's CAFM.",
                                                  "Compile the handover package as one PDF plus native files."],
    "Customer playbook - Schedules and look-aheads": ["Import from P6 or MS Project; keep logic intact.",
                                                      "Update progress weekly from site; planner approves.",
                                                      "Three-week look-ahead for foremen on mobile.",
                                                      "Watch total float on the critical path."],
}

TEMPLATES = {
    "BIM Execution Plan (BEP) template": ["Project information", "BIM goals and uses", "Roles and responsibilities",
                                          "Information delivery milestones (TIDP/MIDP)", "Naming (ISO 19650)",
                                          "Model federation and clash detection", "Level of information need",
                                          "Common data environment workflow", "Model quality checks", "Handover (COBie)"],
    "Inspection and Test Plan (ITP) template": ["Activity", "Specification clause", "Inspection type (hold / witness / "
                                                                                    "review)", "Acceptance criteria",
                                                "Records", "Responsible party"],
    "Business Continuity Plan": ["Critical services", "Recovery objectives", "Region failover runbook",
                                 "Communication tree", "Office outage (Denver, Antwerp, Nairobi)", "Test schedule"],
    "Incident Response Plan": ["Severity levels", "Roles", "Communication", "Forensics and evidence", "Regulator and "
                                                                                                      "customer notices",
                               "Post-incident review"],
}


def static_docs(w, sink, C):
    r = random.Random(C.SEED + 5)
    F = C.F
    for i, (title, secs) in enumerate(POLICIES.items(), 1):
        d = C.new_doc(title, f"{C.CO} | Document QS-POL-{i:02d} | Version {r.randint(1, 5)}.{r.randint(0, 9)}")
        for j, s in enumerate(secs, 1):
            d.add_heading(f"{j}. {s}", 1)
            for t in r.sample(POLICY_TEXT, 3):
                d.add_paragraph(t.format(co=C.CO))
        C.save_doc(sink, f"{F['pol']}/Policies/{title}.docx", d)
    for title, (owner, purpose, sections, records, kpi) in SOPS.items():
        dept = title.split("-")[1]
        d = C.new_doc(title, f"Standard Operating Procedure | Version {r.randint(1, 4)}.{r.randint(0, 9)}")
        C.doc_table(d, ["Owner", "Review", "Applies to"], [[owner, "Annual", C.SOP_SCOPE if dept in ("ENG", "SEC") else
                                                             "All offices: Denver, Antwerp, Nairobi"]])
        d.add_heading("Purpose", 1)
        d.add_paragraph(purpose)
        d.add_heading("Roles (RACI)", 1)
        C.doc_table(d, ["Responsible", "Accountable", "Consulted", "Informed"],
                    [[owner, C.HEADS.get(C.ROLES.get(owner, ("Executive",))[0], "Chief Executive Officer"),
                      r.choice(["Legal Counsel", "Security Engineer", "Finance Manager", "Customer Success Manager"]),
                      r.choice(["Leadership team", "Customer", "All staff in scope"])]])
        for h, steps in sections:
            d.add_heading(h, 1)
            for k, s in enumerate(steps, 1):
                d.add_paragraph(f"{k}. {s}")
        d.add_heading("Records", 1)
        d.add_paragraph(records)
        d.add_heading("Measures", 1)
        d.add_paragraph(kpi)
        C.save_doc(sink, f"{F['pol']}/SOPs/{dept}/{title}.docx", d)
    wb = new_book()
    add_sheet(wb, "SOP register", ["SOP", "Owner", "Purpose", "Records", "Measures"],
              [[t, o, p, rec, k] for t, (o, p, _, rec, k) in SOPS.items()],
              {"SOP": 44, "Owner": 30, "Purpose": 56, "Records": 40, "Measures": 40})
    save_book(sink, f"{F['pol']}/SOPs/SOP register.xlsx", wb, "SOP register", C.BANNER)
    for title, points in PLAYBOOKS.items():
        d = C.new_doc(title, f"{C.CO} customer education")
        for x in points:
            C.bullet(d, x)
        C.save_doc(sink, f"{F['pol']}/Customer playbooks/{title}.docx", d)
    for title, secs in TEMPLATES.items():
        d = C.new_doc(title, "Template")
        for j, s in enumerate(secs, 1):
            d.add_heading(f"{j}. {s}", 1)
            d.add_paragraph("[Complete for the project / organisation]")
        C.save_doc(sink, f"{F['pol']}/Templates/{title}.docx", d)
    risks = [[f"R{i + 1:03d}", t, r.choice(["Low", "Medium", "High"]), r.choice(["Low", "Medium", "High"]), o, m]
             for i, (t, o, m) in enumerate([
                 ("Region outage", "Site Reliability Engineer", "Multi-zone; offline mobile; failover drill"),
                 ("Customer data in wrong region", "Data Engineer", "Residency router; monthly scan"),
                 ("Ransomware", "Security Engineer", "Immutable backups; EDR; MFA"),
                 ("Key person dependency in P6 migration", "VP Customer Success", "Cross-training; runbooks"),
                 ("FX loss on KES and EUR revenue", "Chief Financial Officer", "Natural hedge with local payroll"),
                 ("Public tender anti-corruption breach", "Legal Counsel", "Policy, training, approvals"),
                 ("Mobile sync data loss", "Engineering Manager", "Conflict review SOP; history"),
                 ("Sub-processor breach", "Compliance & Privacy Officer", "Vendor reviews; DPAs"),
                 ("Construction market downturn", "Chief Executive Officer", "Diversify regions and segments"),
                 ("Accessibility non-compliance in tenders", "Product Manager", "WCAG 2.2 audits")])]
    wb = new_book()
    add_sheet(wb, "Risk register", ["Risk", "Description", "Likelihood", "Impact", "Owner", "Mitigation"], risks,
              {"Description": 40, "Owner": 30, "Mitigation": 44})
    vendors = [["Stratus Cloud", "Hosting (all regions)", "Yes", "SOC 2, ISO 27001", "Annual"],
               ["Mapline APIs", "Maps and geocoding", "Yes", "SOC 2", "Annual"],
               ["Inkwell Sign", "E-signature", "Yes", "ISO 27001", "Annual"],
               ["Parcelmail", "Transactional email", "Yes", "SOC 2", "Annual"],
               ["Scanlight OCR", "Document OCR", "Yes", "ISO 27001", "Annual"],
               ["Toolstack Software", "Internal tools", "No", "SOC 2", "Biennial"]]
    add_sheet(wb, "Sub-processors & vendors", ["Vendor", "Service", "Processes customer data", "Assurance", "Review"],
              vendors, {"Vendor": 22, "Service": 26})
    qa = [[q, a] for q, a in [
        ("Do you hold ISO/IEC 27001 certification?", "Yes, certified since 2020; certificate available in the trust portal."),
        ("Do you have a SOC 2 Type II report?", "Yes, annual, covering security, availability and confidentiality."),
        ("Where is customer data stored?", "In the hosting region chosen in the order form: Americas, Europe or Africa."),
        ("Is data encrypted?", "TLS 1.2+ in transit; AES-256 at rest; keys managed per region."),
        ("Do you support SSO?", "SAML 2.0 and OIDC; SCIM provisioning on Enterprise."),
        ("What are your RPO and RTO?", "RPO 15 minutes, RTO 4 hours; failover tested quarterly."),
        ("Can the mobile app work offline?", "Yes; data is encrypted on device and synced with conflict review."),
        ("Do you support open formats?", "IFC 2x3/4/4.3, BCF 2.1/3.0, XER, MPP import, CSV/XLSX/PDF exports."),
        ("How do you handle sub-processors?", "Listed publicly; 30 days' notice of changes; DPAs in place.")]]
    add_sheet(wb, "Security questionnaire answers", ["Question", "Approved answer"], qa, {"Question": 46, "Approved answer": 80})
    save_book(sink, f"{F['sec']}/Registers (risk, vendors, questionnaire library).xlsx", wb, "Registers", C.BANNER)
    for role, (dept, office, base, _) in C.ROLES.items():
        d = C.new_doc(f"Job description - {role}", f"Department: {dept} | Office: {office}")
        C.doc_table(d, ["Reports to", "Salary band (USD/year, Denver basis)"],
                    [[C.HEADS.get(dept, "Chief Executive Officer"), f"{base * 12 * .88:,.0f} - {base * 12 * 1.2:,.0f}"]])
        d.add_heading("What you will do", 1)
        for x in r.sample(["Work closely with contractors and site teams", "Keep customer project data safe and in region",
                           "Ship high-quality work in two-week sprints", "Write clear documentation",
                           "Visit live construction sites to learn how teams work", "Mentor teammates",
                           "Measure outcomes on real projects"], 4):
            C.bullet(d, x)
        C.save_doc(sink, f"{F['hr']}/Job descriptions/{role}.docx", d)
    d = C.new_doc(f"{C.CO} - dataset README", C.BANNER)
    d.add_paragraph("Synthetic, internally consistent records of a fictional construction software company with offices "
                    "in Denver, Antwerp and Nairobi: customers, subscriptions and renewals; contracts, order forms and "
                    "DPAs; implementation services; engineering, incidents and releases; platform usage and SLAs per "
                    "hosting region; sample customer project workspaces (P6-style XER schedules, cost reports, change "
                    "orders, pay applications with retention, daily logs, RFIs, inspections, punch lists, safety records, "
                    "photo registers on drawing coordinates, ISO 19650 registers, IFC models, DXF plans, handover "
                    "registers); support; security and compliance evidence; marketing; payroll in three countries and "
                    "per-person HR files; double-entry books whose trial balance balances every month; policies, SOPs, "
                    "playbooks and templates.")
    for v in F.values():
        C.bullet(d, v.split("/", 1)[1])
    C.save_doc(sink, f"{C.ROOT}/README.docx", d)
    wb = new_book()
    add_sheet(wb, "Chart of accounts", ["Account", "Name", "Type"], [[a, *v] for a, v in sorted(C.ACCOUNTS.items())],
              {"Name": 50})
    add_sheet(wb, "Price book", ["Module", "USD per user per year (2017 basis, +4%/year)"],
              [[k, v] for k, v in C.MODULES.items()] + [["Enterprise platform fee", C.TIERS["Enterprise"][1]]],
              {"Module": 30})
    add_sheet(wb, "Offices", ["Office", "Region", "Country", "Pay currency", "Pay index", "Employer tax rate"],
              [[k, *v] for k, v in C.OFFICES.items()])
    add_sheet(wb, "Notice", ["Notice"], [[C.BANNER], ["Domains use the reserved .example TLD."]], {"Notice": 110})
    save_book(sink, f"{C.ROOT}/Data dictionary.xlsx", wb, "Data dictionary", C.BANNER)
