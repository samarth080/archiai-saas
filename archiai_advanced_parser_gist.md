# ArchiAI — Advanced Keyword Parsing Engine
## Design Gist for Codex Implementation

> **Purpose:** This document is the complete design spec for upgrading `prompt_service.py`
> and `layout_service.py` from basic keyword matching to an advanced parsing engine.
> Implement everything described here without deviating from the existing module structure.
> All code is pure Python — no external AI APIs, no new heavy dependencies.

---

## 1. What Exists Today (Baseline)

The current `prompt_service.py` does roughly this:

```python
# Current behaviour (simplified)
def extract_requirements(prompt: str) -> dict:
    rooms = []
    for keyword in ROOM_KEYWORDS:
        if keyword in prompt.lower():
            rooms.append({"type": keyword, "count": extract_count(prompt, keyword)})
    floor_count = extract_floor_count(prompt)
    return {"rooms": rooms, "floors": floor_count}
```

**Problems with this:**
- If the user says "family home", they get zero rooms because none are named explicitly.
- "master bedroom with ensuite" creates two unrelated rooms with no spatial relationship.
- "large open plan kitchen-dining" gives the kitchen a scalar size bump but ignores the compound concept.
- "no garage" is ignored entirely.
- "modern minimalist apartment" carries no influence on layout decisions.

---

## 2. Target Architecture

Replace the single `extract_requirements` function with a **pipeline of 6 stages**.
Each stage is a pure function. They chain together. Each stage's output feeds the next.

```
prompt (str)
    │
    ▼
Stage 1: Normalise & Tokenise
    │  → cleaned_text, tokens
    ▼
Stage 2: Building Type Inference
    │  → building_type, style_hints, inferred_base_rooms
    ▼
Stage 3: Explicit Room Extraction
    │  → explicit_rooms (type, count, size_modifier)
    ▼
Stage 4: Merge & Deduplicate
    │  → merged_rooms (explicit overrides inferred)
    ▼
Stage 5: Relational Constraint Extraction
    │  → constraints (adjacency, exclusion, grouping)
    ▼
Stage 6: Size & Proportion Resolution
    │  → final_requirements (rooms with resolved m², constraints, metadata)
    ▼
layout_service.py (consumes final_requirements)
```

---

## 3. Stage 1 — Normalise & Tokenise

**File:** `backend/app/services/parser/normaliser.py`

```python
SYNONYMS = {
    # Room synonyms → canonical name
    "lounge": "living_room",
    "sitting room": "living_room",
    "reception": "living_room",
    "family room": "living_room",
    "drawing room": "living_room",
    "washroom": "bathroom",
    "toilet": "bathroom",
    "wc": "bathroom",
    "powder room": "bathroom",
    "half bath": "bathroom",
    "loo": "bathroom",
    "study": "office",
    "den": "office",
    "home office": "office",
    "work room": "office",
    "playroom": "kids_room",
    "nursery": "kids_room",
    "utility room": "laundry",
    "laundry room": "laundry",
    "scullery": "laundry",
    "pantry": "storage",
    "store room": "storage",
    "box room": "storage",
    "master bedroom": "master_bedroom",
    "master suite": "master_bedroom",
    "primary bedroom": "master_bedroom",
    "en suite": "ensuite",
    "ensuite bathroom": "ensuite",
    "attached bathroom": "ensuite",
    "double garage": "garage",
    "single garage": "garage",
    "carport": "garage",
    "mud room": "mudroom",
    "entry": "foyer",
    "entryway": "foyer",
    "hallway": "foyer",
    "entrance hall": "foyer",
    "great room": "living_room",          # open-plan large living
    "open plan": "open_plan_living",      # compound concept, handled in Stage 3
    "open-plan": "open_plan_living",
}

NUMBER_WORDS = {
    "one": 1, "a": 1, "an": 1, "single": 1,
    "two": 2, "double": 2, "dual": 2,
    "three": 3, "triple": 3,
    "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8,
}

def normalise(prompt: str) -> str:
    """
    Lowercase, replace synonym phrases with canonical names,
    expand number words to digits, strip extra whitespace.
    Process multi-word synonyms before single-word ones (longest match first).
    """
    text = prompt.lower().strip()
    # Sort synonyms by length descending so multi-word matches first
    for phrase, canonical in sorted(SYNONYMS.items(), key=lambda x: -len(x[0])):
        text = text.replace(phrase, canonical)
    for word, digit in NUMBER_WORDS.items():
        # Replace number words that appear before a room type
        text = re.sub(rf"\b{word}\b", str(digit), text)
    return text
```

---

## 4. Stage 2 — Building Type Inference

**File:** `backend/app/services/parser/building_inference.py`

This is the most impactful stage. It infers what kind of building is being described
and returns a **template of default rooms** that get used when the user hasn't named rooms explicitly.

