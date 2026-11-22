"""Read translation units from XLIFF files.

Supports:
- XLIFF 1.2 (`<trans-unit>` with `<source>` / `<target>`)
- XLIFF 2.0 / 2.1 (`<unit>` → `<segment>` with `<source>` / `<target>`)
- SDL Trados `.sdlxliff` (segments as `<mrk mtype="seg">` inside `<seg-source>` / `<target>`)

Inline markup (`<g>`, `<x/>`, `<ph>`, `<bpt>`, `<pc>`, `<sc/>`, …) is kept as
short tag tokens such as `<x id="1"/>` so the placeholder check can compare
source and target. Standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass
import xml.etree.ElementTree as ET

# Inline elements that carry no translatable text of their own.
_EMPTY_INLINE = {"x", "bx", "ex", "ph", "it", "bpt", "ept", "sc", "ec", "cp", "sm", "em"}
# Inline elements that wrap translatable text.
_WRAPPING_INLINE = {"g", "pc", "mrk", "sub"}


@dataclass
class Unit:
    id: str
    source: str
    target: str
    state: str = ""
    note: str = ""


class XliffError(ValueError):
    pass


def _local(tag: str) -> str:
    """Tag name without its XML namespace."""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _text(elem: ET.Element | None) -> str:
    """Text of an element, with inline markup rendered as tag tokens."""
    if elem is None:
        return ""
    parts = [elem.text or ""]
    for child in elem:
        name = _local(child.tag)
        cid = child.get("id") or child.get("mid") or child.get("rid") or ""
        attr = f' id="{cid}"' if cid else ""
        if name == "mrk" and child.get("mtype") == "seg":
            parts.append(_text(child))           # Trados segment wrapper: keep only its content
        elif name in _WRAPPING_INLINE:
            parts.append(f"<{name}{attr}>{_text(child)}</{name}>")
        elif name in _EMPTY_INLINE:
            parts.append(f"<{name}{attr}/>")
        else:
            parts.append(_text(child))
        parts.append(child.tail or "")
    return "".join(parts).strip()


def _children(elem: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in elem if _local(c.tag) == name]


def _child(elem: ET.Element, name: str) -> ET.Element | None:
    found = _children(elem, name)
    return found[0] if found else None


def _segments(elem: ET.Element | None) -> dict[str, ET.Element]:
    """Trados segments (`<mrk mtype="seg" mid=…>`) inside an element, by mid."""
    if elem is None:
        return {}
    return {m.get("mid", ""): m for m in elem.iter()
            if _local(m.tag) == "mrk" and m.get("mtype") == "seg"}


def _notes(elem: ET.Element) -> str:
    notes = [n for n in elem.iter() if _local(n.tag) == "note" and (n.text or "").strip()]
    return " | ".join(n.text.strip() for n in notes)


def parse(data: bytes | str) -> list[Unit]:
    """Parse XLIFF content and return one Unit per translatable segment."""
    try:
        root = ET.fromstring(data.encode("utf-8") if isinstance(data, str) else data)
    except ET.ParseError as exc:
        raise XliffError(f"Not a valid XML file: {exc}") from exc
    if _local(root.tag) != "xliff":
        raise XliffError("Not an XLIFF file (root element is not <xliff>).")

    version = root.get("version", "")
    units: list[Unit] = []

    if version.startswith("2"):
        for unit in root.iter():
            if _local(unit.tag) != "unit":
                continue
            uid = unit.get("id", "")
            segs = _children(unit, "segment")
            for i, seg in enumerate(segs, 1):
                target = _child(seg, "target")
                units.append(Unit(
                    id=uid if len(segs) == 1 else f"{uid}.{seg.get('id') or i}",
                    source=_text(_child(seg, "source")),
                    target=_text(target),
                    state=seg.get("state", ""),
                    note=_notes(unit),
                ))
        return units

    # XLIFF 1.x, including Trados .sdlxliff
    for tu in root.iter():
        if _local(tu.tag) != "trans-unit" or tu.get("translate") == "no":
            continue
        uid = tu.get("id", "")
        target = _child(tu, "target")
        source_segs = _segments(_child(tu, "seg-source"))
        if source_segs:
            target_segs = _segments(target)
            for mid, src in source_segs.items():
                units.append(Unit(
                    id=f"{uid}.{mid}" if len(source_segs) > 1 else uid,
                    source=_text(src),
                    target=_text(target_segs.get(mid)),
                    note=_notes(tu),
                ))
        else:
            units.append(Unit(
                id=uid,
                source=_text(_child(tu, "source")),
                target=_text(target),
                state=target.get("state", "") if target is not None else "",
                note=_notes(tu),
            ))
    return units
