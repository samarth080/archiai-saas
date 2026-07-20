"""
Regression suite for generated-marker sanity.

The partition-wall generator used to test the WRONG axis's gap when deciding
adjacency: any two rooms in the same row counted as adjacent no matter how
far apart, spraying phantom walls and "Interior Door" markers straight
through the rooms in between (the "random tan rectangles" bug). These tests
pin the fixed behaviour end to end:

- doors and partition walls only on true shared boundaries, never inside a
  room's interior
- at most one door between the same two rooms
- service rooms open onto corridor/private neighbours, not the dining room
- no column/furniture/generic markers in generated output
- save/reload keeps door/window/wall counts identical
"""
from collections import Counter

from httpx import AsyncClient

from app.services.layout_service import (
    _generate_partition_walls,
    _room_bounds,
    generate_layout,
)
from app.services.prompt_service import detect_building_type, extract_rooms


PROMPTS = [
    "3 bedroom house with 2 bathrooms and a kitchen",
    "office with reception, open workspace, 4 meeting rooms, a kitchen and 2 restrooms",
    "clinic with reception, waiting room, 3 consultation rooms and a bathroom",
    "apartment with living room, kitchen, dining room and bathroom",
]


def _generate(prompt: str, total_floors: int = 1) -> dict:
    return generate_layout(
        extract_rooms(prompt),
        prompt=prompt,
        building_type=detect_building_type(prompt),
        total_floors=total_floors,
    )


def _objects(layout: dict) -> list[dict]:
    return [obj for floor in layout["floors"] for obj in floor["rooms"]]


def _rooms(layout: dict) -> list[dict]:
    return [o for o in _objects(layout) if o["objectType"] == "room"]


def _interior_doors(layout: dict) -> list[dict]:
    return [o for o in _objects(layout) if o.get("label") == "Interior Door"]


def _strictly_inside(obj: dict, room: dict, margin: float = 0.2) -> bool:
    x1, x2, z1, z2 = _room_bounds(room)
    px, pz = obj["position"]["x"], obj["position"]["z"]
    return x1 + margin < px < x2 - margin and z1 + margin < pz < z2 - margin


def _touching_rooms(obj: dict, rooms: list[dict], eps: float = 0.1) -> list[str]:
    px, pz = obj["position"]["x"], obj["position"]["z"]
    touched = []
    for room in rooms:
        if room.get("floorLevel") != obj.get("floorLevel"):
            continue
        x1, x2, z1, z2 = _room_bounds(room)
        if x1 - eps <= px <= x2 + eps and z1 - eps <= pz <= z2 + eps:
            touched.append(room["id"])
    return touched


def test_no_door_or_wall_sits_inside_a_room():
    for prompt in PROMPTS:
        layout = _generate(prompt)
        rooms = _rooms(layout)
        markers = [
            o for o in _objects(layout)
            if o.get("label") in ("Interior Door", "Partition Wall")
        ]
        for marker in markers:
            offenders = [
                room["label"] for room in rooms
                if room.get("floorLevel") == marker.get("floorLevel")
                and _strictly_inside(marker, room)
            ]
            assert not offenders, (
                f"{prompt!r}: {marker['label']} at {marker['position']} lies inside {offenders}"
            )


def test_at_most_one_door_between_the_same_two_rooms():
    for prompt in PROMPTS:
        layout = _generate(prompt)
        rooms = _rooms(layout)
        pair_counts: Counter = Counter()
        for door in _interior_doors(layout):
            touched = tuple(sorted(_touching_rooms(door, rooms)))
            # A valid interior door sits on the boundary of exactly two rooms.
            assert len(touched) == 2, (
                f"{prompt!r}: door at {door['position']} touches {len(touched)} rooms"
            )
            pair_counts[touched] += 1
        duplicates = {pair: n for pair, n in pair_counts.items() if n > 1}
        assert not duplicates, f"{prompt!r}: duplicate doors {duplicates}"


def test_door_count_stays_proportionate_to_room_count():
    """A 10-room plan needs ~a door per room, not one per room pair."""
    for prompt in PROMPTS:
        layout = _generate(prompt)
        room_count = len(_rooms(layout))
        door_count = len(_interior_doors(layout))
        assert door_count <= room_count + 3, (
            f"{prompt!r}: {door_count} interior doors for {room_count} rooms"
        )