### 4a. Building Type Taxonomy

```python
BUILDING_TYPES = {
    "studio_apartment":   {"keywords": ["studio", "studio apartment", "bedsit", "bachelor pad"], "floors": 1},
    "apartment":          {"keywords": ["apartment", "flat", "condo", "unit", "1bhk", "2bhk", "3bhk"], "floors": 1},
    "family_home":        {"keywords": ["family home", "family house", "house", "home", "bungalow", "cottage"], "floors": 1},
    "two_storey_home":    {"keywords": ["two storey", "two-storey", "two story", "2 storey", "two floor house"], "floors": 2},
    "townhouse":          {"keywords": ["townhouse", "town house", "terraced house", "row house"], "floors": 2},
    "villa":              {"keywords": ["villa", "mansion", "estate", "luxury home"], "floors": 2},
    "office":             {"keywords": ["office", "workspace", "coworking", "co-working", "commercial"], "floors": 1},
    "retail":             {"keywords": ["shop", "store", "retail", "boutique", "showroom"], "floors": 1},
    "restaurant":         {"keywords": ["restaurant", "cafe", "coffee shop", "bistro", "eatery", "diner"], "floors": 1},
    "school":             {"keywords": ["school", "classroom", "educational", "college", "university"], "floors": 2},
    "clinic":             {"keywords": ["clinic", "medical", "doctor", "dental", "healthcare"], "floors": 1},
    "hotel":              {"keywords": ["hotel", "motel", "inn", "bed and breakfast", "guesthouse"], "floors": 3},
    "warehouse":          {"keywords": ["warehouse", "industrial", "factory", "storage facility"], "floors": 1},
}
```

### 4b. Room Templates per Building Type

```python
# Each template is a list of (room_type, count, size_key)
# size_key references the SIZE_RULES table in Stage 6
BUILDING_TEMPLATES = {
    "studio_apartment": [
        ("open_plan_living", 1, "large"),   # combined living/sleeping/kitchen
        ("bathroom", 1, "small"),
    ],
    "apartment": [
        ("living_room", 1, "medium"),
        ("kitchen", 1, "medium"),
        ("bedroom", 2, "medium"),           # default 2-bed apartment
        ("bathroom", 1, "small"),
    ],
    "family_home": [
        ("living_room", 1, "large"),
        ("kitchen", 1, "medium"),
        ("dining_room", 1, "medium"),
        ("master_bedroom", 1, "large"),
        ("bedroom", 2, "medium"),
        ("bathroom", 2, "small"),
        ("foyer", 1, "small"),
    ],
    "two_storey_home": [
        # Ground floor
        ("living_room", 1, "large"),
        ("kitchen", 1, "large"),
        ("dining_room", 1, "medium"),
        ("foyer", 1, "small"),
        ("bathroom", 1, "small"),           # guest WC downstairs
        # Upper floor
        ("master_bedroom", 1, "large"),
        ("bedroom", 2, "medium"),
        ("bathroom", 1, "medium"),          # family bathroom upstairs
    ],
    "office": [
        ("reception", 1, "medium"),
        ("open_office", 1, "xlarge"),
        ("meeting_room", 2, "medium"),
        ("office", 1, "small"),             # private office
        ("kitchen", 1, "small"),            # breakroom
        ("bathroom", 2, "small"),
    ],
    "restaurant": [
        ("dining_area", 1, "xlarge"),
        ("kitchen", 1, "large"),
        ("bar", 1, "medium"),
        ("bathroom", 2, "small"),
        ("storage", 1, "small"),
    ],
    "retail": [
        ("sales_floor", 1, "xlarge"),
        ("storage", 1, "medium"),
        ("changing_room", 2, "small"),
        ("office", 1, "small"),
        ("bathroom", 1, "small"),
    ],
    # Add more as needed
}
```

### 4c. Style/Vibe Keywords

```python
STYLE_HINTS = {
    "minimalist":   {"open_plan_bias": True,  "room_count_modifier": -1, "ceiling_height": "high"},
    "modern":       {"open_plan_bias": True,  "room_count_modifier": 0,  "ceiling_height": "standard"},
    "traditional":  {"open_plan_bias": False, "room_count_modifier": 0,  "ceiling_height": "standard"},
    "luxury":       {"open_plan_bias": False, "room_count_modifier": +1, "size_upgrade": True},
    "compact":      {"open_plan_bias": True,  "room_count_modifier": -1, "size_downgrade": True},
    "spacious":     {"open_plan_bias": True,  "room_count_modifier": 0,  "size_upgrade": True},
    "cozy":         {"open_plan_bias": False, "room_count_modifier": -1, "size_downgrade": True},
    "studio":       {"open_plan_bias": True,  "room_count_modifier": -2},
    "open plan":    {"open_plan_bias": True},
    "open-plan":    {"open_plan_bias": True},
}
```

