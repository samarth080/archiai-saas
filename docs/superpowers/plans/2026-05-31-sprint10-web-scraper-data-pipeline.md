# Sprint 10: Web Scraper and Data Pipeline

## 1. Sprint Goal

Build a responsible, isolated data pipeline that collects public textual architectural-layout references and converts them into structured layout-learning records for future Sprint 11 generator improvements.

This sprint creates the data foundation only. It does not train a model, parse floor-plan images, or modify live layout generation.

## 2. Why This Data Matters

The current deterministic generator can place labelled room blocks, but future improvement needs a structured knowledge base grounded in public architectural guidance. The pipeline should help future rules answer:

- Which rooms commonly exist for a building type?
- Which room sizes and area ratios are typical?
- Which rooms should be adjacent or separated?
- How should public, private, service, and circulation zones relate?
- Where do corridors, stairs, doors, windows, balconies, utilities, and entries usually belong?
- Which high-level patterns recur across apartments, houses, offices, clinics, classrooms, retail spaces, studios, restaurants, and small industrial spaces?

The resulting dataset is intended for rule improvement and later model experimentation. It must preserve provenance so future consumers can distinguish reference material from inferred rules.

## 3. MVP Scope

- Register and manage permitted public reference sources.
- Store source metadata and robots.txt review timestamps.
- Check robots.txt before every scrape run.
- Fetch one safe public textual source at a time with polite headers.
- Prefer HTML text, headings, paragraphs, lists, and tables.
- Store raw text records with source URL, access timestamp, and run linkage.
- Normalize whitespace and extract deterministic metadata from raw text.
- Store structured layout patterns separately from raw records.
- Expose authenticated MVP APIs for source CRUD, scraper execution, run history, status, and pattern listing.
- Add a simple authenticated internal/dev frontend monitoring page, hidden from normal product navigation by default.
- Keep all scraper code isolated from project, design, and generator logic.

The data-pipeline UI is internal/admin/dev tooling. Normal users should not manage scraper sources or see it as a customer-facing product feature. For MVP internal testing, frontend visibility is explicitly gated with `VITE_SHOW_DEV_TOOLS=true`.

## 4. Explicitly Excluded Scope

- AI model training, fine-tuning, embeddings, or vector search.
- LLM-assisted extraction, classification, or summarization.
- Image download, image scraping, OCR, floor-plan image parsing, or drawing reconstruction.
- Copyrighted drawings, watermarked plans, paid plan catalogues, private plans, personal data, or social-media images.
- Large-scale crawling, recursive crawling, queue workers, distributed scraping, or scheduled jobs.
- Generator rule updates or live use of scraped records.
- Legal-compliance claims. Accessibility and egress references are informational source records only.
- Advanced admin analytics, source-quality scoring workflows, and approval queues.

## 5. Useful Data Types To Collect

### Building-Type References

Target:

- apartment
- house
- studio
- office
- retail/store
- clinic/small healthcare layout
- classroom/school layout
- cafe/restaurant
- warehouse/small industrial space
- mixed-use layout where publicly described

Collect:

- common room types
- typical room count ranges
- common zoning sequences
- total area ranges where available
- circulation and layout notes

### Room-Type References

Target room vocabulary:

- bedroom
- master bedroom
- guest room
- bathroom
- kitchen
- living room
- dining room
- study/office
- meeting room
- reception
- storage
- utility/laundry
- balcony
- terrace
- garage/parking
- corridor
- stairs
- open space
- waiting area
- classroom
- consultation room
- retail display area

Collect:

- typical usage
- required or optional status where stated
- public/private/service/circulation zone
- count ranges by building type

### Room Sizes And Ratios

Collect where explicitly available:

- area range in square metres
- width/depth range
- original value and unit when conversion is needed
- room-to-total-area ratio range
- corridor width, door width, and circulation guidance

### Adjacency And Separation

Positive patterns:

