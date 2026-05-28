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
_REMOVE_VERBS = r"remove|delete|drop|get rid of|no more|without"


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

    return ops