### 4d. BHK Pattern (Indian market specific — relevant for your userbase)

```python
BHK_PATTERN = re.compile(r'(\d)\s*bhk')

def extract_bhk(text: str) -> dict | None:
    """
    '2bhk' → {"bedrooms": 2, "hall": 1, "kitchen": 1}
    '3bhk' → {"bedrooms": 3, "hall": 1, "kitchen": 1}
    """
    match = BHK_PATTERN.search(text)
    if match:
        n = int(match.group(1))
        return {"bedroom": n, "living_room": 1, "kitchen": 1, "bathroom": max(1, n - 1)}
    return None
```

---

## 5. Stage 3 — Explicit Room Extraction

**File:** `backend/app/services/parser/room_extractor.py`

This stage finds rooms that the user *explicitly named*, including compound rooms and count extraction.

### 5a. Count Extraction

```python
COUNT_PATTERNS = [
    re.compile(r'(\d+)\s+{room}'),           # "3 bedrooms"
    re.compile(r'{room}s?\s+x\s*(\d+)'),     # "bedroom x 2"
    re.compile(r'{room}s?\s+\((\d+)\)'),     # "bedroom (2)"
]

def extract_count(text: str, room_type: str) -> int:
    """
    Try each COUNT_PATTERN. If none match but room_type is present, return 1.
    """
    for pattern in COUNT_PATTERNS:
        compiled = re.compile(pattern.pattern.replace('{room}', room_type))
        match = compiled.search(text)
        if match:
            return int(match.group(1))
    if room_type in text:
        return 1
    return 0
```

### 5b. Compound Room Detection

These are multi-word room concepts that should be treated as a single spatial unit:

```python
COMPOUND_ROOMS = {
    "open_plan_living":        ["living_room", "dining_room"],   # merge into one large room
    "kitchen_dining":          ["kitchen", "dining_room"],       # merge, remove separate dining
    "master_bedroom_ensuite":  ["master_bedroom", "ensuite"],    # keep separate but force adjacency
    "studio_unit":             ["bedroom", "living_room"],       # merge into open plan
    "home_gym_spa":            ["gym", "bathroom"],              # keep separate, force adjacency
}

COMPOUND_PATTERNS = {
    r"open[\s-]?plan\s+(kitchen[\s-]?dining|living[\s-]?dining|kitchen[\s-]?living)":
        "open_plan_living",
    r"kitchen[\s-]?diner":
        "kitchen_dining",
    r"master\s+bedroom\s+with\s+(en[\s-]?suite|attached\s+bath)":
        "master_bedroom_ensuite",
    r"kitchen[\s-]?dining[\s-]?(room)?":
        "kitchen_dining",
}
```

### 5c. Size Modifier Extraction

```python
SIZE_MODIFIERS = {
    "tiny": 0.5, "very small": 0.6, "small": 0.75, "compact": 0.75,
    "standard": 1.0, "normal": 1.0, "regular": 1.0,
    "medium": 1.0,
    "large": 1.3, "big": 1.3, "spacious": 1.4,
    "very large": 1.6, "huge": 1.8, "massive": 2.0, "grand": 1.8,
    "open plan": 1.5,   # open plan rooms are inherently larger
}

OCCUPANCY_SIZES = {
    # "seats N" / "for N people" → derives m² for dining/meeting rooms
    r"seats?\s+(\d+)":      lambda n: max(12, int(n) * 1.5),   # 1.5m² per person
    r"for\s+(\d+)\s+people": lambda n: max(12, int(n) * 1.5),
    r"(\d+)\s+car\s+garage": lambda n: int(n) * 14,            # 14m² per car bay
}
```

---

## 6. Stage 4 — Merge & Deduplicate

**File:** `backend/app/services/parser/merger.py`

Rules for merging inferred template rooms with explicitly extracted rooms:

```python
def merge_rooms(template_rooms: list, explicit_rooms: list) -> list:
    """
    Merge strategy:
    1. Start with template_rooms as the base.
    2. For every room in explicit_rooms:
       a. If the same room_type exists in template, REPLACE it (explicit wins on count + size).
       b. If it doesn't exist, ADD it.
    3. Remove any template rooms marked for exclusion (Stage 5 constraints).
    4. Apply open_plan_bias: if style says open_plan_bias=True, merge living+dining into open_plan_living.
    """
```

**Deduplication edge cases to handle:**
- `bedroom` (count=2) in template + `master_bedroom` (count=1) explicit → keep both, subtract 1 from bedroom count
- `bathroom` (count=2) in template + `ensuite` explicit → keep both (ensuite is distinct)
- `open_plan_living` compound → remove standalone `living_room` and `dining_room` if they were template defaults

