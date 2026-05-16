"""
build_training_data.py — Build a Cellpose-ready 3D training dataset from the
Imaris ground-truth masks in Box.

Source layout (Box):
    <construct>/
        Cut ROI/<file>.tif        # raw (Z, 2, Y, X) — ch0=nuclei, ch1=cond
        Masks/<file>.tif          # (Z, Y, X) uint8 with values {0, 1, 2}:
                                  #   1 = nuclear condensate (Imaris)
                                  #   2 = cytoplasmic condensate (Imaris)

Output layout (--output):
    train/<construct>__<stem>_img.tif     # (Z, Y, X) uint16 — cond channel only
    train/<construct>__<stem>_masks.tif   # (Z, Y, X) uint16 — instance labels
    val/  ...                              # same pattern
    manifest.csv                          # one row per kept volume
    skipped.csv                           # masks that were excluded + reason

We union label 1 and label 2 into a single binary condensate mask, then run
3D connected components (face-connectivity) to assign instance IDs. The output
is a drop-in replacement for the input to Cellpose's `segment_condensates`
in pipeline.py — single-channel images, instance-labeled masks.

Usage:
    python spring_implementation/training/build_training_data.py
    python spring_implementation/training/build_training_data.py --dry-run
"""

import argparse
import csv
import re
import time
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import tifffile as tiff
from skimage.measure import label as cc_label

# Per-construct condensate-channel index (0-indexed into axis-C of the ROI).
# Determined empirically by which channel has highest intensity inside the
# Imaris mask. Default is 1 (JABr convention: ch0=nuclei, ch1=condensate).
COND_CHANNEL_OVERRIDE = {
    "JABr_mCherry":      0,   # mCherry signal on ch0
    "JABr MS2_mCherry":  0,   # same
    # 15ntCMango / 15ntEMango: 3-channel but cond still on ch1 (default)
}

# Pattern that pulls the sample suffix (e.g. "Sample1_1_1.tif", "sample3_3_1.tif",
# even "Smaple1_4_4.tif" — there is a real typo in ABPP filenames) out of either
# a mask filename or a ROI filename, so we can pair them despite prefix mismatches
# like "JAPP_..." (mask) vs "JBPP_..." (ROI) seen in the JBPP folder.
SAMPLE_SUFFIX_RE = re.compile(r"[Ss][mam]+ple\d+(?:_\d+)+\.tif$", re.IGNORECASE)

warnings.filterwarnings("ignore", message=".*invalid page offset.*")


def _retry(fn, *args, retries=3, delay=1.0, **kwargs):
    """Retry on transient Box Drive sync errors (WinError 1006, etc.)."""
    last = None
    for i in range(retries):
        try:
            return fn(*args, **kwargs)
        except OSError as e:
            last = e
            time.sleep(delay * (i + 1))
    raise last


def _path_exists(p: Path) -> bool:
    try:
        return _retry(p.exists)
    except OSError:
        return False

DEFAULT_BOX = Path(r"C:/Users/Danie/Box/Condensate Volume Quantification")
DEFAULT_OUT = Path(__file__).parent / "dataset"

# Non-construct folders in the Box root
SKIP_FOLDERS = {"Fig 3 plots", "Figures", "Statistics", "Tornado", "loop recruitment"}


def parse_args():
    p = argparse.ArgumentParser(description="Build Cellpose training dataset from Box masks.")
    p.add_argument("--box-root", default=DEFAULT_BOX, type=Path)
    p.add_argument("--output",   default=DEFAULT_OUT, type=Path)
    p.add_argument("--val-frac", default=0.2,         type=float)
    p.add_argument("--seed",     default=42,          type=int)
    p.add_argument("--dry-run",  action="store_true",
                   help="List planned dataset without writing files")
    return p.parse_args()


def find_constructs(box_root: Path):
    out = []
    for p in sorted(box_root.iterdir()):
        if not p.is_dir() or p.name in SKIP_FOLDERS:
            continue
        masks_dir = p / "Masks"
        rois_dir  = p / "Cut ROI"
        if not (masks_dir.exists() and rois_dir.exists()):
            continue
        mask_files = sorted(masks_dir.glob("*.tif"))
        if mask_files:
            out.append((p.name, masks_dir, rois_dir, mask_files))
    return out


def build_one(mask_path: Path, roi_path: Path, cond_ch: int):
    """Return (cond_image, instance_mask, n_instances, n_voxels, err)."""
    try:
        m = _retry(tiff.imread, mask_path)
        r = _retry(tiff.imread, roi_path)
    except Exception as e:
        return None, None, 0, 0, f"read error: {e}"

    if m.ndim != 3:
        return None, None, 0, 0, f"mask not 3D: {m.shape}"
    if r.ndim != 4 or r.shape[1] < 2:
        return None, None, 0, 0, f"roi shape not (Z,C>=2,Y,X): {r.shape}"
    if cond_ch >= r.shape[1]:
        return None, None, 0, 0, f"cond_ch={cond_ch} out of range for shape {r.shape}"
    if (m.shape[0], m.shape[1], m.shape[2]) != (r.shape[0], r.shape[2], r.shape[3]):
        return None, None, 0, 0, f"shape mismatch: mask {m.shape} vs roi {r.shape}"

    cond_binary = (m == 1) | (m == 2)
    n_voxels = int(cond_binary.sum())
    if n_voxels == 0:
        return None, None, 0, 0, "empty mask"

    inst = cc_label(cond_binary, connectivity=1).astype(np.uint16)
    cond_image = r[:, cond_ch, :, :].astype(np.uint16, copy=True)
    return cond_image, inst, int(inst.max()), n_voxels, None


