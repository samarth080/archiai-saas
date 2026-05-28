# Sprint 8 — Prompt Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Users improve an existing saved layout with a follow-up prompt that adds, removes, or resizes rooms — without disturbing existing room positions — and each refinement creates a new `DesignVersion`.

**Architecture:** New backend module `refinement_service.py` exposes a rule-based parser (`parse_refinement`) that turns a natural-language prompt into a list of `AddOp` / `RemoveOp` / `ResizeOp` dataclasses, and an applier (`apply_refinement`) that mutates an existing layout dict append-only and returns a summary string. A new `POST /api/design/refine` endpoint persists the result as a `DesignVersion(version_type='refined')` and logs `design.refined`. The frontend bottom prompt bar gains a Generate / Refine segmented toggle and a dismissable summary banner.

**Tech Stack:** FastAPI, SQLAlchemy (async), Pydantic v2, pytest, React 18, TypeScript, Zustand, Vitest, React Testing Library (added in Task 8), happy-dom (added in Task 8).

**Spec:** [docs/superpowers/specs/2026-05-28-sprint8-prompt-refinement-design.md](../specs/2026-05-28-sprint8-prompt-refinement-design.md)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/app/services/refinement_service.py` | CREATE | Op dataclasses, `parse_refinement`, `apply_refinement` |
| `backend/app/tests/test_refinement_service.py` | CREATE | 6 parser tests + 5 applier tests |
| `backend/app/schemas/design.py` | MODIFY | `RefineRequest`, `RefineResponse` |
| `backend/app/api/designs/router.py` | MODIFY | `POST /refine` endpoint |
| `backend/app/tests/test_designs.py` | MODIFY | 3 refine endpoint tests |
| `frontend/package.json` | MODIFY | Add `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `happy-dom` |
| `frontend/vitest.config.ts` | CREATE | Vitest config with `happy-dom`, setup file |
| `frontend/src/test-setup.ts` | CREATE | `expect.extend(matchers)` from jest-dom |
| `frontend/tsconfig.json` | MODIFY (if needed) | Include test types |
| `frontend/src/services/design.service.ts` | MODIFY | `refineLayout`, `RefineResponse` |
| `frontend/src/pages/Project/index.tsx` | MODIFY | Mode toggle, submit dispatcher, banner |
| `frontend/src/pages/Project/index.test.tsx` | CREATE | 3 RTL tests |
| `CLAUDE.md` | MODIFY | Mark Sprint 8 complete |

---

## Pre-flight

Work on the existing branch `sprint-8/prompt-refinement` (already created during brainstorming). All commits land on this branch; the final PR targets `main`.

```bash
git checkout sprint-8/prompt-refinement
git status   # expect: spec already committed; nothing untracked beyond the usual __pycache__
```

Verify the baseline tests pass before starting:

```bash
docker-compose -f docker-compose.yml up -d db   # backend tests need Postgres
cd backend && pytest -v 2>&1 | tail -5
# expected: 58 passed (per CLAUDE.md Sprint 7 numbers)
cd ../frontend && npm test 2>&1 | tail -5
# expected: 20 passed (per CLAUDE.md Sprint 6 numbers)
```

If baseline tests fail, stop and report — don't start implementing on a red branch.

---

### Task 1: Parser — `AddOp` dataclass + `parse_refinement` (ADD verbs)

**Files:**
- Create: `backend/app/services/refinement_service.py`
- Test:   `backend/app/tests/test_refinement_service.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/app/tests/test_refinement_service.py`:

```python
from app.services.refinement_service import AddOp, parse_refinement


def test_parse_add_single_bedroom():
    assert parse_refinement("add a bedroom") == [AddOp(room_type="bedroom", count=1)]


def test_parse_add_numeric_count():
    assert parse_refinement("add 3 bathrooms") == [AddOp(room_type="bathroom", count=3)]


def test_parse_add_word_count():
    assert parse_refinement("add three bedrooms") == [AddOp(room_type="bedroom", count=3)]


def test_parse_add_another():
    assert parse_refinement("another bedroom please") == [AddOp(room_type="bedroom", count=1)]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest app/tests/test_refinement_service.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.services.refinement_service'`.

- [ ] **Step 3: Implement the parser (ADD only)**

Create `backend/app/services/refinement_service.py`:

```python
import re
from dataclasses import dataclass

from app.services.prompt_service import ROOM_PATTERNS, WORD_TO_NUM


@dataclass
class AddOp:
    room_type: str
    count: int


@dataclass
class RemoveOp:
    room_type: str
    count: int | None  # None == remove all


@dataclass
class ResizeOp:
    room_type: str
    factor: float


RefinementOp = AddOp | RemoveOp | ResizeOp

_COUNT_ALTS = "|".join(WORD_TO_NUM.keys())
_ADD_VERBS = r"add|include|insert|put in|put|another|also need"


def _parse_count(raw: str | None) -> int:
    if raw is None:
        return 1
    if raw.isdigit():
        return int(raw)
    return WORD_TO_NUM.get(raw.lower(), 1)


def _blank_span(text: str, start: int, end: int) -> str:
    return text[:start] + " " * (end - start) + text[end:]


def parse_refinement(prompt: str) -> list[RefinementOp]:
    text = prompt.lower()
    ops: list[RefinementOp] = []

    # ADD pass
    for room_type, keywords in ROOM_PATTERNS:
        for keyword in keywords:
            pattern = re.compile(
                r"\b(?:" + _ADD_VERBS + r")\s+"
                r"(?:an?\s+|(?P<count>\d+|" + _COUNT_ALTS + r")\s+)?"
                + re.escape(keyword) + r"s?\b",
                re.IGNORECASE,
            )
            matches = list(pattern.finditer(text))
            if not matches:
                continue
            total = 0
            for m in matches:
                total += _parse_count(m.group("count"))
            ops.append(AddOp(room_type=room_type, count=total))
            for m in reversed(matches):
                text = _blank_span(text, m.start(), m.end())
            break  # don't try other keywords for the same room_type

    return ops
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && pytest app/tests/test_refinement_service.py -v
```
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/refinement_service.py backend/app/tests/test_refinement_service.py
git commit -m "feat(sprint8): add refinement parser ADD pass"
```

---

### Task 2: Parser — REMOVE verbs

**Files:**
- Modify: `backend/app/services/refinement_service.py`
- Modify: `backend/app/tests/test_refinement_service.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/app/tests/test_refinement_service.py`:

```python
from app.services.refinement_service import RemoveOp  # add to existing import