---

## 7. Stage 5 — Relational Constraint Extraction

**File:** `backend/app/services/parser/constraint_extractor.py`

This stage extracts *spatial relationships* between rooms. The layout engine then uses
these to influence placement — adjacent rooms get placed next to each other.

### 7a. Adjacency Constraints

```python
ADJACENCY_PATTERNS = [
    # "X next to Y", "X beside Y", "X adjacent to Y"
    (r"(\w[\w\s]+?)\s+(?:next to|beside|adjacent to|adjoining|connected to)\s+([\w\s]+)", "ADJACENT"),
    # "X with ensuite" → master_bedroom ADJACENT ensuite
    (r"(\w[\w\s]+?)\s+with\s+(en[\s-]?suite|attached bath|private bath)", "ADJACENT"),
    # "X near Y", "X close to Y"
    (r"(\w[\w\s]+?)\s+(?:near|close to|by the|next to the)\s+([\w\s]+)", "NEAR"),
    # "kitchen-dining" compound → implicit adjacency
    (r"(\w+)[\s-](\w+)\s+(?:combo|combination|combined)", "ADJACENT"),
]

# Hardcoded implicit constraints (always applied regardless of prompt)
IMPLICIT_ADJACENCY = [
    ("master_bedroom", "ensuite"),      # ensuite is always next to master
    ("kitchen", "dining_room"),         # kitchen always near dining
    ("foyer", "living_room"),           # entry leads to living
    ("kitchen", "laundry"),             # utility proximity
    ("garage", "mudroom"),              # garage entry → mudroom
    ("office", "meeting_room"),         # office cluster
]
```

### 7b. Exclusion / Negation Constraints

```python
EXCLUSION_PATTERNS = [
    r"no\s+([\w\s]+)",                  # "no garage"
    r"without\s+(a\s+)?([\w\s]+)",     # "without a basement"
    r"don'?t\s+(?:want|need)\s+(a\s+)?([\w\s]+)",  # "don't need a study"
    r"exclude\s+([\w\s]+)",             # "exclude the basement"
    r"remove\s+([\w\s]+)",
]
```

### 7c. Zone Preferences

```python
ZONE_PATTERNS = {
    "ground floor": "ground",
    "first floor": "upper",
    "upstairs": "upper",
    "downstairs": "ground",
    "basement": "basement",
    "top floor": "top",
    "front of house": "public",
    "back of house": "private",
    "rear": "private",
    "street facing": "public",
}

# "bedrooms upstairs" → all bedroom-type rooms go to upper zone
ZONE_ASSIGNMENT_PATTERNS = [
    r"([\w\s]+(?:room|bedroom|bathroom|office|kitchen)s?)\s+(upstairs|downstairs|on the ground floor|on the first floor)",
]
```

---

## 8. Stage 6 — Size & Proportion Resolution

**File:** `backend/app/services/parser/size_resolver.py`

Converts size keys and modifiers into actual square metre values.
These are realistic architectural sizes, not arbitrary numbers.

```python
# Base sizes in m² — realistic defaults
BASE_SIZES = {
    "master_bedroom":    20.0,
    "bedroom":           12.0,
    "kids_room":         10.0,
    "ensuite":            5.0,
    "bathroom":           6.0,
    "living_room":       24.0,
    "open_plan_living":  40.0,
    "dining_room":       16.0,
    "kitchen":           14.0,
    "kitchen_dining":    28.0,  # merged
    "office":            12.0,
    "open_office":       50.0,
    "meeting_room":      20.0,
    "reception":         18.0,
    "foyer":              8.0,
    "laundry":            6.0,
    "storage":            4.0,
    "garage":            18.0,
    "gym":               20.0,
    "dining_area":       40.0,  # restaurant
    "kitchen":           30.0,  # restaurant kitchen (larger)
    "sales_floor":       60.0,
    "bar":               20.0,
    "mudroom":            5.0,
    "staircase":          6.0,
}

SIZE_KEY_MULTIPLIERS = {
    "small":  0.75,
    "medium": 1.0,
    "large":  1.3,
    "xlarge": 1.8,
}

def resolve_size(room_type: str, size_key: str, size_modifier: float, occupancy_m2: float | None) -> dict:
    """
    Returns {"area_m2": float, "width": float, "depth": float}
    
    Priority:
    1. occupancy_m2 if derived from "seats N" or "for N people"
    2. base_size × size_key_multiplier × size_modifier
    
    Width and depth are derived from area assuming a reasonable aspect ratio:
    - Square-ish rooms: ratio 1:1.2
    - Long rooms (dining, office): ratio 1:1.6
    - Corridors/foyer: ratio 1:2.5
    """
    LONG_ROOM_TYPES = {"dining_room", "kitchen", "office", "foyer", "corridor", "laundry"}
    
    base = BASE_SIZES.get(room_type, 12.0)
    area = occupancy_m2 or (base * SIZE_KEY_MULTIPLIERS.get(size_key, 1.0) * size_modifier)
    
    if room_type in LONG_ROOM_TYPES:
        ratio = 1.6
    else:
        ratio = 1.2
    
    width = round(math.sqrt(area / ratio), 1)
    depth = round(width * ratio, 1)
    
    return {"area_m2": round(area, 1), "width": width, "depth": depth}
```