- kitchen near dining
- dining near living
- living near entry
- bathroom near bedrooms
- reception near entry
- waiting area near reception
- consultation rooms near waiting area
- classroom near corridor
- storage near service/work areas
- balcony connected to living room or bedroom
- stairs near circulation/common zones

Negative patterns:

- bedrooms away from noisy public zones
- bathrooms not opening directly into kitchens where avoidable
- private rooms away from primary entrance
- service/storage separated from guest-facing zones
- meeting rooms separated from noisy work zones
- clinic consultation rooms buffered from waiting-area noise where possible

### Zoning And Circulation

Zones:

- public: entry, living, dining, reception, waiting area
- private: bedrooms, studies, consultation rooms
- service: kitchen, bathroom, laundry, storage, utility
- circulation: corridor, stairs, lifts, lobby

Collect:

- zone sequences
- central-corridor and side-corridor patterns
- open-plan layouts with limited corridors
- stair/lift placement near common circulation
- entry-to-room access notes

### Openings, Accessibility, And Egress

Collect public textual guidance:

- external rooms generally need natural-light openings
- bedrooms and living rooms commonly sit on external walls
- bathrooms need ventilation, window, or service-shaft consideration
- doors connect rooms to corridors or common areas
- main entry commonly reaches foyer, living, or reception zones
- balcony doors connect to living rooms or bedrooms
- public accessibility circulation notes
- public corridor, doorway, stair, lift, and emergency-exit references

Store these as reference notes, never as a claim of legal compliance.

### Layout Pattern Examples

Target high-level patterns:

- open-plan apartment
- compact studio
- linear-corridor apartment
- central-living layout
- split public/private house
- ground-floor public plus upper-floor private
- office with reception, open workspace, and meeting rooms
- clinic with reception, waiting, and consultation rooms
- classroom cluster around corridor
- retail display, checkout, and storage layout

## 6. Source Policy

Permitted:

- public textual guidance pages
- public government or institutional accessibility references
- public articles with textual room-size or layout-rule references
- public HTML tables and lists
- manually approved source URLs

Not permitted:

- blocked paths under robots.txt
- paid or authenticated content
- watermarked or copyrighted plan drawings
- image galleries, social-media content, Pinterest, or Instagram
- pages containing personal or private client data
- sources whose terms prohibit the intended collection

Every stored raw record and processed pattern must retain:

- source ID
- source URL
- access timestamp
- scrape-run ID for raw data

## 7. Legal And Ethical Scraping Rules

- Check robots.txt before fetching page content.
- Refuse to scrape a disallowed path.
- Treat an invalid URL as blocked.
- Handle missing robots.txt conservatively but explicitly: allow public text fetch for MVP while recording that no policy file was found.
- Handle robots.txt network errors explicitly and refuse the run until the source can be checked.
- Use a polite ArchiAI user agent and fetch one URL per manual run.
- Do not recursively crawl links.
- Do not download images or binary files.
- Do not collect personal data.
- Store public textual rules and structured notes, not reproductions of drawings.

## 8. Scraper Architecture

Keep scraper code separate from design generation:

```text
Authenticated API
  -> scraper source CRUD
  -> robots checker
  -> single-source scraper runner
  -> raw text records
  -> deterministic cleaner / metadata extractor
  -> structured layout patterns
```

Proposed backend modules:

```text
backend/app/models/scraper_source.py
backend/app/models/scraper_run.py
backend/app/models/scraped_record.py
backend/app/models/layout_pattern.py
backend/app/schemas/scraper.py
backend/app/services/robots_txt_checker.py
backend/app/services/scraper_service.py
backend/app/services/scraper_cleaning_service.py
backend/app/api/scraper/router.py
```

For MVP, one authenticated request triggers one scrape run synchronously. Background queues and scheduling stay deferred.

## 9. Proposed Database Models

### ScraperSource

