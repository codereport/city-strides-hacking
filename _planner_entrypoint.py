"""Run canonical data scripts from the private route-planner submodule."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PLANNER_ROOT = ROOT / "city-strides-route-planner"


def run_planner_script(script_name: str) -> None:
    """Delegate a legacy repository-root entry point to the planner script."""

    script = PLANNER_ROOT / script_name
    if not script.is_file():
        raise SystemExit(
            "The city-strides-route-planner submodule is required. Initialize it with:\n"
            "  git -c submodule.city-strides-route-planner.update=checkout "
            "submodule update --init city-strides-route-planner"
        )

    sys.path.insert(0, str(PLANNER_ROOT))
    sys.argv[0] = str(script)
    runpy.run_path(str(script), run_name="__main__")
