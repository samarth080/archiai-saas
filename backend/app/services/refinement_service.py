import copy
import re
from dataclasses import dataclass
from math import sqrt

from app.services.layout_service import ROOM_COLORS
from app.services.prompt_service import ROOM_DEFAULTS, ROOM_PATTERNS, WORD_TO_NUM


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
_REMOVE_VERBS = r"remove|delete|drop|get rid of|no more|without"
_BIGGER_WORDS = r"bigger|larger|spacious"
_SMALLER_WORDS = r"smaller|compact"


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

    return ops


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