---

## 9. Final Output Schema

What `prompt_service.py` should return after all 6 stages:

```python
@dataclass
class RoomRequirement:
    room_type: str          # canonical name, e.g. "master_bedroom"
    count: int
    area_m2: float
    width: float            # metres
    depth: float            # metres
    floor_preference: str   # "ground", "upper", "any"
    zone: str               # "public", "private", "service"
    size_key: str           # "small"/"medium"/"large"/"xlarge"
    is_compound: bool       # True if merged from compound pattern
    source: str             # "explicit" | "inferred" | "bhk"

@dataclass  
class AdjacencyConstraint:
    room_a: str
    room_b: str
    strength: str           # "MUST" (explicit) | "SHOULD" (implicit)

@dataclass
class ParsedRequirements:
    building_type: str
    style_hints: dict
    total_floors: int
    rooms: list[RoomRequirement]
    adjacency_constraints: list[AdjacencyConstraint]
    exclusions: list[str]   # room types to exclude
    raw_prompt: str
    confidence: float       # 0.0–1.0, based on how much was inferred vs explicit
```

---

## 10. Layout Service Changes

`layout_service.py` needs to consume the new `ParsedRequirements` and honour constraints.

### 10a. Adjacency-Aware Placement

```python
def place_with_adjacency(rooms: list[RoomRequirement], constraints: list[AdjacencyConstraint]) -> list[PlacedRoom]:
    """
    Algorithm:
    1. Build an adjacency graph from constraints.
    2. Find connected components — rooms that must cluster together.
    3. Place clusters first, then place remaining rooms.
    4. Within a cluster: place rooms side-by-side (share an edge).
    5. Between clusters: leave a 1m gap.
    
    Placement grid: snap all rooms to 0.5m grid.
    Zone separation: public zone (x < 0), private zone (x > 0), service zone (rear, z > zone_depth).
    """
```

### 10b. Multi-floor Distribution

```python
def assign_floors(rooms: list[RoomRequirement], total_floors: int) -> dict[int, list[RoomRequirement]]:
    """
    Rules (in priority order):
    1. Honour explicit floor_preference ("ground", "upper").
    2. Ground floor: living, kitchen, dining, foyer, service rooms, guest bathroom.
    3. Upper floors: bedrooms, ensuites, family bathroom, office.
    4. If total_floors == 1: everything on ground, ignore preferences.
    5. Distribute remaining rooms evenly across upper floors.
    """
```

---

## 11. File Structure

```
backend/app/services/
├── prompt_service.py          # existing — becomes the pipeline orchestrator
├── layout_service.py          # existing — update to consume ParsedRequirements
├── refinement_service.py      # existing — update to use new room taxonomy
└── parser/                    # NEW directory
    ├── __init__.py
    ├── normaliser.py           # Stage 1
    ├── building_inference.py   # Stage 2
    ├── room_extractor.py       # Stage 3
    ├── merger.py               # Stage 4
    ├── constraint_extractor.py # Stage 5
    ├── size_resolver.py        # Stage 6
    └── data/
        ├── building_templates.py   # BUILDING_TEMPLATES dict
        ├── synonyms.py             # SYNONYMS dict
        └── size_rules.py           # BASE_SIZES, SIZE_KEY_MULTIPLIERS
```

The `data/` files are pure dicts — easy to extend without touching logic.

---

## 12. Test Cases Codex Must Write

Every stage needs unit tests. Key cases:

```python
# Stage 2 — Building inference
assert infer_building_type("3bhk apartment") == "apartment"
assert infer_building_type("modern family home") == "family_home"
assert infer_building_type("coffee shop with seating for 20") == "restaurant"

# Stage 3 — Compound detection
assert "open_plan_living" in extract_rooms("open plan kitchen dining area")
assert "master_bedroom_ensuite" in extract_rooms("master bedroom with ensuite")

# Stage 5 — Exclusion
assert "garage" in extract_constraints("family home with no garage").exclusions

# Stage 5 — Adjacency
constraints = extract_constraints("kitchen next to the dining room")
assert any(c.room_a == "kitchen" and c.room_b == "dining_room" for c in constraints.adjacency)

# Stage 6 — Size resolution
room = resolve_size("master_bedroom", "large", 1.0, None)
assert room["area_m2"] == 26.0   # 20 * 1.3
assert room["width"] * room["depth"] == pytest.approx(room["area_m2"], rel=0.05)

# Full pipeline
result = parse_prompt("3 bedroom family home, modern, open plan kitchen-dining, master with ensuite, no garage")
assert result.building_type == "family_home"
assert result.total_floors == 1
assert sum(r.count for r in result.rooms if r.room_type == "bedroom") == 3
assert "garage" in result.exclusions
assert any(c.room_a == "master_bedroom" for c in result.adjacency_constraints)
assert any(r.room_type == "kitchen_dining" for r in result.rooms)  # compound merged
```