def test_parse_remove_single():
    assert parse_refinement("remove the office") == [RemoveOp(room_type="office", count=1)]


def test_parse_remove_all():
    assert parse_refinement("remove all bathrooms") == [RemoveOp(room_type="bathroom", count=None)]


def test_parse_remove_no_more():
    assert parse_refinement("no more bathrooms") == [RemoveOp(room_type="bathroom", count=None)]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest app/tests/test_refinement_service.py::test_parse_remove_single -v
```
Expected: FAIL — `parse_refinement` returns `[]` because REMOVE pass not implemented.

- [ ] **Step 3: Implement the REMOVE pass**

In `backend/app/services/refinement_service.py`, add a `_REMOVE_VERBS` constant and a second pass to `parse_refinement` (insert after the ADD pass, before `return ops`):

```python
_REMOVE_VERBS = r"remove|delete|drop|get rid of|no more|without"

# Inside parse_refinement, after the ADD pass:

    # REMOVE pass
    for room_type, keywords in ROOM_PATTERNS:
        for keyword in keywords:
            pattern = re.compile(
                r"\b(?:" + _REMOVE_VERBS + r")\s+"
                r"(?:(?P<all>all)\s+|the\s+|an?\s+|(?P<count>\d+|" + _COUNT_ALTS + r")\s+)?"
                + re.escape(keyword) + r"s?\b",
                re.IGNORECASE,
            )
            matches = list(pattern.finditer(text))
            if not matches:
                continue
            remove_all = False
            removed_count = 0
            for m in matches:
                if m.group("all"):
                    remove_all = True
                    break
                removed_count += _parse_count(m.group("count"))
            # Some REMOVE verbs imply "all" by themselves
            if not remove_all:
                for m in matches:
                    if re.search(r"\b(no more|without)\b", m.group(0), re.IGNORECASE):
                        remove_all = True
                        break
            ops.append(RemoveOp(
                room_type=room_type,
                count=None if remove_all else max(1, removed_count),
            ))
            for m in reversed(matches):
                text = _blank_span(text, m.start(), m.end())
            break
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && pytest app/tests/test_refinement_service.py -v
```
Expected: 7 tests PASS (4 ADD + 3 REMOVE).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/refinement_service.py backend/app/tests/test_refinement_service.py
git commit -m "feat(sprint8): add refinement parser REMOVE pass"
```

---

### Task 3: Parser — RESIZE verbs + combined / no-op

**Files:**
- Modify: `backend/app/services/refinement_service.py`
- Modify: `backend/app/tests/test_refinement_service.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/app/tests/test_refinement_service.py`:

```python
from app.services.refinement_service import ResizeOp  # add to existing import


def test_parse_resize_bigger():
    assert parse_refinement("make the kitchen bigger") == [ResizeOp(room_type="kitchen", factor=1.4)]


def test_parse_resize_smaller():
    assert parse_refinement("shrink the living room") == [
        ResizeOp(room_type="living_room", factor=0.7)
    ]


def test_parse_combined_add_remove():
    assert parse_refinement("add a bedroom and remove the office") == [
        AddOp(room_type="bedroom", count=1),
        RemoveOp(room_type="office", count=1),
    ]


def test_parse_returns_empty_for_unrecognised():
    assert parse_refinement("just chilling here") == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest app/tests/test_refinement_service.py::test_parse_resize_bigger -v
```
Expected: FAIL — returns `[]` because RESIZE pass not implemented.

- [ ] **Step 3: Implement the RESIZE pass**

In `backend/app/services/refinement_service.py`, add the RESIZE pass after REMOVE:

```python
_BIGGER_WORDS = r"bigger|larger|spacious"
_SMALLER_WORDS = r"smaller|compact"

# Inside parse_refinement, after the REMOVE pass:

    # RESIZE pass
    for room_type, keywords in ROOM_PATTERNS:
        for keyword in keywords:
            kw = re.escape(keyword)
            pattern = re.compile(
                r"\b(?:"
                r"make\s+(?:the\s+)?" + kw + r"s?\s+(?P<grow1>" + _BIGGER_WORDS + r")\b"
                r"|make\s+(?:the\s+)?" + kw + r"s?\s+(?P<shrink1>" + _SMALLER_WORDS + r")\b"
                r"|(?P<grow2>expand)\s+(?:the\s+)?" + kw + r"s?\b"
                r"|(?P<shrink2>shrink)\s+(?:the\s+)?" + kw + r"s?\b"
                r")",
                re.IGNORECASE,
            )
            matches = list(pattern.finditer(text))
            if not matches:
                continue
            m = matches[0]
            grew = bool(m.group("grow1") or m.group("grow2"))
            ops.append(ResizeOp(
                room_type=room_type,
                factor=1.4 if grew else 0.7,
            ))
            for hit in reversed(matches):
                text = _blank_span(text, hit.start(), hit.end())
            break
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && pytest app/tests/test_refinement_service.py -v
```
Expected: 11 tests PASS (4 ADD + 3 REMOVE + 4 new = 11 total parser tests; matches spec).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/refinement_service.py backend/app/tests/test_refinement_service.py
git commit -m "feat(sprint8): add refinement parser RESIZE pass"
```

---

### Task 4: Applier — `apply_refinement` for RESIZE + REMOVE + summary

**Files:**
- Modify: `backend/app/services/refinement_service.py`
- Modify: `backend/app/tests/test_refinement_service.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/app/tests/test_refinement_service.py`:

```python
import copy
from math import sqrt

from app.services.refinement_service import apply_refinement

