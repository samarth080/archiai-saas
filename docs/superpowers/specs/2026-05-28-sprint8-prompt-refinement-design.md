# Sprint 8 — Prompt Refinement: Design Spec

**Date:** 2026-05-28
**Status:** Approved
**Sprint Goal:** Users improve an existing saved layout with a follow-up prompt; refinements add, remove, or resize rooms without disturbing existing room positions, and every refinement creates a new `DesignVersion`.

---

## Context

Builds on Sprint 6 (which landed the `Design` and `DesignVersion` tables and the manual save flow) and Sprint 7 (which added project-scoped versions, duplicate, and thumbnails). Today, when a user types into the bottom prompt bar, the layout is **regenerated from scratch** — any manual edits the user has made in the editor are lost. Sprint 8 introduces a second mode of that bar that **refines** the existing layout instead.

Files already present and extended rather than rewritten:

- `backend/app/services/prompt_service.py` — keyword tables, count parsing, size modifiers (reused, not modified)
- `backend/app/services/layout_service.py` — zone partition (reused for placement logic)
- `backend/app/api/designs/router.py` — gains one new endpoint
- `backend/app/schemas/design.py` — gains two new request/response shapes
- `frontend/src/services/design.service.ts` — gains `refineLayout`
- `frontend/src/pages/Project/index.tsx` — gains a Generate/Refine toggle and a summary banner

---

## Scope

### In scope

- `refinement_service.py` — rule-based parser (text → list of refinement ops) + applier (ops + current layout → new layout + summary string)
- `POST /api/design/refine { designId, prompt }` — auth-required endpoint
- `DesignVersion(version_type='refined')` row per successful refinement
- `ActivityLog` entry `design.refined`
- Frontend: Generate / Refine segmented toggle on the bottom prompt bar; Refine disabled until a saved design exists
- Frontend: dismissable summary banner above the prompt bar showing what changed (`"Added 1 bedroom, removed 1 office"`)
- Backend tests: parser, applier (including the append-only invariant), endpoint
- Frontend tests: toggle enabled/disabled, submit dispatches correct endpoint, banner renders + dismisses

### Out of scope

- **Move and rotate refinements.** The Inspector already covers these directly. Adding "move the kitchen to the corner" is too ambiguous to parse deterministically.
- **Rename refinements.** Inspector handles labels.
- **Style changes** (`"make it modern"`) — the rest of the system has no style semantics yet.
- **Adding or removing floors.** Deferred to a future sprint; would require reshuffling.
- **Smart repacking after add/remove.** Append-only by design — manual drags from the editor must survive a refinement.
- **Undo / restore from a previous version.** Sprint 9.
- **Per-room diff highlights on the canvas.** Banner only.

---

## Architecture

### Backend flow

```text
POST /api/design/refine { designId, prompt }
  ├── _require_auth → user_id
  ├── load Design (404 if missing, 403 if owned by another user)
  ├── ops = refinement_service.parse_refinement(prompt)
  │     └── if [] → 422 "Couldn't understand the refinement. Try…"
  ├── new_layout, summary = refinement_service.apply_refinement(design.layout_json, ops)
  │     └── if summary == "" → 422 "No matching rooms found for that change."
  ├── design.layout_json = new_layout
  ├── design.updated_at = now()
  ├── INSERT DesignVersion(version_type='refined', version_number = max+1,
  │                       version_name=f"Refinement v{n}", change_summary=summary,
  │                       prompt_used=prompt, layout_json=new_layout)
  ├── log_activity("design.refined")
  └── 200 RefineResponse(**new_layout, refinementSummary=summary,
                         designId, designVersionId)
```

### Frontend flow

```text
User has a saved design (designId != null)
  → mode auto-flips from 'generate' to 'refine' the first time hasSavedLayout becomes true
User types "add a bedroom" and clicks Refine
  → POST /api/design/refine { designId, prompt }
  → on 200: canvasStore.loadLayout(result)
            setRefinementSummary(result.refinementSummary)
  → banner renders above prompt bar
  → user types in textarea → banner auto-clears (fresh edit starting)
  → user can dismiss the banner with the ✕ button

Mode = 'generate' (user explicitly toggled back, or never had a design)
  → POST /api/design/generate as today; replaces the layout
```

