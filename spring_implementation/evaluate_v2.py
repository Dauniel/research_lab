"""
evaluate_v2.py — Re-run batch_compare for all 5 focus constructs against
the v2 (cleaned-data + augmentation) trained model, then re-run
analyze_calibration so the calibration_table.json + per-construct
accuracy table update in place.

Usage:
    python spring_implementation/evaluate_v2.py [--model PATH]
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DEFAULT_MODEL = ROOT / "training" / "models" / "models" / "cond_cyto3_v2_clean"
BOX = Path("C:/Users/Danie/Box/Condensate Volume Quantification")

CONSTRUCTS = ["JABr", "GABr", "AABr", "JABr_4arm", "Tornado"]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model",  default=DEFAULT_MODEL, type=Path)
    p.add_argument("--suffix", default="v2", type=str, help="Output dir suffix")
    p.add_argument("--cond-topx",     default=100.0, type=float)
    p.add_argument("--cond-cellprob", default=-2.0,  type=float)
    return p.parse_args()


def main():
    args = parse_args()
    if not args.model.exists():
        print(f"Model not found: {args.model}")
        sys.exit(1)

    print(f"Evaluating v2 model: {args.model}\n")
    for c in CONSTRUCTS:
        out_dir = ROOT / "outputs" / "experiments" / f"batch_{c}_trained_{args.suffix}"
        cmd = [
            sys.executable, str(ROOT / "batch_compare.py"),
            "--construct-dir", str(BOX / c),
            "--output",        str(out_dir),
            "--cond-model",    str(args.model),
            "--cond-topx",     str(args.cond_topx),
            "--cond-cellprob", str(args.cond_cellprob),
        ]
        print(f"=== {c} ===")
        print(" ".join(cmd))
        rc = subprocess.call(cmd)
        if rc != 0:
            print(f"  [FAIL] exit code {rc}")
        print()

    print("All constructs done. Re-running analyzer...\n")
    subprocess.call([sys.executable, str(ROOT / "analyze_calibration.py")])


if __name__ == "__main__":
    main()
