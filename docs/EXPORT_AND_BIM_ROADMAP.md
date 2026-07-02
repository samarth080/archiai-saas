# Export & BIM Roadmap

How ArchiAI moves from "download a canvas image" to real interchange formats.
Sequenced so each step is shippable on its own. Formats past SVG/PDF are gated
behind billing entitlements (`dxf_export`, `bim_export`).

## Now (shipped / near-term)

- **PNG image** of the canvas (Sprint 12) — `preserveDrawingBuffer` on the R3F
  canvas.
- **PDF summary** (Sprint 12) — lightweight project summary via jsPDF.

## Planned (Phase 7 — one exporter interface)

A single server-side exporter interface, format-by-format:

1. **SVG floor plan** — 2D plan projection of the layout (walls, doors, windows,
   spaces, dimension lines) as layered SVG.
2. **PDF sheet** — the SVG placed on a titled sheet with a title block and scale
   bar.
3. **DXF** via `ezdxf` — one layer per element class
   (`A-WALL`, `A-DOOR`, `A-GLAZ`, `A-AREA`, `FURN`, `A-ANNO-DIMS`), real-world
   units and scale. Opens in any DXF viewer/CAD. **Gated on `dxf_export`.**
4. **glTF / GLB** — the existing 3D scene exported for web/AR viewers.

`ezdxf` is a new dependency to be flagged before adding (per CLAUDE.md).

## Later (Phase 8 — BIM-ready model + mapping)

Not a certified IFC writer in this pass — a **model + documented mapping only**:

- An element schema carrying `category, level, geometry, material,
  relationships (hosted_by / bounded_by / …), quantities`.
- Schedules (space / door / window) reconciled against geometry counts.
- A documented mapping to IFC (`IfcSpace`, `IfcWallStandardCase`, `IfcDoor`,
  `IfcWindow`, `IfcStair`, `IfcFurnishingElement`) and Revit-interop notes.
- **Gated on `bim_export`.**

## Explicit non-goals (this horizon)

- **No native DWG.** DWG is proprietary; the DXF exporter is designed so a
  DWG-via-converter/plugin path can be added later without reworking it.
- **No certified IFC writer** — mapping doc + element model only.

## Dependencies on other work

Real DXF/SVG/BIM output needs true wall/door/window *topology* (openings cut
into walls, shared-wall dedup) from the graph-driven planning phases (Pillar A /
Phases 4–5), not the current flat-box + marker geometry. Export fidelity tracks
that geometry work.
