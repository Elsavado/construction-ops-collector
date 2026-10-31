# construction-ops-collector

GitHub Actions collector of operational research data for a **construction software company** (planning and
scheduling, estimating and cost control, field/site management, handover and facilities, CAD/BIM), across every
field such a company works in: projects, cost, safety, CAD and BIM models, accounting, legal and contracts, HR,
software engineering, sales and support, security, SOPs, courses and training. Files go straight from the runner to
Google Drive with rclone (very large files stream directly from the source to Drive).

Everything is filed by topic under `Construction Operations Research/Public Data/`:

| Folder | Main sources |
|---|---|
| 01 Planning & Scheduling | schedule datasets, GAO schedule guide, MPXJ (P6 / MS Project formats), project-management tools |
| 02 Estimating & Cost Control | construction cost and price indices (US Census, Eurostat), GAO cost guide, cost datasets |
| 03 Site Operations, Safety & Quality | OSHA injury, severe-injury and fatality data, Eurostat accidents, site imagery, defects, materials |
| 04 Handover, Facilities & Asset Management | building energy, HVAC, maintenance and facility datasets |
| 05 CAD, BIM & 3D Models | 3D models by format (STL, OBJ, FBX, 3DS, Blender, glTF, STEP, IFC, DWG/DXF, Revit), BIM sample models, CAD part libraries, Objaverse objects by category, Poly Haven, ModelNet, Fusion 360 Gallery, ABC CAD dataset, CAD/BIM software docs |
| 06 Accounting & Finance | SEC Financial Statement Data Sets; filings of listed construction-software, contractor, homebuilder and materials companies |
| 07 Legal, Contracts & Compliance | construction contracts filed as SEC exhibits (25 types incl. AIA, design-build, EPC, subcontracts), eCFR titles (OSHA, FAR, ...), Federal Claims case law, CUAD |
| 08 HR & Workforce | O*NET occupations, construction employment, hours and wages |
| 09 Software Engineering & Cloud · 10 Sales, Marketing & Customer Success · 11 Security & Data Protection | docs (mobile/offline, web, cloud), datasets by topic |
| 12 SOPs, Manuals & Specifications | OSHA / NIOSH / USACE / UK HSE safety manuals, UFC criteria and UFGS specifications, GSA, FHWA, FTA, state DOT construction manuals, UK Construction Playbook, buildingSMART |
| 13 Courses & Training | complete MIT OpenCourseWare course packages (civil engineering, architecture, planning, management) |
| 14 Books & Knowledge Library | open-access books, Wikipedia articles as DOCX, IFC / BCF / IDS / bSDD standards, OWASP |
| 15 GitHub Repositories · 16 Jupyter Notebooks · 17 Software & Apps | licensed repos, notebooks, open-source CAD/BIM/PM/ERP app releases |
| 18 Q&A Archives | Stack Exchange dumps: Engineering, Home Improvement, GIS, Blender, 3D Printing, Project Management, Stack Overflow, ... |
| 19 Videos & Talks | openly licensed CAD, AutoCAD, Revit/BIM, 3D modelling, construction and safety videos (Internet Archive) |
| 20 Construction Industry & Markets | US construction spending, housing starts, building permits; Eurostat production, permits, confidence |

English content only. Only openly licensed or public-domain material is collected; each folder's source and licence
are recorded in `_state`.

## Running

- Secret `RCLONE_CONF`: rclone.conf with the Google Drive remote named `[pax]`. Optional: `KAGGLE_API_TOKEN`, `HF_TOKEN`.
- Variable `LIVE=true` turns on uploads (otherwise dry runs).
- Two jobs every 6 hours: `public` (data, documents, courses) and `models` (3D / CAD / BIM). Each source gets a
  fair share of the run; state lives on Drive in `_state/`.