SAMPLE_LAYOUT = {
    "version": "1.0",
    "metadata": {"prompt": "starter", "building_type": "apartment", "room_count": 3},
    "building": {"floorHeight": 3.2},
    "floors": [
        {
            "id": "floor_0",
            "name": "Ground Floor",
            "level": 0,
            "elevation": 0.0,
            "rooms": [
                {
                    "id": "r-1", "label": "Living Room", "roomType": "living_room",
                    "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                    "position": {"x": 2.5, "y": 1.5, "z": 2.5},
                    "size": {"w": 5.0, "h": 3.0, "d": 5.0},
                    "rotation": {"x": 0, "y": 0, "z": 0}, "color": "#818cf8",
                },
                {
                    "id": "r-2", "label": "Kitchen", "roomType": "kitchen",
                    "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                    "position": {"x": 8.0, "y": 1.5, "z": 2.0},
                    "size": {"w": 4.0, "h": 3.0, "d": 4.0},
                    "rotation": {"x": 0, "y": 0, "z": 0}, "color": "#34d399",
                },
                {
                    "id": "r-3", "label": "Office", "roomType": "office",
                    "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                    "position": {"x": 2.0, "y": 1.5, "z": 9.0},
                    "size": {"w": 4.0, "h": 3.0, "d": 4.0},
                    "rotation": {"x": 0, "y": 0, "z": 0}, "color": "#a78bfa",
                },
            ],
        }
    ],
    "rooms": [],
}
# Mirror floor rooms into top-level for sanity
SAMPLE_LAYOUT["rooms"] = [
    copy.deepcopy(r) for r in SAMPLE_LAYOUT["floors"][0]["rooms"]
]


def test_apply_resize_scales_w_and_d_by_sqrt_factor_and_keeps_xz():
    layout = copy.deepcopy(SAMPLE_LAYOUT)
    new_layout, summary = apply_refinement(layout, [ResizeOp(room_type="kitchen", factor=1.4)])

    kitchen = next(r for r in new_layout["rooms"] if r["id"] == "r-2")
    expected_w = round(4.0 * sqrt(1.4), 1)
    assert kitchen["size"]["w"] == expected_w
    assert kitchen["size"]["d"] == expected_w
    assert kitchen["position"]["x"] == 8.0
    assert kitchen["position"]["z"] == 2.0
    assert kitchen["position"]["y"] == 0.0 + kitchen["size"]["h"] / 2
    assert "Resized" in summary and "kitchen" in summary.lower()


def test_apply_remove_existing_room_returns_summary():
    layout = copy.deepcopy(SAMPLE_LAYOUT)
    new_layout, summary = apply_refinement(layout, [RemoveOp(room_type="office", count=1)])

    assert all(r["id"] != "r-3" for r in new_layout["rooms"])
    assert len(new_layout["rooms"]) == 2
    assert "Removed" in summary and "office" in summary.lower()


def test_apply_remove_missing_room_returns_empty_summary():
    layout = copy.deepcopy(SAMPLE_LAYOUT)
    new_layout, summary = apply_refinement(layout, [RemoveOp(room_type="balcony", count=1)])

    assert len(new_layout["rooms"]) == 3
    assert summary == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest app/tests/test_refinement_service.py::test_apply_resize_scales_w_and_d_by_sqrt_factor_and_keeps_xz -v
```
Expected: FAIL — `apply_refinement` not defined.

- [ ] **Step 3: Implement RESIZE, REMOVE, and the summary builder**

Append to `backend/app/services/refinement_service.py`:

```python
import copy
from math import sqrt

from app.services.layout_service import ROOM_COLORS
from app.services.prompt_service import ROOM_DEFAULTS


def _floor_elevation_for_level(layout: dict, level: int) -> float:
    for floor in layout.get("floors") or []:
        if floor.get("level") == level:
            return float(floor.get("elevation") or 0.0)
    return 0.0


def _rebuild_layout(layout: dict, rooms: list[dict]) -> dict:
    new = copy.deepcopy(layout)
    new["rooms"] = rooms
    floors = new.get("floors") or []
    for floor in floors:
        floor["rooms"] = [r for r in rooms if r.get("floorLevel") == floor.get("level")]
    metadata = new.setdefault("metadata", {})
    metadata["room_count"] = len(rooms)
    metadata["totalRooms"] = len(rooms)
    return new


def _label_for_summary(room_type: str) -> str:
    return ROOM_DEFAULTS[room_type]["label"].lower()


def apply_refinement(layout: dict, ops: list[RefinementOp]) -> tuple[dict, str]:
    rooms = [copy.deepcopy(r) for r in layout.get("rooms", [])]
    summary_parts: list[str] = []

    # Order: RESIZE -> REMOVE -> ADD
    for op in ops:
        if not isinstance(op, ResizeOp):
            continue
        matches = [r for r in rooms if r.get("roomType") == op.room_type]
        if not matches:
            continue
        f = sqrt(op.factor)
        for room in matches:
            room["size"]["w"] = round(room["size"]["w"] * f, 1)
            room["size"]["d"] = round(room["size"]["d"] * f, 1)
            elevation = _floor_elevation_for_level(layout, room.get("floorLevel") or 0)
            room["position"]["y"] = round(elevation + room["size"]["h"] / 2, 2)
        labels = ", ".join(m["label"] for m in matches)
        summary_parts.append(
            f"Resized {len(matches)} {_label_for_summary(op.room_type)}"
            + ("s" if len(matches) > 1 else "")
            + f" ({labels})"
        )

    for op in ops:
        if not isinstance(op, RemoveOp):
            continue
        matches = [r for r in rooms if r.get("roomType") == op.room_type]
        if not matches:
            continue
        to_remove = matches if op.count is None else matches[: op.count]
        remove_ids = {r["id"] for r in to_remove}
        rooms = [r for r in rooms if r["id"] not in remove_ids]
        label = _label_for_summary(op.room_type)
        summary_parts.append(
            f"Removed {len(to_remove)} {label}" + ("s" if len(to_remove) > 1 else "")
        )

    # ADD pass — implemented in Task 5 / Task 6

    new_layout = _rebuild_layout(layout, rooms)
    summary = ", ".join(summary_parts)
    if summary:
        summary = summary[0].upper() + summary[1:]
    return new_layout, summary
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && pytest app/tests/test_refinement_service.py -v
```
Expected: 14 PASS (11 parser + 3 new applier).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/refinement_service.py backend/app/tests/test_refinement_service.py
git commit -m "feat(sprint8): apply_refinement supports RESIZE and REMOVE"
```

