"""Thin wrapper: the code lives in repeat-common (repeat_common.fetch_dpg_atlas); see its docstring.

    python tools/fetch_dpg_atlas.py [options]
"""
import sys
from pathlib import Path

try:
    from repeat_common.fetch_dpg_atlas import main
except ImportError:   # not installed: use the sibling checkout
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "repeat-common" / "src"))
    from repeat_common.fetch_dpg_atlas import main

if __name__ == "__main__":
    main()
