"""Dev-only debug renderer (workflow Step 1.4).

Usage:  python scripts/render_debug.py app/tests/fixtures/requirements/3bhk_adjacencies.json [out.svg]

Runs the MVP engine on a RequirementsSpec fixture and writes an SVG — the human
sanity check ("does this look like a home a person could walk through?") with
no frontend needed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.requirements import RequirementsSpec  # noqa: E402
from app.services.export.render import layout_to_svg  # noqa: E402
from app.services.layout_engine import generate_plan  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    fixture = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else fixture.with_suffix(".svg")

    spec = RequirementsSpec.model_validate_json(fixture.read_text())
    plan = generate_plan(spec)
    out.write_text(layout_to_svg(plan, title=fixture.stem))
    print(f"{fixture.stem}: {len(plan.rooms)} rooms, {len(plan.walls)} walls, "
          f"{len(plan.doors)} doors -> {out}")


if __name__ == "__main__":
    main()