| Field | Type | Notes |
|---|---|---|
| `id` | String UUID | Primary key |
| `name` | String | Human-readable source name |
| `base_url` | Text | Public page or base URL |
| `robots_txt_url` | Text | Explicit or derived robots URL |
| `is_permitted` | Boolean | Last known policy result |
| `data_type` | String | Textual content type |
| `source_category` | String | `guideline`, `room_size_reference`, or `layout_pattern_reference` |
| `added_at` | Timestamp | Source registration timestamp |
| `last_checked` | Timestamp | Last robots check |
| `created_by` | FK to User | Authenticated source creator |

### ScraperRun

| Field | Type | Notes |
|---|---|---|
| `id` | String UUID | Primary key |
| `source_id` | FK to ScraperSource | Indexed |
| `started_at` | Timestamp | Run start |
| `completed_at` | Timestamp | Optional |
| `status` | String | `pending`, `running`, `completed`, or `failed` |
| `records_collected` | Integer | Defaults to zero |
| `error_message` | Text | Optional |

### ScrapedRecord

| Field | Type | Notes |
|---|---|---|
| `id` | String UUID | Primary key |
| `source_id` | FK to ScraperSource | Indexed |
| `run_id` | FK to ScraperRun | Indexed |
| `source_url` | Text | Fetched page URL |
| `accessed_at` | Timestamp | Fetch timestamp |
| `raw_text` | Text | Clean textual reference only |
| `raw_metadata_json` | JSON | Optional extraction context |

### LayoutPattern

| Field | Type | Notes |
|---|---|---|
| `id` | String UUID | Primary key |
| `source_id` | FK to ScraperSource | Indexed |
| `source_url` | Text | Public provenance |
| `accessed_at` | Timestamp | Public source access timestamp |
| `building_type` | String | Optional normalized building category |
| `layout_pattern` | String | Optional normalized pattern name |
| `room_type` | String | Optional normalized room category |
| `typical_area_sqm_min` | Float | Optional |
| `typical_area_sqm_max` | Float | Optional |
| `zone` | String | Optional normalized zone |
| `adjacent_to` | JSON | String array |
| `avoid_adjacent_to` | JSON | String array |
| `room_to_total_area_ratio_min` | Float | Optional |
| `room_to_total_area_ratio_max` | Float | Optional |
| `circulation_notes` | Text | Optional |
| `door_window_notes` | Text | Optional |
| `accessibility_notes` | Text | Optional |
| `egress_notes` | Text | Optional |
| `placement_notes` | Text | Optional |
| `confidence` | String | `low`, `medium`, or `high` |
| `created_at` | Timestamp | Pattern creation timestamp |

Use JSON rather than PostgreSQL-only JSONB in models where practical so SQLite tests remain portable while PostgreSQL still stores structured values.

## 10. Backend Endpoint Plan