---

## 13. Backward Compatibility Rules

- `prompt_service.extract_requirements()` must keep the same function signature.
- The return value can be extended but must still produce `rooms[]` and `floors` at top level.
- `layout_service.generate_layout()` must still accept the old format as a fallback.
- All existing 56+ backend tests must still pass.
- Add new tests; do not delete old ones.

---

## 14. Implementation Order for Codex

Do these in sequence. Commit after each step passes its tests.

1. Create `backend/app/services/parser/` directory and data files
2. Implement and test `normaliser.py` (Stage 1)
3. Implement and test `building_inference.py` (Stage 2) with BHK support
4. Implement and test `room_extractor.py` (Stage 3) including compounds
5. Implement and test `merger.py` (Stage 4)
6. Implement and test `constraint_extractor.py` (Stage 5)
7. Implement and test `size_resolver.py` (Stage 6)
8. Wire all stages into `prompt_service.py` pipeline
9. Update `layout_service.py` for adjacency-aware placement and floor distribution
10. Run full test suite — all old tests must pass, new tests must pass
11. Update `refinement_service.py` to use the new room taxonomy (synonym normalisation)

---

## 15. Prompts This Should Handle Well (Acceptance Criteria)

After implementation, these prompts must produce sensible layouts:

| Prompt | Expected Behaviour |
|---|---|
| `"3bhk flat"` | 3 beds, living, kitchen, 2 baths — apartment template |
| `"modern minimalist studio"` | 1 open_plan room, 1 bath, no separate rooms |
| `"family home with no garage"` | Family template, garage excluded |
| `"restaurant seating 40"` | Dining 60m², kitchen 30m², bar, 2 baths |
| `"2 storey house, bedrooms upstairs"` | Beds on floor 2, living/kitchen on floor 1 |
| `"open plan kitchen dining living"` | Single merged room ~55m² |
| `"master bedroom with ensuite"` | Forced adjacency between the two |
| `"office with 3 meeting rooms and a breakroom"` | Office template + explicit overrides |
| `"cozy 1 bedroom cottage"` | Small sizes, 1 bed, compact layout |
| `"luxury villa with home gym and spa"` | Size upgrades, gym+bathroom adjacency |

---

## 16. Git Workflow — Branch and Push

**Codex must NOT push directly to `main`.** This follows the repo's existing contribution rules in `CLAUDE.md`.

### Branch naming
```bash
git checkout -b sprint-14/advanced-keyword-parser
```

### Commit after each stage (from Section 14)
```bash
# Example commit messages — follow this pattern exactly
git add backend/app/services/parser/
git commit -m "feat(parser): add Stage 1 normaliser with synonym expansion"

git commit -m "feat(parser): add Stage 2 building type inference with BHK support"

git commit -m "feat(parser): add Stage 3 compound room extraction"

git commit -m "feat(parser): add Stage 4 merge and deduplication"

git commit -m "feat(parser): add Stage 5 relational constraint extraction"

git commit -m "feat(parser): add Stage 6 size and proportion resolver"

git commit -m "feat(parser): wire all 6 stages into prompt_service pipeline"

git commit -m "feat(layout): update layout_service for adjacency-aware placement"

git commit -m "feat(parser): add Vastu compliance module and integration"

git commit -m "test(parser): full test suite — all old + new tests passing"
```

### Push the branch
```bash
git push origin sprint-14/advanced-keyword-parser
```

**Do not open a PR or merge into main.** The human (Udai) will review the branch,
run tests locally, and handle the PR themselves.

### What Codex must NOT do
- `git push origin main` — forbidden
- `git merge main` — do not merge anything
- Force push anything — forbidden
- Delete or rename existing files outside `backend/app/services/parser/` without flagging it

---

## 17. Vastu Shastra Compliance Feature

Vastu is a traditional Indian architectural system that defines directional rules for
room placement. It is a major trust signal for Indian users — many homeowners and
architects will not approve a layout that violates Vastu. This is a **significant
differentiator** for the Indian market and costs nothing to implement deterministically.

