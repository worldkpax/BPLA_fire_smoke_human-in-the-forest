"""Thin wrapper that dispatches to module or ground runtime."""

from __future__ import annotations

import os

ROLE_ENV = "FIRE_UAV_ROLE"


def _is_module_role() -> bool:
    role = os.environ.get(ROLE_ENV, "ground").lower()
    return role.startswith("module")


def main() -> None:  # noqa: D401
    if _is_module_role():
        from fire_uav.module_app.main_module import main as module_main

        module_main()
    else:
        from fire_uav.ground_app.main_ground import main as ground_main

        ground_main()


if __name__ == "__main__":  # pragma: no cover
    main()
