# Sprint 10 To Sprint 11 Pattern Data Workflow

## Short Answer

You do not need to run the Sprint 10 scraper before generating layouts.

Sprint 11 always has deterministic fallback rules for room sizing, zoning, adjacency, avoid-adjacency, building templates, and layout-quality scoring. Layout generation continues to work when the `layout_patterns` table is empty.

Run the scraper or seed local MVP patterns before testing the data-informed path. Pattern records act as a structured knowledge base that overlays the built-in defaults. This is not neural-model training and does not require a paid AI API.

## Sprint 10: Structured Public-Text Collection

Sprint 10 stores safe public-text references through these tables:

- `scraper_sources`: registered public source URLs and source metadata
- `scraper_runs`: explicit scraper-run status and history
- `scraped_records`: visible public text with `source_url` and `accessed_at`
- `layout_patterns`: deterministic structured metadata extracted from collected text

The scraper checks `robots.txt` before fetching a source. A blocked, invalid, or unreachable policy check fails closed. The HTML parser ignores images, SVG, scripts, styles, and non-text content. Do not register copyrighted floor-plan image pages as reference sources.

Extracted `layout_patterns` fields include:

- Building type and layout-pattern name
- Room type and typical area range
- Public, private, service, or circulation zone
- Preferred and avoided adjacencies
- Optional room-to-total-area ratios
- Circulation, opening, accessibility, egress, and placement notes
- Source URL, access time, and confidence

Authenticated users can register and run vetted public-text sources from the `/scraper` dashboard or through `/api/scraper/*`.

## Sprint 11: Pattern-Informed Deterministic Generation

`POST /api/design/generate` uses the following flow:

1. Parse the prompt with deterministic keyword rules.
2. Detect building type, rooms, floor count, and optional total area.
3. Load relevant `LayoutPattern` rows for the detected building and rooms.
4. Overlay accepted records onto fallback sizing, zone, adjacency, and avoid-adjacency rules.
5. Apply a deterministic building template.
6. Generate room blocks and floor assignments.
7. Score the generated concept layout and return compact generation insights.

Database pattern records currently improve:

- Room area ranges
- Room-to-total-area ratios
- Room zones
- Preferred adjacency
- Avoid-adjacency
- Layout-pattern diagnostics and quality scoring

Prompt keyword detection and building-type detection remain code-defined keyword maps. Scraped or seeded patterns do not add arbitrary new prompt vocabulary yet.

## No Pattern Data Flow

```text
User prompt
  -> rule-based parser
  -> fallback building template
  -> fallback sizing, zoning, and adjacency rules
  -> deterministic layout
  -> quality score with pattern-data:fallback-defaults
```

## Pattern Data Available Flow

```text
User prompt
  -> rule-based parser
  -> detected building type and rooms
  -> query layout_patterns
  -> overlay pattern-informed sizing, zoning, and adjacency rules
  -> deterministic building template and layout
  -> quality score with pattern-data:source-derived or pattern-data:seed
```

## Local MVP Seed Data

Use the seed command when you want predictable local pattern records without relying on live online sources. The seed rows are explicitly labeled:

- `source_url = "seed:mvp-patterns"`
- `data_type = "structured_seed"`
- `source_category = "dev_seed_layout_patterns"`
- `confidence = "seed"`
- Placement notes begin with `MVP seed only:`

The resolver accepts seed rows below medium and high confidence source-derived rows. A stronger vetted source-derived pattern wins when both exist.

Run migrations, register a local user, then seed from the `backend` folder:

```powershell
..\.venv311\Scripts\python.exe -m alembic upgrade head
..\.venv311\Scripts\python.exe -m scripts.seed_layout_patterns --user-email you@example.com
```

The command is idempotent. Re-running it does not create duplicate pattern rows.

## Run A Vetted Public-Text Source

1. Start the app and sign in.
2. Open `http://localhost:5173/scraper`.
3. Add a vetted HTTP or HTTPS public-text source and its `robots.txt` URL.
4. Click `Run`.
5. Confirm the run completed and inspect extracted patterns.

The scraper does not crawl automatically. Every run is explicit.

## Verify Pattern Records

Use the Data Pipeline page at `http://localhost:5173/scraper`, or call the authenticated API:

```powershell
$token = (Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/auth/login `
  -ContentType 'application/json' `
  -Body '{"email":"you@example.com","password":"password123"}').access_token

Invoke-RestMethod `
  -Uri http://localhost:8000/api/scraper/patterns `
  -Headers @{ Authorization = "Bearer $token" }
```

Seed rows are easy to recognize because their `source_url` is `seed:mvp-patterns`.

## Compare Generation Before And After Seeding

Generate a layout before seeding and inspect:

```json
{
  "patternDataUsed": false,
  "patternDataSource": "fallback-defaults"
}
```

Seed the records, generate again, and inspect:

```json
{
  "patternDataUsed": true,
  "patternDataSource": "seed"
}
```

Vetted scraper-derived records produce:

```json
{
  "patternDataUsed": true,
  "patternDataSource": "source-derived"
}
```

Useful prompts:

- `2 bedroom apartment with open plan kitchen, living room, balcony and 2 bathrooms`
- `small clinic with waiting area, reception, 2 consultation rooms and bathroom`
- `office with reception, meeting room and open workspace`
- `2 floor house with bedrooms upstairs, living room and kitchen downstairs`

## Future AI Scope

Pattern data is a structured rule overlay today. Future work may evaluate model training, fine-tuning, layout-ranking models, LLM prompt parsing, OpenAI/Claude/Gemini providers, local runtimes through Ollama or Hugging Face, and privacy-safe learning from user edits. Those capabilities remain disabled and deferred. See [`FUTURE_AI_INTEGRATION.md`](FUTURE_AI_INTEGRATION.md).