Authenticated MVP routes:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/scraper/sources` | List registered sources |
| `POST` | `/api/scraper/sources` | Register a public reference source |
| `GET` | `/api/scraper/sources/{id}` | Get source detail |
| `PUT` | `/api/scraper/sources/{id}` | Update source metadata |
| `DELETE` | `/api/scraper/sources/{id}` | Delete source if no protected references block it |
| `POST` | `/api/scraper/run` | Run one permitted source synchronously |
| `GET` | `/api/scraper/runs` | List run history newest first |
| `GET` | `/api/scraper/runs/{id}` | Get run detail |
| `GET` | `/api/scraper/status` | Return latest run status |
| `GET` | `/api/scraper/patterns` | List processed layout-learning records |

The current application has no system-admin role. For this MVP, routes require authentication and clearly document that limitation. A dedicated admin authorization layer is deferred.

## 11. Data Cleaning Plan

Deterministic MVP cleaning:

1. Remove scripts, styles, navigation noise, and repeated whitespace.
2. Extract visible text from headings, paragraphs, lists, and tables.
3. Normalize casing for vocabulary matching while preserving source text.
4. Detect known building types and room types from controlled vocabularies.
5. Detect numeric area ranges in square metres and square feet.
6. Convert square feet to square metres while retaining source notes.
7. Detect zone keywords.
8. Detect simple adjacency and separation phrases.
9. Detect circulation, opening, accessibility, and egress keywords.
10. Store sparse structured records when values are unavailable rather than guessing.

## 12. Metadata Extraction Plan

Input:

- raw visible text
- source URL
- accessed timestamp

Output:

```json
{
  "source_url": "https://example.com/public-layout-guide",
  "accessed_at": "2026-05-31T00:00:00Z",
  "building_type": "apartment",
  "layout_pattern": "public_private_split",
  "room_type": "bedroom",
  "typical_area_sqm_min": 10,
  "typical_area_sqm_max": 16,
  "zone": "private",
  "adjacent_to": ["bathroom", "corridor"],
  "avoid_adjacent_to": ["kitchen", "garage"],
  "placement_notes": "Source-derived textual note.",
  "confidence": "medium"
}
```

MVP confidence:

- `high`: explicit textual statement or table value
- `medium`: deterministic phrase match with source text retained
- `low`: partial metadata with limited context

## 13. Layout Pattern Extraction Plan

Create one or more sparse `LayoutPattern` records from each raw record. Do not manufacture fields when source text does not contain them.

Examples:

- room-size table row -> room type plus area range
- article paragraph -> building type plus zoning or adjacency notes
- public accessibility page -> circulation/accessibility reference note
- layout-guide list -> pattern name plus zone sequence and common room groups

Processed patterns remain read-only learning references during Sprint 10.

## 14. Test Plan

### Backend

- Source create/list/get/update/delete.
- Run creation, completion, failure, status, and record counts.
- robots.txt allowed, disallowed, missing, network-error, and invalid-URL behavior.
- Runner refusal for blocked paths.
- HTML text extraction without image collection.
- Raw-record normalization.
- Deterministic room/building/zone/area/adjacency extraction.
- Pattern persistence with source URL and access timestamp.
- Auth required for scraper APIs.
- Existing auth, project, design, draft, refinement, workspace, and activity tests remain green.

### Frontend

- Service endpoint mapping.
- Source form submission.
- Loading, empty, error, run-history, and pattern-table states.
- TypeScript check, Vitest suite, and production build remain green.

## 15. Task Checklist

1. Write Sprint 10 plan and add the `CLAUDE.md` checklist.
2. Add failing backend pipeline tests.
3. Add `ScraperSource` and `ScraperRun` models plus migration.
4. Add robots.txt checker utility.
5. Add safe single-source scraper runner and raw-record storage.
6. Add deterministic data cleaning and metadata extraction.
7. Add structured `LayoutPattern` model plus migration.
8. Add authenticated scraper-management APIs.
9. Add simple scraper-monitoring frontend UI.
10. Run final checks and mark Sprint 10 complete.

## 16. Risks And Assumptions

- robots.txt is necessary but not sufficient for permission. Sources must also be intentionally approved before use.
- Missing robots.txt and robots network failure are different states. Network failure blocks scraping; a confirmed missing file can permit public textual fetching with explicit metadata.
- Source pages may change structure. Store raw normalized text and provenance so extraction can be rerun.
- Deterministic parsing intentionally produces sparse records. It must not guess missing architectural facts.
- The existing app has no admin role, so MVP scraper APIs are authenticated-user-only.
- Synchronous runs are suitable only for one safe source at a time.
- SQLite backend tests build tables from SQLAlchemy metadata; model exports must remain complete.
- PostgreSQL migrations must remain additive and reversible.

## 17. Commit Plan

Create local commits only on `sprint-10/web-scraper-data-pipeline`. Do not push during the task sequence.

1. `Add Sprint 10 scraper pipeline plan`
2. `Add scraper pipeline backend tests`
3. `Add scraper source and run models`
4. `Add robots txt checker utility`
5. `Add basic scraper runner`
6. `Add scraper data cleaning and metadata extraction`
7. `Add structured layout pattern model`
8. `Add scraper management API endpoints`
9. `Add scraper monitoring UI`
10. `Complete Sprint 10 web scraper data pipeline`