---

### Task 5: Applier — `AddOp` placement (single-floor)

**Files:**
- Modify: `backend/app/services/refinement_service.py`
- Modify: `backend/app/tests/test_refinement_service.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/app/tests/test_refinement_service.py`:

```python
def test_apply_add_appends_room_without_moving_existing():
    layout = copy.deepcopy(SAMPLE_LAYOUT)
    before_by_id = {r["id"]: copy.deepcopy(r) for r in layout["rooms"]}

    new_layout, summary = apply_refinement(layout, [AddOp(room_type="bedroom", count=1)])

    # Append-only invariant: existing rooms identical
    existing = [r for r in new_layout["rooms"] if r["id"] in before_by_id]
    for room in existing:
        assert room == before_by_id[room["id"]]

    # New bedroom present
    new_rooms = [r for r in new_layout["rooms"] if r["id"] not in before_by_id]
    assert len(new_rooms) == 1
    bedroom = new_rooms[0]
    assert bedroom["roomType"] == "bedroom"
    assert bedroom["objectType"] == "room"
    assert bedroom["floorLevel"] == 0
    assert bedroom["size"] == {"w": 4.0, "h": 3.0, "d": 4.0}
    assert bedroom["color"] == "#f472b6"
    # Y bottom on the floor
    assert bedroom["position"]["y"] == bedroom["size"]["h"] / 2

    assert "Added" in summary and "bedroom" in summary.lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest app/tests/test_refinement_service.py::test_apply_add_appends_room_without_moving_existing -v
```
Expected: FAIL — new bedroom missing (ADD pass not implemented).

- [ ] **Step 3: Implement single-floor ADD**

In `backend/app/services/refinement_service.py`, add helper constants and helpers and the ADD pass. Insert near the top (after `_REMOVE_VERBS` / `_BIGGER_WORDS`):

```python
import uuid

_PUBLIC = frozenset({"living_room", "kitchen", "dining_room", "hallway"})
_PRIVATE = frozenset({"master_bedroom", "bedroom", "bathroom"})
_GAP = 1.0
_ZONE_GAP = 2.0
_FLOOR_HEIGHT = 3.2


def _zone_for(room_type: str) -> str:
    if room_type in _PUBLIC:
        return "public"
    if room_type in _PRIVATE:
        return "private"
    return "other"


def _next_position_in_zone(
    floor_rooms: list[dict],
    zone: str,
    new_w: float,
    new_d: float,
) -> tuple[float, float]:
    same_zone = [r for r in floor_rooms if _zone_for(r.get("roomType", "")) == zone]
    if same_zone:
        rightmost = max(r["position"]["x"] + r["size"]["w"] / 2 for r in same_zone)
        existing = same_zone[0]
        new_x = round(rightmost + _GAP + new_w / 2, 2)
        new_z = round(
            existing["position"]["z"] + (new_d - existing["size"]["d"]) / 2, 2
        )
        return new_x, new_z

    if not floor_rooms:
        return round(new_w / 2, 2), round(new_d / 2, 2)

    backmost = max(r["position"]["z"] + r["size"]["d"] / 2 for r in floor_rooms)
    new_z = round(backmost + _ZONE_GAP + new_d / 2, 2)
    return round(new_w / 2, 2), new_z


def _choose_floor_level(layout: dict, room_type: str, existing_rooms: list[dict]) -> int:
    floors = layout.get("floors") or []
    if len(floors) <= 1:
        return 0
    if room_type in {"living_room", "kitchen", "dining_room", "hallway", "garage"}:
        return 0
    if room_type == "bathroom":
        ground_has_bathroom = any(
            r["roomType"] == "bathroom" and r.get("floorLevel") == 0
            for r in existing_rooms
        )
        if not ground_has_bathroom:
            return 0
    # Upper floors round-robin by count of rooms on each upper floor
    upper_levels = [f["level"] for f in floors if f["level"] > 0]
    if not upper_levels:
        return 0
    counts = {
        level: sum(1 for r in existing_rooms if r.get("floorLevel") == level)
        for level in upper_levels
    }
    return min(upper_levels, key=lambda lvl: (counts[lvl], lvl))


def _make_room(room_type: str, layout: dict, existing_rooms: list[dict]) -> dict:
    defaults = ROOM_DEFAULTS[room_type]
    color = ROOM_COLORS.get(room_type, "#94a3b8")
    level = _choose_floor_level(layout, room_type, existing_rooms)
    elevation = _floor_elevation_for_level(layout, level)
    floor_rooms = [r for r in existing_rooms if r.get("floorLevel") == level]
    zone = _zone_for(room_type)
    new_x, new_z = _next_position_in_zone(floor_rooms, zone, defaults["w"], defaults["d"])
    floor_id = next(
        (f["id"] for f in layout.get("floors") or [] if f.get("level") == level),
        f"floor_{level}",
    )
    return {
        "id": str(uuid.uuid4()),
        "label": defaults["label"],
        "roomType": room_type,
        "objectType": "room",
        "floorId": floor_id,
        "floorLevel": level,
        "position": {
            "x": new_x,
            "y": round(elevation + 3.0 / 2, 2),
            "z": new_z,
        },
        "size": {"w": defaults["w"], "h": 3.0, "d": defaults["d"]},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "color": color,
    }
```

Then, inside `apply_refinement`, replace the placeholder ADD comment with the actual ADD pass (insert before `_rebuild_layout`):

