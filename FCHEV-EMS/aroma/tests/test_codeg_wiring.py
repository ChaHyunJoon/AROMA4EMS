"""Static wiring checks for the battery_degradation co-objective change.
Run: python3 -m pytest tests/test_codeg_wiring.py  (or: python3 tests/test_codeg_wiring.py)
"""
import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_no_battery_usage_identifier_remains():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for path in glob.glob(os.path.join(here, "*.py")):
        with open(path) as f:
            assert "battery_usage" not in f.read(), f"battery_usage still in {path}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print(f"PASS {name}")
    print("ALL PASS")