---

## File Map

```text
backend/app/
├── services/
│   └── refinement_service.py            CREATE — parse_refinement, apply_refinement, op dataclasses
├── schemas/
│   └── design.py                        MODIFY — RefineRequest, RefineResponse
├── api/designs/router.py                MODIFY — POST /refine
└── tests/
    ├── test_refinement_service.py       CREATE — parser + applier unit tests
    └── test_designs.py                  MODIFY — three endpoint tests

frontend/src/
├── services/
│   └── design.service.ts                MODIFY — refineLayout, RefineResponse
├── pages/Project/
│   ├── index.tsx                        MODIFY — mode toggle, submit dispatcher, banner
│   └── index.test.tsx                   CREATE — RTL tests for toggle + banner
```

---

## Backend: `refinement_service.py`

### Op dataclasses

```python
from dataclasses import dataclass

@dataclass
class AddOp:
    room_type: str
    count: int                  # positive

@dataclass
class RemoveOp:
    room_type: str
    count: int | None           # None = remove all matches; otherwise remove first N

@dataclass
class ResizeOp:
    room_type: str
    factor: float               # 1.4 = bigger, 0.7 = smaller

RefinementOp = AddOp | RemoveOp | ResizeOp
```

### Parser — `parse_refinement(prompt: str) -> list[RefinementOp]`

Lowercases the prompt and reuses `ROOM_PATTERNS`, `WORD_TO_NUM`, and `_COUNT_ALTS` from `prompt_service.py` so the room-keyword surface stays in one place. Runs three passes in this fixed order — ADD, REMOVE, RESIZE — blanking out the matched span after each match so later passes don't double-count.

| Op | Verbs | Regex (conceptual) |
|---|---|---|
| ADD | `add`, `include`, `insert`, `put`, `another`, `also need` | `\b(?:add\|include\|insert\|put\|another\|also need)\s+(?:an?\s+\|(\d+)\s+\|(<count-word>)\s+)?<room-keyword>s?\b` |
| REMOVE | `remove`, `delete`, `drop`, `get rid of`, `no more`, `without` | `\b(?:remove\|delete\|drop\|get rid of\|no more\|without)\s+(?:(all)\s+\|(the)\s+\|an?\s+\|(\d+)\s+)?<room-keyword>s?\b` |
| RESIZE | `make … bigger/larger/spacious/smaller/compact`, `expand`, `shrink` | `\b(?:make\s+(?:the\s+)?<room-keyword>\s+(bigger\|larger\|spacious\|smaller\|compact)\|(expand)\s+(?:the\s+)?<room-keyword>\|(shrink)\s+(?:the\s+)?<room-keyword>)\b` |

`<room-keyword>` is any keyword string from `ROOM_PATTERNS` — longer/more specific phrases first so `"master bedroom"` doesn't get partial-matched by `"bedroom"`. `<count-word>` is the `_COUNT_ALTS` alternation (`one`…`ten`).

**Examples:**

| Prompt | Parsed ops |
|---|---|
| `"add a bedroom"` | `[AddOp(bedroom, 1)]` |
| `"add 3 bathrooms"` | `[AddOp(bathroom, 3)]` |
| `"add three bedrooms"` | `[AddOp(bedroom, 3)]` |
| `"another bedroom please"` | `[AddOp(bedroom, 1)]` |
| `"remove the office"` | `[RemoveOp(office, 1)]` |
| `"remove all bathrooms"` | `[RemoveOp(bathroom, None)]` |
| `"no more bathrooms"` | `[RemoveOp(bathroom, None)]` |
| `"make the kitchen bigger"` | `[ResizeOp(kitchen, 1.4)]` |
| `"shrink the living room"` | `[ResizeOp(living_room, 0.7)]` |
| `"add a bedroom and remove the office"` | `[AddOp(bedroom, 1), RemoveOp(office, 1)]` |
| `"just chilling"` | `[]` |