```python
    for op in ops:
        if not isinstance(op, AddOp):
            continue
        added: list[dict] = []
        for _ in range(op.count):
            new_room = _make_room(op.room_type, layout, rooms)
            rooms.append(new_room)
            added.append(new_room)
        if added:
            label = _label_for_summary(op.room_type)
            summary_parts.append(
                f"Added {len(added)} {label}" + ("s" if len(added) > 1 else "")
            )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && pytest app/tests/test_refinement_service.py -v
```
Expected: 15 PASS (added one more).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/refinement_service.py backend/app/tests/test_refinement_service.py
git commit -m "feat(sprint8): apply_refinement single-floor ADD with append-only placement"
```

---

### Task 6: Applier — multi-floor ADD + combined summary

**Files:**
- Modify: `backend/app/tests/test_refinement_service.py`

(no production code changes required — `_choose_floor_level` already supports multi-floor)

- [ ] **Step 1: Write the failing tests**

Append to `backend/app/tests/test_refinement_service.py`:

```python
def _multi_floor_layout() -> dict:
    return {
        "version": "1.0",
        "metadata": {"prompt": "2-floor", "building_type": "house", "room_count": 1},
        "building": {"floorHeight": 3.2},
        "floors": [
            {
                "id": "floor_0",
                "name": "Ground Floor",
                "level": 0,
                "elevation": 0.0,
                "rooms": [
                    {
                        "id": "kit", "label": "Kitchen", "roomType": "kitchen",
                        "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                        "position": {"x": 2.0, "y": 1.5, "z": 2.0},
                        "size": {"w": 4.0, "h": 3.0, "d": 4.0},
                        "rotation": {"x": 0, "y": 0, "z": 0}, "color": "#34d399",
                    }
                ],
            },
            {
                "id": "floor_1",
                "name": "First Floor",
                "level": 1,
                "elevation": 3.2,
                "rooms": [],
            },
        ],
        "rooms": [
            {
                "id": "kit", "label": "Kitchen", "roomType": "kitchen",
                "objectType": "room", "floorId": "floor_0", "floorLevel": 0,
                "position": {"x": 2.0, "y": 1.5, "z": 2.0},
                "size": {"w": 4.0, "h": 3.0, "d": 4.0},
                "rotation": {"x": 0, "y": 0, "z": 0}, "color": "#34d399",
            }
        ],
    }


def test_apply_add_multi_floor_routes_bedroom_to_upper_level():
    layout = _multi_floor_layout()
    new_layout, _ = apply_refinement(layout, [AddOp(room_type="bedroom", count=1)])

    added = next(r for r in new_layout["rooms"] if r["roomType"] == "bedroom")
    assert added["floorLevel"] == 1
    assert added["floorId"] == "floor_1"
    # On a floor at elevation 3.2, the box bottom should sit at 3.2 → y = 3.2 + 1.5 = 4.7
    assert added["position"]["y"] == 4.7


def test_apply_combined_ops_summary():
    layout = copy.deepcopy(SAMPLE_LAYOUT)
    _, summary = apply_refinement(
        layout,
        [AddOp(room_type="bedroom", count=1), RemoveOp(room_type="office", count=1)],
    )
    assert summary == "Removed 1 office, Added 1 bedroom"
```

> **Why this order in the summary:** `apply_refinement` runs RESIZE → REMOVE → ADD, and `summary_parts` is appended in that order, so the final string starts with the operations that actually ran. The capitalisation step touches only the first character.

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest app/tests/test_refinement_service.py::test_apply_add_multi_floor_routes_bedroom_to_upper_level app/tests/test_refinement_service.py::test_apply_combined_ops_summary -v
```
Expected: PASS for the multi-floor test (logic already in place from Task 5). The combined-summary test should also PASS if the implementation matches; if it doesn't, fix the implementation to match the assertion (the assertion is the contract).

- [ ] **Step 3: If combined-summary test fails, fix in `apply_refinement`**

The expected output is `"Removed 1 office, Added 1 bedroom"`. If the implementation produces a different string, debug by re-reading the order of `summary_parts.append` calls — must be RESIZE, then REMOVE, then ADD, with `_label_for_summary` returning lowercase labels.

- [ ] **Step 4: Run the full suite**

```bash
cd backend && pytest app/tests/test_refinement_service.py -v
```
Expected: 17 PASS (15 from Tasks 1-5 + 2 new).

- [ ] **Step 5: Commit**

```bash
git add backend/app/tests/test_refinement_service.py
git commit -m "test(sprint8): cover multi-floor ADD placement and combined summary"
```

---

### Task 7: Backend — schemas + `POST /api/design/refine` endpoint

**Files:**
- Modify: `backend/app/schemas/design.py`
- Modify: `backend/app/api/designs/router.py`
- Modify: `backend/app/tests/test_designs.py`

- [ ] **Step 1: Write the failing endpoint tests**

Append to `backend/app/tests/test_designs.py`:

```python
async def test_refine_creates_new_version_and_logs_activity(client: AsyncClient):
    token = await _register_and_token(client, "refine@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Refine Project", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = project.json()["id"]
    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project_id, "prompt": "2 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token}"},
    )
    design_id = generated.json()["designId"]
    bedrooms_before = sum(
        1 for r in generated.json()["rooms"] if r["roomType"] == "bedroom"
    )

    response = await client.post(
        "/api/design/refine",
        json={"designId": design_id, "prompt": "add a bedroom"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    bedrooms_after = sum(1 for r in data["rooms"] if r["roomType"] == "bedroom")
    assert bedrooms_after == bedrooms_before + 1
    assert "Added 1 bedroom" in data["refinementSummary"]

    async with TestSessionLocal() as session:
        version_count = await session.scalar(
            select(func.count()).select_from(DesignVersion).where(
                DesignVersion.design_id == design_id
            )
        )
        assert version_count == 2
        latest = await session.scalar(
            select(DesignVersion)
            .where(DesignVersion.design_id == design_id)
            .order_by(DesignVersion.version_number.desc())
        )
        assert latest.version_type == "refined"
        assert "Added 1 bedroom" in (latest.change_summary or "")

        activity_actions = await session.scalars(select(ActivityLog.action))
        assert "design.refined" in activity_actions.all()


async def test_refine_unparsable_prompt_returns_422(client: AsyncClient):
    token = await _register_and_token(client, "refine-unparse@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Unparse", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project.json()["id"], "prompt": "2 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.post(
        "/api/design/refine",
        json={"designId": generated.json()["designId"], "prompt": "hello world"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert "Couldn't understand" in response.json()["error"]


async def test_refine_other_users_design_returns_403(client: AsyncClient):
    token_a = await _register_and_token(client, "refine-owner@example.com")
    token_b = await _register_and_token(client, "refine-intruder@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Owned", "description": None},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project.json()["id"], "prompt": "2 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    response = await client.post(
        "/api/design/refine",
        json={"designId": generated.json()["designId"], "prompt": "add a bedroom"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd backend && pytest app/tests/test_designs.py::test_refine_creates_new_version_and_logs_activity -v
```
Expected: 404 or 405 — endpoint not registered.

