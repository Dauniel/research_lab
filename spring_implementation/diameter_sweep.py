"""
diameter_sweep.py — Search the Cellpose `diameter` parameter that maximizes
Pearson r between pipeline_pc and ref_pc for one construct.

The trained model was trained at default diameter (~30). At inference,
specifying a smaller diameter rescales images upward so small condensates
appear as ~30 px to the model. This is a per-construct lever the prior
batch runs never touched.

Usage:
    python spring_implementation/diameter_sweep.py \
        --construct GABr \
        --diameters 10 15 20 25 30
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff
import torch
from cellpose import models, core, denoise as cp_denoise

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import denoise_stack, segment_condensates, segment_nuclei, compute_partition_coefficient
from batch_compare import max_overlap_nucleus


BOX_ROOT = Path("C:/Users/Danie/Box/Condensate Volume Quantification")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--construct",     required=True, type=str)
    p.add_argument("--cond-model",    default="spring_implementation/training/models/models/cond_cyto3_resume", type=Path)
    p.add_argument("--cond-cellprob", default=-2.0,  type=float)
    p.add_argument("--cond-topx",     default=100.0, type=float)
    p.add_argument("--diameters",     default=[10, 15, 20, 25, 30], nargs="+", type=float)
    p.add_argument("--n-cells",       default=10,    type=int, help="Subsample cells for speed")
    p.add_argument("--output",        default=None,  type=Path)
    return p.parse_args()


def run_one(tif_path, dn_model, cond_seg, nuc_seg, diameter, cellprob, topx):
    roi = tiff.imread(tif_path)
    nuc_stack  = roi[:, 0, :, :].copy()
    cond_stack = roi[:, 1, :, :].copy()
    cond_restored = denoise_stack(cond_stack, dn_model, "condensates")
    nuc_restored  = denoise_stack(nuc_stack,  dn_model, "nuclei")
    cond_masks = segment_condensates(cond_restored, cond_seg, diameter=diameter, cellprob_threshold=cellprob)
    nuc_masks  = segment_nuclei(nuc_restored,  nuc_seg, diameter=None, cellprob_threshold=-2.0)
    nuc_masks  = max_overlap_nucleus(nuc_masks, cond_masks)
    return compute_partition_coefficient(cond_stack, cond_masks, nuc_masks, cond_topx=topx)


def main():
    args = parse_args()
    out = args.output or (Path(__file__).parent / "outputs" / "diagnostics" / f"diameter_sweep_{args.construct}")
    out.mkdir(parents=True, exist_ok=True)

    construct_dir = BOX_ROOT / args.construct
    ref_csv = next(construct_dir.glob("*_Partition coefficient_nuclear.csv"))
    ref_df = pd.read_csv(ref_csv)
    ref_df.columns = ["filename", "ref_cond_density", "ref_dilute_density", "ref_pc"]
    ref_lookup = ref_df.set_index("filename")

    roi_dir = construct_dir / "Cut ROI"
    tifs = [p for p in sorted(roi_dir.rglob("*.tif"))
            if "_cp_masks" not in p.name and p.name in ref_lookup.index]
    if args.n_cells and args.n_cells < len(tifs):
        # Spread the sample across the cell list
        idx = np.linspace(0, len(tifs)-1, args.n_cells, dtype=int)
        tifs = [tifs[i] for i in idx]
    print(f"Construct={args.construct}  cells={len(tifs)}  diameters={args.diameters}")

    use_gpu = core.use_gpu()
    dn_model = cp_denoise.DenoiseModel(model_type="denoise_cyto3", gpu=use_gpu)
    nuc_seg  = models.CellposeModel(gpu=use_gpu, model_type="cyto3")
    cond_seg = models.CellposeModel(gpu=use_gpu, pretrained_model=str(args.cond_model))

    rows = []
    for d in args.diameters:
        diameter = None if d == 0 else float(d)
        for tif in tifs:
            try:
                res = run_one(tif, dn_model, cond_seg, nuc_seg, diameter, args.cond_cellprob, args.cond_topx)
                ref = ref_lookup.loc[tif.name]
                rows.append({
                    "filename":   tif.name,
                    "diameter":   d,
                    "ref_pc":     ref["ref_pc"],
                    "pipeline_pc": res["pc"],
                })
            except Exception as e:
                print(f"  {tif.name} ERROR: {e}")

    df = pd.DataFrame(rows)
    df.to_csv(out / "sweep.csv", index=False)

    print("\nDiameter sweep results:")
    for d, g in df.groupby("diameter"):
        gg = g.dropna(subset=["pipeline_pc"])
        if len(gg) < 2:
            print(f"  d={d}: too few results")
            continue
        r = np.corrcoef(gg["ref_pc"], gg["pipeline_pc"])[0, 1]
        rmse = float(((gg["pipeline_pc"] - gg["ref_pc"]) ** 2).mean() ** 0.5)
        err = (gg["pipeline_pc"] - gg["ref_pc"]).abs() / gg["ref_pc"] * 100
        print(f"  diameter={d:>5}: r={r:.3f}  RMSE={rmse:.2f}  err%={err.mean():.1f}  n={len(gg)}")


if __name__ == "__main__":
    main()