def sample_suffix(name: str) -> str:
    """Return canonical sample suffix (e.g. 'sample1_1_1.tif') used to pair
    masks with ROIs across naming inconsistencies. Falls back to full name."""
    m = SAMPLE_SUFFIX_RE.search(name)
    return m.group(0).lower().replace("smaple", "sample") if m else name.lower()


def main():
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    constructs = find_constructs(args.box_root)
    print(f"Constructs with Masks/ + Cut ROI/: {len(constructs)}")
    total_files = sum(len(mf) for _, _, _, mf in constructs)
    print(f"Mask files to process            : {total_files}")

    train_dir = args.output / "train"
    val_dir   = args.output / "val"
    if not args.dry_run:
        train_dir.mkdir(parents=True, exist_ok=True)
        val_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    skipped = []

    for cname, masks_dir, rois_dir, mask_files in constructs:
        # Build a suffix → ROI path lookup so we can match across construct/typo
        # mismatches (e.g. JAPP-named masks living in JBPP/, "Smaple" typos).
        try:
            roi_by_suffix = {
                sample_suffix(p.name): p
                for p in _retry(lambda: list(rois_dir.glob("*.tif")))
            }
        except OSError:
            roi_by_suffix = {}

        cond_ch = COND_CHANNEL_OVERRIDE.get(cname, 1)

        # Pair masks with matching ROIs first (some constructs may have orphans)
        pairs = []
        for mp in mask_files:
            rp = rois_dir / mp.name
            if not _path_exists(rp):
                rp = roi_by_suffix.get(sample_suffix(mp.name))
            if rp is not None and _path_exists(rp):
                pairs.append((mp, rp))
            else:
                skipped.append((cname, mp.name, "no matching Cut ROI"))
        if not pairs:
            continue

        # Stratified 80/20 split within this construct (at least 1 in val if n>=2)
        order = np.arange(len(pairs))
        rng.shuffle(order)
        if len(pairs) >= 2:
            n_val = max(1, int(round(len(pairs) * args.val_frac)))
        else:
            n_val = 0
        val_set = set(order[:n_val].tolist())

        for i, (mp, rp) in enumerate(pairs):
            split = "val" if i in val_set else "train"
            img, inst, n_inst, n_vox, err = build_one(mp, rp, cond_ch)
            if err is not None:
                skipped.append((cname, mp.name, err))
                continue

            stem = f"{cname.replace(' ', '_')}__{mp.stem}"
            row = {
                "construct":   cname,
                "filename":    mp.name,
                "split":       split,
                "n_instances": n_inst,
                "n_voxels":    n_vox,
                "shape":       f"{img.shape[0]}x{img.shape[1]}x{img.shape[2]}",
            }

            if not args.dry_run:
                out_dir = train_dir if split == "train" else val_dir
                img_p  = out_dir / f"{stem}_img.tif"
                mask_p = out_dir / f"{stem}_masks.tif"
                tiff.imwrite(img_p,  img,  compression="zlib")
                tiff.imwrite(mask_p, inst, compression="zlib")
                row["img_path"]  = str(img_p.relative_to(args.output)).replace("\\", "/")
                row["mask_path"] = str(mask_p.relative_to(args.output)).replace("\\", "/")

            rows.append(row)

        n_t = sum(1 for r in rows if r["construct"] == cname and r["split"] == "train")
        n_v = sum(1 for r in rows if r["construct"] == cname and r["split"] == "val")
        print(f"  {cname:<22}  train={n_t:>3}  val={n_v:>3}  (skip={sum(1 for s in skipped if s[0]==cname)})", flush=True)

    # Manifest
    if not args.dry_run and rows:
        fields = list(rows[0].keys())
        with open(args.output / "manifest.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        if skipped:
            with open(args.output / "skipped.csv", "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["construct", "filename", "reason"])
                w.writerows(skipped)

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary ({'DRY RUN' if args.dry_run else 'written'})")
    print(f"  Kept    : {len(rows)}")
    print(f"  Train   : {sum(1 for r in rows if r['split']=='train')}")
    print(f"  Val     : {sum(1 for r in rows if r['split']=='val')}")
    print(f"  Skipped : {len(skipped)}")

    # Instance stats
    if rows:
        inst_counts = [r["n_instances"] for r in rows]
        vox_counts  = [r["n_voxels"]    for r in rows]
        print(f"  Instances per volume : min={min(inst_counts)}  med={int(np.median(inst_counts))}  "
              f"max={max(inst_counts)}  total={sum(inst_counts)}")
        print(f"  Voxels per volume    : min={min(vox_counts)}  med={int(np.median(vox_counts))}  "
              f"max={max(vox_counts)}  total={sum(vox_counts)}")

    if skipped:
        print(f"\nReasons for skip (first 10):")
        for c, fn, why in skipped[:10]:
            print(f"  {c}/{fn}: {why}")

    if not args.dry_run:
        print(f"\nOutput: {args.output}")


if __name__ == "__main__":
    main()