- [ ] **Step 3: Add the request/response schemas**

In `backend/app/schemas/design.py`, after the existing `SaveDesignRequest`:

```python
class RefineRequest(BaseModel):
    design_id: str = Field(..., alias="designId")
    prompt: str = Field(..., min_length=3)

    model_config = {"populate_by_name": True}


class RefineResponse(GenerateResponse):
    refinementSummary: str
```

- [ ] **Step 4: Implement the endpoint**

In `backend/app/api/designs/router.py`, add imports near the top:

```python
from datetime import datetime, timezone
from sqlalchemy import func, select

from app.models.design import Design
from app.models.design_version import DesignVersion
from app.schemas.design import RefineRequest, RefineResponse
from app.services.refinement_service import apply_refinement, parse_refinement
```

Then add the endpoint at the bottom of the file:

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
            detail=(
                "Couldn't understand the refinement. "
                "Try: 'add a bedroom', 'remove the office', 'make the kitchen bigger'."
            ),
        )

    new_layout, summary = apply_refinement(design.layout_json, ops)
    if not summary:
        raise HTTPException(
            status_code=422, detail="No matching rooms found for that change."
        )

    design.layout_json = new_layout
    design.updated_at = datetime.now(timezone.utc)

    max_version = await db.scalar(
        select(func.max(DesignVersion.version_number)).where(
            DesignVersion.design_id == design.id
        )
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

- [ ] **Step 5: Run the full backend suite**

```bash
cd backend && pytest -v 2>&1 | tail -20
```
Expected: 0 failures. Total = baseline + 17 refinement_service tests + 3 new endpoint tests.

Also confirm the three new endpoint tests specifically:

```bash
cd backend && pytest \
  app/tests/test_designs.py::test_refine_creates_new_version_and_logs_activity \
  app/tests/test_designs.py::test_refine_unparsable_prompt_returns_422 \
  app/tests/test_designs.py::test_refine_other_users_design_returns_403 -v
```
Expected: 3 PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/design.py backend/app/api/designs/router.py backend/app/tests/test_designs.py
git commit -m "feat(sprint8): POST /api/design/refine endpoint with version + activity log"
```

---

### Task 8: Frontend — install RTL + happy-dom + configure Vitest

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test-setup.ts`
- Modify: `frontend/tsconfig.json`

- [ ] **Step 1: Install dev dependencies**

```bash
cd frontend && npm install --save-dev \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  happy-dom
```

Expected: `package.json` updated, no peer dep errors. If npm warns about a peer-dep mismatch with React 18, re-run with `--legacy-peer-deps`.

- [ ] **Step 2: Create Vitest config**

Create `frontend/vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
  },
})
```

- [ ] **Step 3: Create test setup file**

Create `frontend/src/test-setup.ts`:

```typescript
import '@testing-library/jest-dom/vitest'
```

- [ ] **Step 4: Make sure TypeScript sees vitest globals + jest-dom matchers**

In `frontend/tsconfig.json`, add `"vitest/globals"` and `"@testing-library/jest-dom"` to `compilerOptions.types` (or to the existing `types` array if it exists). Read the file first to apply the minimal change:

```bash
cd frontend && cat tsconfig.json
```

Then edit so `compilerOptions.types` contains both entries. Example final shape:

```json
{
  "compilerOptions": {
    "...": "...",
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  }
}
```

If `tsconfig.json` does not currently have a `types` field, add it. If it has one, append the two entries without removing existing ones.

- [ ] **Step 5: Verify existing tests still pass**

```bash
cd frontend && npm test 2>&1 | tail -5
```
Expected: 20 PASS (same as baseline — config change should not break the existing pure-store tests).

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/src/test-setup.ts frontend/tsconfig.json
git commit -m "chore(sprint8): set up React Testing Library + happy-dom for frontend tests"
```

---

### Task 9: Frontend — `refineLayout` service function

**Files:**
- Modify: `frontend/src/services/design.service.ts`

- [ ] **Step 1: Implement `refineLayout` and its response type**

Append to `frontend/src/services/design.service.ts`:

```typescript
export interface RefineResponse extends GenerateResponse {
  refinementSummary: string
}

export async function refineLayout(
  designId: string,
  prompt: string,
): Promise<RefineResponse> {
  const { data } = await api.post<RefineResponse>('/api/design/refine', {
    designId,
    prompt,
  })
  return data
}
```

- [ ] **Step 2: Verify `tsc --noEmit` is clean**

```bash
cd frontend && npx tsc --noEmit
```
Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/design.service.ts
git commit -m "feat(sprint8): add refineLayout to design service"
```

---

### Task 10: Frontend — Generate/Refine toggle + submit dispatcher (with RTL test)

**Files:**
- Modify: `frontend/src/pages/Project/index.tsx`
- Create: `frontend/src/pages/Project/index.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/pages/Project/index.test.tsx`:

```tsx
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import ProjectPage from './index'
import api from '../../services/api'
import { useCanvasStore, INITIAL_ROOMS, DEFAULT_FLOOR, DEFAULT_FLOOR_HEIGHT } from '../../store/canvasStore'

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { name: 'Tester', email: 'tester@example.com' },
    logOut: vi.fn(),
  }),
}))

function renderProjectPage() {
  return render(
    <MemoryRouter initialEntries={['/projects/p1']}>
      <Routes>
        <Route path="/projects/:id" element={<ProjectPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

const PROJECT_FIXTURE = {
  id: 'p1',
  user_id: 'u1',
  title: 'Test',
  description: null,
  thumbnail_url: null,
  created_at: '2026-05-28T00:00:00Z',
  updated_at: '2026-05-28T00:00:00Z',
}

beforeEach(() => {
  vi.mocked(api.get).mockReset()
  vi.mocked(api.post).mockReset()
  useCanvasStore.setState({
    rooms: INITIAL_ROOMS.map((r) => ({
      ...r,
      floorId: DEFAULT_FLOOR.id,
      floorLevel: DEFAULT_FLOOR.level,
      position: { ...r.position },
      size: { ...r.size },
      rotation: { ...r.rotation },
    })),
    floors: [DEFAULT_FLOOR],
    selectedFloor: 0,
    floorHeight: DEFAULT_FLOOR_HEIGHT,
    designId: null,
    designVersionId: null,
    layoutMetadata: {},
    selectedId: null,
    snapToGrid: false,
    gridSize: 1,
    saveStatus: 'saved',
    lastSavedAt: null,
    activityLog: [],
  })
})


describe('ProjectPage refine flow', () => {
  it('disables the Refine toggle until a design exists', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/projects/p1') return { data: PROJECT_FIXTURE }
      if (url === '/api/design/project/p1/latest') {
        const err: any = new Error('not found')
        err.response = { status: 404 }
        throw err
      }
      throw new Error('unexpected URL ' + url)
    })

    renderProjectPage()

    const refineButton = await screen.findByRole('tab', { name: 'Refine' })
    expect(refineButton).toBeDisabled()
  })

  it('posts to /api/design/refine when Refine mode is active', async () => {
    const designFixture = {
      version: '1.0',
      designId: 'd1',
      designVersionId: 'v1',
      metadata: { prompt: 'starter', building_type: 'apartment', room_count: 1 },
      building: { floorHeight: 3.2 },
      floors: [{ id: 'floor_0', name: 'Ground', level: 0, elevation: 0, rooms: [] }],
      rooms: [],
    }
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/projects/p1') return { data: PROJECT_FIXTURE }
      if (url === '/api/design/project/p1/latest') return { data: designFixture }
      throw new Error('unexpected URL ' + url)
    })
    vi.mocked(api.post).mockImplementation(async (url: string) => {
      if (url === '/api/design/refine') {
        return {
          data: {
            ...designFixture,
            refinementSummary: 'Added 1 bedroom',
          },
        }
      }
      throw new Error('unexpected POST ' + url)
    })

    renderProjectPage()
    const user = userEvent.setup()

    const refineTab = await screen.findByRole('tab', { name: 'Refine' })
    await waitFor(() => expect(refineTab).not.toBeDisabled())
    await user.click(refineTab)

    const textarea = screen.getByLabelText('Layout prompt')
    await user.type(textarea, 'add a bedroom')
    const submitButton = screen.getByRole('button', { name: 'Refine' })
    await user.click(submitButton)

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/api/design/refine', {
        designId: 'd1',
        prompt: 'add a bedroom',
      }),
    )
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd frontend && npm test -- src/pages/Project/index.test.tsx
```
Expected: FAIL — no `tab` role "Refine" exists yet.

- [ ] **Step 3: Implement the toggle and submit dispatcher**

In `frontend/src/pages/Project/index.tsx`:

3a. Update imports to include `refineLayout`:

```tsx
import {
  generateLayout,
  getLatestProjectDesign,
  refineLayout,
  saveDesignLayout,
} from '../../services/design.service'
```

3b. Add the mode + summary state next to the existing state declarations:

```tsx
const [mode, setMode] = useState<'generate' | 'refine'>('generate')
const [refinementSummary, setRefinementSummary] = useState<string | null>(null)
const userPickedModeRef = useRef(false)
```

(Import `useRef` alongside `useState, useEffect` from React if it isn't already.)

3c. Auto-flip mode the first time `designId` becomes non-null:

```tsx
useEffect(() => {
  if (designId && mode === 'generate' && !userPickedModeRef.current) {
    setMode('refine')
  }
}, [designId, mode])
```

3d. Rename `handleGenerate` to `handleSubmit` and make it dispatch on mode:

```tsx
const handleSubmit = async () => {
  if (!prompt.trim()) return
  setGenerating(true)
  setGenerateError(null)
  setLayoutSaveError(null)
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
      apiErr.response?.data?.error ??
        (mode === 'refine'
          ? 'Refinement failed. Try a more specific change.'
          : 'Generation failed. Try a more detailed description.'),
    )
  } finally {
    setGenerating(false)
  }
}
```

Update the `onClick` of the existing submit button from `handleGenerate` to `handleSubmit`. Replace every other call site of `handleGenerate` with `handleSubmit`.

3e. Update the button label and add the segmented toggle. Replace the existing `{/* Prompt bar */}` block (currently:

```tsx
<div className="border-t border-gray-200 bg-white p-3 flex flex-col gap-1">
  <div className="flex gap-2 items-end">
    <textarea ... />
    <button ... onClick={handleGenerate} ...>
      {generating ? 'Generating…' : 'Generate'}
    </button>
  </div>
  ...
</div>
```

) with:

```tsx
<div className="border-t border-gray-200 bg-white p-3 flex flex-col gap-2">
  <div
    role="tablist"
    aria-label="Prompt mode"
    className="inline-flex w-fit rounded border border-gray-300 text-xs overflow-hidden"
  >
    <button
      role="tab"
      aria-selected={mode === 'generate'}
      className={`px-3 py-1 ${mode === 'generate' ? 'bg-indigo-500 text-white' : 'bg-white text-gray-700'}`}
      onClick={() => {
        userPickedModeRef.current = true
        setMode('generate')
      }}
    >
      Generate
    </button>
    <button
      role="tab"
      aria-selected={mode === 'refine'}
      disabled={!designId}
      title={designId ? '' : 'Generate a layout first'}
      className={`px-3 py-1 ${mode === 'refine' ? 'bg-indigo-500 text-white' : 'bg-white text-gray-700'} disabled:opacity-50 disabled:cursor-not-allowed`}
      onClick={() => {
        userPickedModeRef.current = true
        setMode('refine')
      }}
    >
      Refine
    </button>
  </div>
  <div className="flex gap-2 items-end">
    <textarea
      aria-label="Layout prompt"
      className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
      rows={2}
      placeholder={
        mode === 'refine'
          ? "Refine your layout… e.g. 'add a bedroom', 'remove the office', 'make the kitchen bigger'"
          : 'Describe your layout… e.g. 3 bedroom apartment with open kitchen and living room'
      }
      value={prompt}
      onChange={(e) => {
        setPrompt(e.target.value)
        setRefinementSummary(null)
      }}
      disabled={generating}
    />
    <button
      aria-busy={generating}
      className="bg-indigo-500 hover:bg-indigo-600 disabled:bg-indigo-300 text-white font-medium px-4 py-2 rounded-lg text-sm self-stretch"
      onClick={handleSubmit}
      disabled={generating || !prompt.trim()}
    >
      {generating
        ? mode === 'refine' ? 'Refining…' : 'Generating…'
        : mode === 'refine' ? 'Refine' : 'Generate'}
    </button>
  </div>
  {generateError && <p className="text-xs text-red-500">{generateError}</p>}
</div>
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd frontend && npm test -- src/pages/Project/index.test.tsx
```
Expected: 2 PASS.

- [ ] **Step 5: Type-check**

```bash
cd frontend && npx tsc --noEmit
```
Expected: zero errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Project/index.tsx frontend/src/pages/Project/index.test.tsx
git commit -m "feat(sprint8): Generate/Refine toggle and submit dispatcher on Project page"
```

---

### Task 11: Frontend — refinement summary banner

**Files:**
- Modify: `frontend/src/pages/Project/index.tsx`
- Modify: `frontend/src/pages/Project/index.test.tsx`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/pages/Project/index.test.tsx`:

```tsx
  it('renders and dismisses the refinement summary banner', async () => {
    const designFixture = {
      version: '1.0',
      designId: 'd1',
      designVersionId: 'v1',
      metadata: { prompt: 'starter', building_type: 'apartment', room_count: 1 },
      building: { floorHeight: 3.2 },
      floors: [{ id: 'floor_0', name: 'Ground', level: 0, elevation: 0, rooms: [] }],
      rooms: [],
    }
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/projects/p1') return { data: PROJECT_FIXTURE }
      if (url === '/api/design/project/p1/latest') return { data: designFixture }
      throw new Error('unexpected URL ' + url)
    })
    vi.mocked(api.post).mockResolvedValue({
      data: {
        ...designFixture,
        refinementSummary: 'Added 1 bedroom',
      },
    })

    renderProjectPage()
    const user = userEvent.setup()

    const refineTab = await screen.findByRole('tab', { name: 'Refine' })
    await waitFor(() => expect(refineTab).not.toBeDisabled())
    await user.click(refineTab)
    await user.type(screen.getByLabelText('Layout prompt'), 'add a bedroom')
    await user.click(screen.getByRole('button', { name: 'Refine' }))

    const banner = await screen.findByRole('status')
    expect(banner).toHaveTextContent('Added 1 bedroom')

    await user.click(screen.getByRole('button', { name: 'Dismiss' }))
    expect(screen.queryByRole('status')).toBeNull()
  })
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd frontend && npm test -- src/pages/Project/index.test.tsx
```
Expected: FAIL on the new test — `role="status"` banner not present.

- [ ] **Step 3: Implement the banner**

In `frontend/src/pages/Project/index.tsx`, inside the outer `flex flex-col` of the canvas + inspector + prompt bar block, **above** the prompt bar `<div>`, insert:

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

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd frontend && npm test -- src/pages/Project/index.test.tsx
```
Expected: 3 PASS.

- [ ] **Step 5: Run the full frontend suite**

```bash
cd frontend && npm test
```
Expected: 23 PASS (20 from baseline + 3 new).

- [ ] **Step 6: Type-check**

```bash
cd frontend && npx tsc --noEmit
```
Expected: zero errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/Project/index.tsx frontend/src/pages/Project/index.test.tsx
git commit -m "feat(sprint8): show dismissable refinement summary banner"
```

---

### Task 12: Update `CLAUDE.md` Sprint 8 status + final verification

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read the existing Sprint 8 block**

The current `CLAUDE.md` has:

```markdown
### Sprint 8 — Prompt Refinement ⏳ Not Started
```

- [ ] **Step 2: Replace with a Sprint 8 checklist**

Edit `CLAUDE.md`, replacing that single line with:

```markdown
### Sprint 8 — Prompt Refinement ✅ Complete

- [x] `refinement_service.parse_refinement` extracts AddOp / RemoveOp / ResizeOp from natural language
- [x] `refinement_service.apply_refinement` mutates the layout append-only (existing room positions preserved)
- [x] RESIZE → REMOVE → ADD application order; multi-floor ADD routes by Sprint 6 zone+floor rules
- [x] `POST /api/design/refine` returns the updated layout plus a `refinementSummary` string
- [x] Successful refine inserts `DesignVersion(version_type='refined', change_summary=summary)` and logs `design.refined`
- [x] 422 with help text when the prompt produces no ops; 422 with "No matching rooms" when ops are all no-ops
- [x] Generate / Refine segmented toggle on the bottom prompt bar; Refine disabled until a saved design exists
- [x] Summary banner above the prompt bar; auto-clears when the user types; ✕ to dismiss
- [x] React Testing Library + happy-dom configured for frontend RTL tests
- [x] 17 backend refinement service tests + 3 endpoint tests; 3 new frontend RTL tests
- [x] `npx tsc --noEmit` passes with zero errors
```

- [ ] **Step 3: Run all tests one more time to confirm green**

```bash
cd backend && pytest -v 2>&1 | tail -5
```
Expected: 0 failures. (Baseline 58 + 17 service tests + 3 endpoint tests = ~78 passing.)

```bash
cd frontend && npm test 2>&1 | tail -5
```
Expected: 23 PASS.

```bash
cd frontend && npx tsc --noEmit
```
Expected: zero errors.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(sprint8): mark Sprint 8 complete in CLAUDE.md"
```

- [ ] **Step 5: Push the branch**

```bash
git push -u origin sprint-8/prompt-refinement
```

Then open a PR on GitHub from `sprint-8/prompt-refinement` → `main`.

---

## Definition of Done (sprint-level)

- [ ] All 12 tasks above complete
- [ ] Backend test suite passes with zero failures
- [ ] Frontend test suite passes with zero failures
- [ ] `docker-compose up` shows the Generate/Refine flow end-to-end
- [ ] CLAUDE.md Sprint 8 block updated
- [ ] PR open from `sprint-8/prompt-refinement` → `main`