### 17a. What Vastu Is (Context for Codex)

Vastu Shastra maps a building's floor plan onto a compass grid (North/South/East/West
and their intermediates). Each direction is associated with specific rooms that are
considered auspicious or inauspicious. The goal is to place rooms in their "correct"
direction relative to the building's centre.

The building is divided into a 3×3 or 5×5 grid (Vastu Purusha Mandala). The centre
(Brahmasthan) must always remain open or be a courtyard/atrium.

### 17b. Core Directional Rules

```python
# Direction → preferred room types (in priority order)
VASTU_ROOM_DIRECTIONS = {
    "north":       ["office", "living_room", "treasury", "bathroom"],
    "northeast":   ["pooja_room", "meditation_room", "study", "water_feature"],  # most auspicious
    "east":        ["living_room", "dining_room", "bathroom", "children_room"],
    "southeast":   ["kitchen"],                # fire element, SE is the kitchen's only correct direction
    "south":       ["master_bedroom", "storage", "staircase"],
    "southwest":   ["master_bedroom", "heavy_storage"],  # most stable, owner's bedroom
    "west":        ["dining_room", "kids_room", "study"],
    "northwest":   ["guest_bedroom", "garage", "bathroom", "laundry"],
    "centre":      [],                         # MUST be open — Brahmasthan
}

# Rooms that are FORBIDDEN in certain directions
VASTU_FORBIDDEN = {
    "northeast": ["kitchen", "toilet", "staircase", "garage"],  # never pollute NE
    "southeast": ["bedroom", "master_bedroom"],                  # fire direction, no sleep
    "southwest": ["kitchen", "bathroom", "main_entrance"],       # unstable for fire/water
    "centre":    ["bedroom", "kitchen", "bathroom", "staircase"], # Brahmasthan must be open
}

# Main entrance preferred directions (most to least auspicious)
ENTRANCE_DIRECTIONS = ["north", "northeast", "east", "northwest"]
ENTRANCE_FORBIDDEN  = ["south", "southwest"]
```

### 17c. Vastu Keywords — Trigger Detection

The Vastu module only activates when the user signals it. Do not apply Vastu rules silently.

```python
VASTU_TRIGGER_KEYWORDS = [
    "vastu", "vaastu", "vastu shastra", "vastu compliant", "vastu friendly",
    "vastu approved", "as per vastu", "according to vastu",
    "vastu based", "vastu layout",
]

def is_vastu_requested(prompt: str) -> bool:
    text = prompt.lower()
    return any(kw in text for kw in VASTU_TRIGGER_KEYWORDS)
```

### 17d. Vastu Compliance Module

**File:** `backend/app/services/parser/vastu.py`

```python
@dataclass
class VastuViolation:
    room_type: str
    current_direction: str
    recommended_direction: str
    severity: str          # "critical" | "moderate" | "minor"
    message: str           # human-readable explanation

@dataclass
class VastuResult:
    is_requested: bool
    violations: list[VastuViolation]
    suggestions: list[str]        # plain English improvement suggestions
    compliance_score: float       # 0.0 (all wrong) to 1.0 (fully compliant)
    brahmasthan_clear: bool        # is the centre of the layout open?

def get_vastu_direction(room_position: dict, building_centre: dict) -> str:
    """
    Given a room's (x, z) position and the building's centre (x, z),
    return the compass direction: "north", "northeast", "east", etc.
    
    Use 8-direction mapping (45° sectors each).
    Coordinate system: in Three.js/R3F, -Z is north, +Z is south, +X is east, -X is west.
    """
    dx = room_position["x"] - building_centre["x"]
    dz = room_position["z"] - building_centre["z"]
    angle = math.degrees(math.atan2(dx, -dz)) % 360  # 0° = north, clockwise
    
    directions = [
        "north", "northeast", "east", "southeast",
        "south", "southwest", "west", "northwest"
    ]
    index = round(angle / 45) % 8
    return directions[index]

def check_vastu_compliance(placed_rooms: list, building_bounds: dict) -> VastuResult:
    """
    After layout_service places rooms, run this check.
    Returns VastuResult with violations, suggestions, and score.
    
    Score calculation:
    - Start at 1.0
    - Subtract 0.15 for each critical violation
    - Subtract 0.08 for each moderate violation
    - Subtract 0.03 for each minor violation
    - Clamp to [0.0, 1.0]
    """

def apply_vastu_placement(
    rooms: list[RoomRequirement],
    constraints: list[AdjacencyConstraint],
    building_bounds: dict,
) -> list[RoomRequirement]:
    """
    Modify room zone/floor_preference hints to nudge placement toward
    Vastu-correct directions BEFORE layout_service does placement.
    
    This does not guarantee Vastu compliance (adjacency constraints may conflict)
    but makes the initial placement attempt directionally correct.
    
    Priority order when conflicts arise:
    1. Explicit user constraints (from Stage 5) always win
    2. Adjacency constraints (master_bedroom+ensuite must stay together)
    3. Vastu direction preferences
    4. Zone (public/private) defaults
    """
```