**Disambiguation rules baked in:**
- Bare ADD with no count → count = 1.
- `"add another bedroom"` → count = 1 (the word `"another"` is the verb, not a count modifier).
- REMOVE with no quantifier → count = 1 (remove the first match).
- REMOVE with `all` / `no more` → count = `None` (remove all matches).
- RESIZE always targets every room of the matching type — see the applier section.

### Applier — `apply_refinement(layout: dict, ops: list[RefinementOp]) -> tuple[dict, str]`

Returns the new layout dict and a one-sentence summary for the banner. The summary is `""` when every op was a no-op (e.g. removing a room type that doesn't exist); the endpoint returns 422 in that case.

**Order of operations:** RESIZE → REMOVE → ADD.
- Resize first so we don't waste work on rooms we're about to remove.
- Remove second so ADD's "rightmost room in zone" calculation reflects the post-removal state.

**Append-only invariant:** existing room dicts are deep-copied into the result. Their `id`, `position`, `size`, `color`, `floorId`, `floorLevel`, and `rotation` are never mutated except by an explicit `ResizeOp` matching them.

#### RESIZE

For each `ResizeOp(room_type, factor)`:
- For every room in the layout where `room.roomType == room_type`:
  - `f = sqrt(factor)`
  - `size.w *= f`; `size.d *= f` (round to 1 decimal place, same as `prompt_service.py`)
  - `position.y = floor_elevation + size.h / 2` so the box bottom stays on the floor
  - `size.h` and `position.x` / `position.z` are unchanged
- Summary contribution: `"Resized N room(s) (<room labels comma-separated>)"`
- If zero rooms matched: contributes `"<room-type> (none found)"` to the summary instead

**Known trade-off:** because X/Z are preserved, a grown room can overlap its neighbour. We accept this — the user can drag to fix. Adding collision avoidance is deferred (would require a "Section 3.5" of the algorithm and complicates testing).

#### REMOVE

For each `RemoveOp(room_type, count)`:
- Find all rooms where `room.roomType == room_type`, in layout order.
- If `count is None`: drop all of them.
- Else: drop the first `count` of them (oldest first).
- Summary contribution: `"Removed N <room label>"` (label pluralised when N > 1).
- If zero matched: contributes `"<room-type> (none found)"`.

#### ADD

For each `AddOp(room_type, count)`:
- For `i in range(count)`:
  1. **Choose target floor.** Single-floor layout → `floor_0`. Multi-floor → use the same rule as `layout_service._assign_rooms_to_floors`:
     - `living_room`, `kitchen`, `dining_room`, `hallway`, `garage` → ground floor
     - `bathroom` → first floor that has no bathroom yet, otherwise round-robin upper floors
     - `bedroom` / `master_bedroom` → round-robin upper floors (level 1+)
     - `balcony`, `utility` → top floor
     - Anything else → round-robin upper floors
  2. **Choose zone** (`_PUBLIC` / `_PRIVATE` / other) using the same `frozenset` partition as `layout_service.py`.
  3. **Compute X.** For the target floor + zone, find the rightmost existing room: `rightmost = max(r.position.x + r.size.w / 2 for r in rooms_on_floor if r.room_type in zone)` (or `0.0` if the zone is empty on that floor). New `position.x = rightmost + 1.0 + new.size.w / 2` (the `1.0` is `_GAP`).
  4. **Compute Z.** If the zone already has at least one room on this floor, reuse that row: `position.z = existing.position.z + (new.size.d - existing.size.d) / 2` so the new room's front edge lines up with the row (when sizes match, the new room sits at the same `z`). If the zone is empty on this floor, start a new row below all existing rows: `position.z = max(r.position.z + r.size.d/2 for r in floor_rooms) + _ZONE_GAP + new.size.d/2`, falling back to `new.size.d / 2` when the floor has no rooms at all.
  5. **Compute Y.** `floor_elevation + new.size.h / 2`.
  6. **Defaults.** `size = ROOM_DEFAULTS[room_type]`, `color = ROOM_COLORS[room_type]`, `rotation = {x:0,y:0,z:0}`, `objectType = "room"`, `roomType = room_type`, `label = ROOM_DEFAULTS[room_type]["label"]`. New `uuid4()` for `id`.
- Summary contribution: `"Added N <room label>"`.

#### Layout JSON updates

After ops are applied:
- `metadata.room_count` and `metadata.totalRooms` recomputed.
- `floors[].rooms` rebuilt from the final flat room list (using `floorLevel` to bucket).
- Top-level `rooms` rebuilt (flat array stays in sync).
- `metadata.lastRefinement = prompt` so the persisted version carries refinement context.

#### Summary string

Join op contributions with `", "`. Capitalise the first letter. Empty if every op was a no-op (endpoint maps to 422).

Examples:
- `"Added 1 bedroom"`
- `"Resized 1 kitchen"`
- `"Resized 3 bedrooms (Master Bedroom, Bedroom 1, Bedroom 2)"`
- `"Added 1 bedroom, removed 1 office"`
- `"Added 1 study (none found)"` — never appears because ADD always succeeds; the `(none found)` suffix is only for REMOVE/RESIZE no-ops

---

## Backend: API

### Schemas (`schemas/design.py`)

```python
class RefineRequest(BaseModel):
    design_id: str = Field(..., alias="designId")
    prompt: str = Field(..., min_length=3)
    model_config = {"populate_by_name": True}

class RefineResponse(GenerateResponse):
    refinementSummary: str
```

`RefineResponse` is `GenerateResponse` plus one extra field. `min_length=3` on `prompt` because refinement prompts are short — `"add a bed"` should be fine.

### Endpoint (`api/designs/router.py`)

```python
@router.post("/refine", response_model=RefineResponse)
async def refine(
    request: RefineRequest,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> RefineResponse:
    design = await db.get(Design, request.design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")
    if design.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    ops = parse_refinement(request.prompt)
    if not ops:
        raise HTTPException(
            status_code=422,
            detail="Couldn't understand the refinement. "
                   "Try: 'add a bedroom', 'remove the office', 'make the kitchen bigger'.",
        )

    new_layout, summary = apply_refinement(design.layout_json, ops)
    if not summary:
        raise HTTPException(status_code=422,
                            detail="No matching rooms found for that change.")

    design.layout_json = new_layout
    design.updated_at = datetime.now(timezone.utc)

    max_version = await db.scalar(
        select(func.max(DesignVersion.version_number))
        .where(DesignVersion.design_id == design.id)
    )
    next_version = (max_version or 0) + 1

    version = DesignVersion(
        design_id=design.id,
        project_id=design.project_id,
        user_id=user_id,
        version_number=next_version,
        version_name=f"Refinement v{next_version}",
        version_type="refined",
        change_summary=summary,
        layout_json=new_layout,
        prompt_used=request.prompt,
    )
    db.add(version)
    await db.commit()
    await db.refresh(design)
    await db.refresh(version)

    await log_activity(db, user_id, "design.refined")

    return RefineResponse(
        **new_layout,
        designId=design.id,
        designVersionId=version.id,
        refinementSummary=summary,
    )
```

### Error responses

| Scenario | Status | Body `error` |
|---|---|---|
| Missing token | 401 | `Not authenticated` |
| Design not found | 404 | `Design not found` |
| Design owned by another user | 403 | `Access forbidden` |
| Prompt < 3 chars | 422 | Pydantic |
| Parser returns no ops | 422 | `Couldn't understand the refinement. Try: 'add a bedroom', 'remove the office', 'make the kitchen bigger'.` |
| All ops no-op | 422 | `No matching rooms found for that change.` |

---

## Frontend: `design.service.ts`

```typescript
export interface RefineResponse extends GenerateResponse {
  refinementSummary: string
}

export async function refineLayout(
  designId: string,
  prompt: string,
): Promise<RefineResponse> {
  const { data } = await api.post<RefineResponse>('/api/design/refine', {
    designId, prompt,
  })
  return data
}
```

---

## Frontend: `pages/Project/index.tsx`

### State additions

```typescript
const [mode, setMode] = useState<'generate' | 'refine'>('generate')
const [refinementSummary, setRefinementSummary] = useState<string | null>(null)
```

Auto-flip mode to `'refine'` the first time `designId` becomes non-null, only if the user has not manually changed mode. Implementation: a single `useEffect` that watches `designId` and, when it goes from null → non-null, calls `setMode('refine')`. Subsequent designId changes do nothing.

### Segmented toggle

```tsx
<div className="inline-flex rounded border border-gray-300 text-xs" role="tablist">
  <button
    role="tab"
    aria-selected={mode === 'generate'}
    className={`px-3 py-1 ${mode === 'generate' ? 'bg-indigo-500 text-white' : 'bg-white text-gray-700'}`}
    onClick={() => setMode('generate')}
  >
    Generate
  </button>
  <button
    role="tab"
    aria-selected={mode === 'refine'}
    disabled={!designId}
    title={designId ? '' : 'Generate a layout first'}
    className={`px-3 py-1 ${mode === 'refine' ? 'bg-indigo-500 text-white' : 'bg-white text-gray-700'} disabled:opacity-50 disabled:cursor-not-allowed`}
    onClick={() => setMode('refine')}
  >
    Refine
  </button>
</div>
```

### Submit dispatcher

The existing `handleGenerate` is renamed to `handleSubmit` and branches on `mode`:

```typescript
const handleSubmit = async () => {
  if (!prompt.trim()) return
  setGenerating(true)
  setGenerateError(null)

  try {
    if (mode === 'refine' && designId) {
      const result = await refineLayout(designId, prompt)
      loadLayout(result)
      setRefinementSummary(result.refinementSummary)
      setPrompt('')
    } else {
      const result = await generateLayout(prompt, id)
      loadLayout(result)
      setHasSavedLayout(true)
      setRefinementSummary(null)
    }
  } catch (err) {
    const apiErr = err as { response?: { data?: { error?: string } } }
    setGenerateError(
      apiErr.response?.data?.error
        ?? (mode === 'refine'
              ? 'Refinement failed. Try a more specific change.'
              : 'Generation failed. Try a more detailed description.'),
    )
  } finally {
    setGenerating(false)
  }
}
```

Button label tracks the mode: `mode === 'refine' ? (generating ? 'Refining…' : 'Refine') : (generating ? 'Generating…' : 'Generate')`.

### Summary banner

Renders above the prompt-bar `<div>`, only when `refinementSummary` is non-null:

```tsx
{refinementSummary && (
  <div
    role="status"
    aria-live="polite"
    className="border-t border-emerald-200 bg-emerald-50 px-3 py-2 flex items-start gap-2"
  >
    <span className="text-xs text-emerald-700 flex-1">{refinementSummary}</span>
    <button
      type="button"
      aria-label="Dismiss"
      className="text-xs text-emerald-700 hover:text-emerald-900"
      onClick={() => setRefinementSummary(null)}
    >
      ✕
    </button>
  </div>
)}
```

Banner clears automatically when the user starts typing — the textarea's `onChange` calls `setRefinementSummary(null)` along with `setPrompt(...)`.

---

## Canvas store

**No changes.** `loadLayout(result)` already preserves `designId` and `designVersionId` from the response, which is exactly what the refinement path needs. The in-memory `activityLog` stays local to the editor; refinement history lives server-side as `DesignVersion` rows.

---

## Testing

### `backend/app/tests/test_refinement_service.py` (CREATE — 11 tests)

Parser tests:
1. `parse_refinement("add a bedroom")` returns `[AddOp(bedroom, 1)]`
2. `parse_refinement("add 3 bathrooms and remove the office")` returns `[AddOp(bathroom, 3), RemoveOp(office, 1)]`
3. `parse_refinement("make the kitchen bigger")` returns `[ResizeOp(kitchen, 1.4)]`
4. `parse_refinement("shrink the living room")` returns `[ResizeOp(living_room, 0.7)]`
5. `parse_refinement("remove all bathrooms")` returns `[RemoveOp(bathroom, None)]`
6. `parse_refinement("hello world")` returns `[]`

Applier tests (using a fixture layout with 1 living room, 1 kitchen, 2 bedrooms, 1 office):
7. `apply_refinement(layout, [AddOp(bedroom, 1)])` — third bedroom appended; original 2 bedrooms' position and size are identical to the input layout (append-only invariant)
8. `apply_refinement(layout, [RemoveOp(office, 1)])` on a layout with no office — returns the original layout and an empty summary
9. `apply_refinement(layout, [ResizeOp(kitchen, 1.4)])` — kitchen W and D scaled by √1.4; kitchen position X and Z unchanged; Y matches `floor_elevation + h/2`
10. Multi-floor — `apply_refinement(multi_floor_layout, [AddOp(bedroom, 1)])` lands the new bedroom on the first upper floor (level 1)
11. Summary text — `apply_refinement(layout, [AddOp(bedroom, 1), RemoveOp(office, 1)])` returns summary `"Added 1 bedroom, removed 1 office"`

### `backend/app/tests/test_designs.py` (MODIFY — 3 new tests)

12. `test_refine_creates_new_version_and_logs_activity` — generate, refine `"add a bedroom"`, expect 200; verify the new layout has one extra bedroom, `DesignVersion(version_number=2, version_type='refined')` exists, ActivityLog has `design.refined`
13. `test_refine_unparsable_prompt_returns_422` — refine `"hello world"` → 422 with the help text
14. `test_refine_other_users_design_returns_403`

### `frontend/src/pages/Project/index.test.tsx` (CREATE — 3 RTL tests)

15. Refine button is disabled when `designId` is null in the store; becomes enabled after `designId` is set
16. Toggling to Refine and clicking submit posts to `/api/design/refine` with `{ designId, prompt }` (mock axios)
17. Banner renders with the `refinementSummary` text after a successful refine; clicking ✕ removes it

---

## Definition of Done

- [ ] `backend/app/services/refinement_service.py` exports `AddOp`, `RemoveOp`, `ResizeOp`, `parse_refinement`, `apply_refinement`
- [ ] `RefineRequest` and `RefineResponse` added to `schemas/design.py`
- [ ] `POST /api/design/refine` registered on `designs/router.py` with auth, 404 / 403 / 422 paths
- [ ] Successful refine inserts `DesignVersion(version_type='refined', change_summary=summary)` and logs `design.refined`
- [ ] Parser supports `add`, `include`, `insert`, `put`, `another`, `also need`; `remove`, `delete`, `drop`, `get rid of`, `no more`, `without`; `make … bigger/larger/spacious/smaller/compact`, `expand`, `shrink`
- [ ] Applier preserves the append-only invariant (existing room `id`/`position`/`size` unchanged except by `ResizeOp` matches)
- [ ] Applier handles multi-floor placement using the Sprint 6 zone+floor rules
- [ ] Frontend `refineLayout` exported from `design.service.ts`
- [ ] Project page has the Generate/Refine segmented toggle; Refine disabled when no `designId`
- [ ] Single submit handler branches on mode; correct button label and loading text per mode
- [ ] Summary banner renders, is dismissable, and auto-clears when the user types
- [ ] 11 new parser/applier tests + 3 new endpoint tests + 3 new frontend RTL tests
- [ ] All existing backend and frontend tests still pass
- [ ] `npx tsc --noEmit` clean
- [ ] `docker-compose up` shows the refine flow end-to-end