def test_generated_layouts_contain_no_placeholder_marker_types():
    allowed = {"room", "wall", "door", "window", "stair"}
    for prompt in PROMPTS:
        types = {o["objectType"] for o in _objects(_generate(prompt, total_floors=2))}
        assert types <= allowed, f"{prompt!r}: unexpected object types {types - allowed}"


def test_windows_and_entry_sit_on_the_boundary_walls():
    layout = _generate(PROMPTS[0])
    footprint = layout["floors"][0]["footprint"]
    x1, z1 = footprint["x"], footprint["z"]
    x2, z2 = x1 + footprint["w"], z1 + footprint["d"]
    exterior = [
        o for o in _objects(layout)
        if o.get("label") in ("Exterior Window", "Entry Door")
    ]
    assert exterior
    for marker in exterior:
        px, pz = marker["position"]["x"], marker["position"]["z"]
        distance = min(abs(px - x1), abs(px - x2), abs(pz - z1), abs(pz - z2))
        assert distance <= 0.2, (
            f"{marker['label']} floats {distance:.2f} m away from the nearest wall"
        )


def _cell(id_: str, room_type: str, x: float, z: float, w: float, d: float) -> dict:
    return {
        "id": id_,
        "label": id_,
        "roomType": room_type,
        "objectType": "room",
        "floorLevel": 0,
        "position": {"x": x, "y": 1.5, "z": z},
        "size": {"w": w, "h": 3.0, "d": d},
    }


def test_service_room_opens_into_private_neighbour_not_public():
    # 2x2 grid: bathroom touches both a dining room (public) and a bedroom
    # (private) — it must become an ensuite, not open into the dining room.
    # Every room stays reachable without passing through the bathroom, so no
    # connectivity-completion door is needed there either.
    rooms = [
        _cell("living", "living_room", 2.0, 2.0, 4.0, 4.0),
        _cell("dining", "dining_room", 6.0, 2.0, 4.0, 4.0),
        _cell("bedroom", "bedroom", 2.0, 6.0, 4.0, 4.0),
        _cell("bathroom", "bathroom", 6.0, 6.0, 4.0, 4.0),
    ]
    markers = _generate_partition_walls(
        rooms, floor_id="floor_0", floor_level=0, elevation=0.0
    )
    doors = [m for m in markers if m["label"] == "Interior Door"]
    bath_doors = [d for d in doors if "bathroom" in _touching_rooms(d, rooms)]
    assert len(bath_doors) == 1
    assert set(_touching_rooms(bath_doors[0], rooms)) == {"bathroom", "bedroom"}


def test_far_apart_same_row_rooms_get_no_wall_or_door():
    # The original bug: two rooms in the same row with a third between them
    # produced a phantom wall + door through the middle room.
    rooms = [
        _cell("left", "living_room", 2.0, 2.0, 4.0, 4.0),
        _cell("middle", "kitchen", 6.0, 2.0, 4.0, 4.0),
        _cell("right", "dining_room", 10.0, 2.0, 4.0, 4.0),
    ]
    markers = _generate_partition_walls(
        rooms, floor_id="floor_0", floor_level=0, elevation=0.0
    )
    for marker in markers:
        assert not _strictly_inside(marker, rooms[1]), (
            f"{marker['label']} at {marker['position']} crosses the middle room"
        )
    # Exactly the two true boundaries get walls: left|middle and middle|right.
    walls = [m for m in markers if m["label"] == "Partition Wall"]
    assert len(walls) == 2


async def _register_and_token(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Marker User", "email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


async def test_save_and_reload_do_not_duplicate_markers(client: AsyncClient):
    token = await _register_and_token(client, "markers@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    project = await client.post(
        "/api/projects",
        json={"title": "Marker Project", "description": None},
        headers=headers,
    )
    project_id = project.json()["id"]

    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project_id, "prompt": "3 bedroom house with 2 bathrooms and a kitchen"},
        headers=headers,
    )
    assert generated.status_code == 200
    layout = generated.json()
    counts_before = Counter(o["objectType"] for o in layout["rooms"])

    saved = await client.put(
        f"/api/design/{layout['designId']}",
        json={"layout": {k: v for k, v in layout.items() if k != "alternatives"}},
        headers=headers,
    )
    assert saved.status_code == 200

    latest = await client.get(f"/api/design/project/{project_id}/latest", headers=headers)
    assert latest.status_code == 200
    counts_after = Counter(o["objectType"] for o in latest.json()["rooms"])

    assert counts_after == counts_before