### 17e. Special Vastu Rooms

Some rooms are India-specific and only appear in Vastu-triggered layouts:

```python
VASTU_SPECIAL_ROOMS = {
    "pooja_room": {
        "area_m2": 6.0,
        "preferred_direction": "northeast",
        "forbidden_directions": ["south", "southwest", "southeast"],
        "description": "Prayer/worship room",
    },
    "meditation_room": {
        "area_m2": 8.0,
        "preferred_direction": "northeast",
        "forbidden_directions": ["southeast"],
        "description": "Meditation or yoga space",
    },
    "tulsi_courtyard": {
        "area_m2": 4.0,
        "preferred_direction": "northeast",
        "description": "Open courtyard for Tulsi plant",
    },
    "brahmasthan": {
        "area_m2": 0.0,   # open space, no room placed here
        "preferred_direction": "centre",
        "description": "Central open space — must remain unbuilt",
    },
}

VASTU_ROOM_TRIGGERS = {
    "pooja": "pooja_room",
    "puja": "pooja_room",
    "prayer room": "pooja_room",
    "mandir": "pooja_room",
    "temple room": "pooja_room",
    "meditation": "meditation_room",
    "yoga room": "meditation_room",
    "courtyard": "tulsi_courtyard",
    "aangan": "tulsi_courtyard",
}
```

### 17f. Integration into the Pipeline

Add Vastu as an optional Stage 7, after Stage 6:

```
Stage 6: Size Resolution
    │
    ▼
Stage 7: Vastu (only if is_vastu_requested == True)
    │  → modifies room zone/direction hints
    │  → adds pooja_room if not present and Vastu requested
    │  → adds VastuResult to ParsedRequirements
    ▼
layout_service.py
    │  → after placement, runs check_vastu_compliance()
    │  → attaches VastuResult to layout metadata
    ▼
Frontend: shows Vastu compliance badge + violations panel
```

### 17g. Frontend: Vastu Compliance UI

The layout insights panel (already exists from Sprint 11) should show:

```
┌─────────────────────────────────────┐
│  🕉  Vastu Compliance               │
│  Score: 78%  ████████░░             │
│                                     │
│  ✅ Kitchen — Southeast (correct)   │
│  ✅ Pooja room — Northeast (correct)│
│  ⚠️  Master bedroom — East          │
│     Recommended: Southwest          │
│  ❌ Bathroom — Northeast            │
│     Avoid placing bathrooms in NE   │
└─────────────────────────────────────┘
```

Add a `VastuPanel` component in `frontend/src/components/VastuPanel.tsx`.
It reads `layout.metadata.vastu` from the layout JSON.
Show it only when `layout.metadata.vastu.is_requested === true`.

### 17h. Vastu Test Cases

```python
# Trigger detection
assert is_vastu_requested("3bhk vastu compliant home") == True
assert is_vastu_requested("modern apartment") == False

# Direction mapping (Three.js coordinate space)
assert get_vastu_direction({"x": 5, "z": 0}, {"x": 0, "z": 0}) == "east"
assert get_vastu_direction({"x": 0, "z": -5}, {"x": 0, "z": 0}) == "north"
assert get_vastu_direction({"x": 5, "z": 5}, {"x": 0, "z": 0}) == "southeast"

# Violation detection
violations = check_vastu_compliance(placed_rooms_with_kitchen_in_north, bounds).violations
assert any(v.room_type == "kitchen" and v.severity == "critical" for v in violations)

# Pooja room auto-added when Vastu requested and not explicit
result = parse_prompt("3bhk vastu compliant home")
assert any(r.room_type == "pooja_room" for r in result.rooms)

# Full compliance score
result = check_vastu_compliance(ideal_vastu_layout, bounds)
assert result.compliance_score >= 0.85
```

### 17i. Important Implementation Notes for Codex

- **Never apply Vastu silently.** Only activate when `is_vastu_requested` is True.
- The `brahmasthan` (centre) must be computed from the building's total bounding box, not the first floor only.
- In multi-floor buildings, Vastu direction rules apply to the **ground floor layout**. Upper floors follow the same directional grid but are less strictly enforced.
- Vastu compliance is a **hint system**, not a hard constraint. If adjacency constraints conflict with Vastu, adjacency wins and the violation is reported — not silently ignored.
- Do not rename or restructure existing layout JSON keys. Add `vastu` as a new key inside `metadata`.
- The compliance score and violations are **read-only output** — the user can choose to act on them or ignore them.
