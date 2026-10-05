"""Run the whole pipeline, stage by stage:  python pipeline/run_all.py
Needs the product photos in source/ (see PIPELINE.md, stage 0) and: pip install -r pipeline/requirements.txt"""
import importlib
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ORDER = [
    ("s01_calibrate", "run"), ("s02_edges", "run"), ("s03_hands", "run"), ("s04_dial_primitives", "run"), ("s05_lines", "run"),
    ("s06_residual", "run"), ("s07_text", "run"), ("s09_body", "run"), ("s10_bezel", "run"),
]


def main():
    for mod, fn in ORDER:
        t = time.time()
        print(f"\n=== {mod} ===")
        m = importlib.import_module(mod)
        if mod == "s02_edges":
            m.run("front_a"); m.run("front_b")
        elif mod == "s03_hands":
            from lib import save_json
            save_json("hands_raw.json", m.run("front_a"))
        else:
            getattr(m, fn)()
        print(f"[{mod}] {time.time() - t:.1f}s")
    # shading / colour measurements are small enough to live in their own script
    importlib.import_module("s08_measure").run()
    b = importlib.import_module("s11_build")
    b.write_assets()
    importlib.import_module("s12_verify").run()
    b.write_assets()                                  # again, so the website carries the verification numbers
    print("\nDone: assets/boreal-*.js, assets/boreal-preview.svg")


if __name__ == "__main__":
    main()
