"""
train_cellpose.py — Fine-tune a Cellpose model on the multi-construct condensate
dataset produced by build_training_data.py.

Cellpose 3 trains 2D networks. Each 3D volume in dataset/{train,val} is sliced
into Z-planes; slices with fewer than --min-masks instance labels are dropped
(they're mostly background and just slow training).

At inference time, the trained 2D weights are used with do_3D=True, which
runs the 2D model along XY, XZ, YZ orientations and stitches gradient flows
into a 3D mask — exactly what pipeline.py already does with cyto3.

Usage:
    python spring_implementation/training/train_cellpose.py
    python spring_implementation/training/train_cellpose.py --epochs 200 --name cond_v1
"""

import argparse
from pathlib import Path

import numpy as np
import tifffile as tiff
from tqdm import tqdm

from cellpose import core, io, models, train


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset",    default=Path(__file__).parent / "dataset", type=Path)
    p.add_argument("--output",     default=Path(__file__).parent / "models",  type=Path)
    p.add_argument("--name",       default="cond_cyto3",                      type=str)
    p.add_argument("--pretrained", default="cyto3",                           type=str)
    p.add_argument("--epochs",     default=150,    type=int)
    p.add_argument("--batch-size", default=8,      type=int)
    p.add_argument("--lr",         default=0.005,  type=float)
    p.add_argument("--save-every", default=25,     type=int)
    p.add_argument("--min-masks",  default=3,      type=int,
                   help="Drop 2D slices with fewer than N instance labels")
    p.add_argument("--manifest",   default=None,   type=Path,
                   help="Optional manifest CSV: keep only listed (construct,filename) pairs")
    p.add_argument("--scale-range", default=None,  type=float,
                   help="Cellpose scale_range augmentation strength (default cellpose internal)")
    p.add_argument("--balance-constructs", action="store_true",
                   help="Upsample underrepresented constructs so each contributes equally")
    p.add_argument("--balance-cap", default=None, type=int,
                   help="Cap the per-construct target slice count (default: match largest construct). "
                        "Use this to limit RAM usage, e.g. --balance-cap 700 keeps total slices ~15k.")
    p.add_argument("--no-gpu",     action="store_true")
    return p.parse_args()


def collect_pairs(split_dir: Path, manifest_keys: set | None = None):
    pairs = []
    for img in sorted(split_dir.glob("*_img.tif")):
        mask = img.parent / img.name.replace("_img.tif", "_masks.tif")
        if not mask.exists():
            continue
        if manifest_keys is not None:
            # manifest filenames look like "<construct>__<orig>_img.tif"; key = stem without _img
            key = img.name.replace("_img.tif", "")
            if key not in manifest_keys:
                continue
        pairs.append((img, mask))
    return pairs


def load_manifest_keys(manifest_path: Path, split: str) -> set:
    import pandas as pd
    df = pd.read_csv(manifest_path)
    df = df[df["split"] == split]
    # img_path looks like "train/<construct>__<orig>_img.tif" — strip dir and _img.tif
    return {Path(p).name.replace("_img.tif", "") for p in df["img_path"]}


def construct_from_filename(path: Path) -> str:
    """Extract construct name from training filename (e.g. 'JABr__Sample..._img.tif' -> 'JABr')."""
    return path.name.split("__")[0]


def load_slices(pairs, min_masks: int, desc: str):
    """Slice each (3D image, 3D instance mask) pair into 2D Z-planes; keep slices
    with at least `min_masks` distinct instance labels.
    Returns (imgs, masks, constructs) where constructs[i] is the construct name
    for slice i."""
    imgs, masks, constructs = [], [], []
    n_volumes_kept = 0
    n_slices_seen = 0
    for img_p, mask_p in tqdm(pairs, desc=desc, unit="vol"):
        construct = construct_from_filename(img_p)
        img_3d  = tiff.imread(img_p)
        mask_3d = tiff.imread(mask_p)
        if img_3d.ndim != 3 or mask_3d.ndim != 3 or img_3d.shape != mask_3d.shape:
            continue
        kept_this_volume = 0
        for z in range(img_3d.shape[0]):
            slc_m = mask_3d[z]
            n_inst = int(slc_m.max())
            if n_inst < min_masks:
                continue
            # Relabel slice 1..k so Cellpose doesn't see gaps in instance IDs
            uniq = np.unique(slc_m)
            uniq = uniq[uniq > 0]
            if len(uniq) < min_masks:
                continue
            remap = np.zeros(uniq.max() + 1, dtype=np.int32)
            for new_id, old_id in enumerate(uniq, start=1):
                remap[old_id] = new_id
            imgs.append(img_3d[z].astype(np.float32))
            masks.append(remap[slc_m].astype(np.int32))
            constructs.append(construct)
            kept_this_volume += 1
            n_slices_seen += 1
        if kept_this_volume:
            n_volumes_kept += 1
    print(f"  {desc}: {n_volumes_kept}/{len(pairs)} volumes contributed, "
          f"{len(imgs)} 2D slices kept")
    return imgs, masks, constructs


def balance_by_construct(imgs, masks, constructs, seed=42, cap=None):
    """Upsample underrepresented constructs so each contributes the same number
    of slices. Target = min(max_construct_slices, cap) if cap is set.
    Uses random duplication with a fixed seed."""
    from collections import defaultdict

    by_construct = defaultdict(list)
    for i, c in enumerate(constructs):
        by_construct[c].append(i)

    max_slices = max(len(idxs) for idxs in by_construct.values())
    target = min(max_slices, cap) if cap is not None else max_slices
    rng = np.random.default_rng(seed)

    balanced_imgs, balanced_masks = [], []
    print(f"\n  Construct balancing (target = {target} slices each"
          + (f", capped from {max_slices}" if cap is not None and cap < max_slices else "") + "):")
    for c in sorted(by_construct):
        idxs = by_construct[c]
        n_orig = len(idxs)
        if n_orig >= target:
            chosen = rng.choice(idxs, size=target, replace=False)
        else:
            chosen = np.concatenate([
                np.array(idxs),
                rng.choice(idxs, size=target - n_orig, replace=True),
            ])
        ratio = len(chosen) / n_orig
        print(f"    {c:<18} {n_orig:>5} -> {len(chosen):>5}  ({ratio:.1f}x)")
        for idx in chosen:
            balanced_imgs.append(imgs[idx])
            balanced_masks.append(masks[idx])

    shuffle_idx = rng.permutation(len(balanced_imgs))
    balanced_imgs = [balanced_imgs[i] for i in shuffle_idx]
    balanced_masks = [balanced_masks[i] for i in shuffle_idx]

    print(f"    {'TOTAL':<18} {len(imgs):>5} -> {len(balanced_imgs):>5}")
    return balanced_imgs, balanced_masks


def main():
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # Wire Cellpose's logging through to stdout so we can see per-epoch losses.
    # Without this, train_seg's epoch metrics go to ~/.cellpose/run.log only.
    io.logger_setup()

    train_keys = val_keys = None
    if args.manifest is not None:
        train_keys = load_manifest_keys(args.manifest, "train")
        val_keys   = load_manifest_keys(args.manifest, "val")
        print(f"Filtering by manifest: {args.manifest}")
    train_pairs = collect_pairs(args.dataset / "train", train_keys)
    val_pairs   = collect_pairs(args.dataset / "val",   val_keys)
    print(f"Train volumes: {len(train_pairs)}")
    print(f"Val volumes  : {len(val_pairs)}")
    if not train_pairs:
        raise SystemExit("No training pairs found — run build_training_data.py first.")

    use_gpu = core.use_gpu() and not args.no_gpu
    # If --pretrained points to a real file, treat it as a resume checkpoint;
    # otherwise it's a built-in model name (e.g. "cyto3").
    pretrained_path = Path(args.pretrained)
    resume_from_ckpt = pretrained_path.is_file()

    print(f"GPU: {'on' if use_gpu else 'off (CPU)'}")
    if resume_from_ckpt:
        print(f"Resuming from checkpoint: {pretrained_path}  ->  saving as '{args.name}'")
    else:
        print(f"Pretrained: {args.pretrained}  ->  fine-tuning to '{args.name}'")
    print(f"Slicing 3D volumes into 2D Z-planes (min {args.min_masks} instances per slice)...")

    train_imgs, train_masks, train_constructs = load_slices(train_pairs, args.min_masks, desc="train")
    val_imgs,   val_masks,   _                = load_slices(val_pairs,   args.min_masks, desc="val  ")

    if not train_imgs:
        raise SystemExit(f"No training slices passed min_masks={args.min_masks}. Try lowering it.")

    if args.balance_constructs:
        train_imgs, train_masks = balance_by_construct(
            train_imgs, train_masks, train_constructs,
            cap=args.balance_cap,
        )

    print(f"\nEpochs={args.epochs}  batch={args.batch_size}  lr={args.lr}")
    print(f"Output dir: {args.output}\n")

    if resume_from_ckpt:
        model = models.CellposeModel(gpu=use_gpu, pretrained_model=str(pretrained_path))
    else:
        model = models.CellposeModel(gpu=use_gpu, model_type=args.pretrained)

    train_kwargs = dict(
        train_data=train_imgs,
        train_labels=train_masks,
        test_data=val_imgs,
        test_labels=val_masks,
        channels=[0, 0],        # grayscale (cond channel only, no nucleus aux channel)
        n_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        save_path=str(args.output),
        save_every=args.save_every,
        save_each=True,         # keep every checkpoint so we can pick best by val loss
        min_train_masks=args.min_masks,
        model_name=args.name,
    )
    if args.scale_range is not None:
        train_kwargs["scale_range"] = args.scale_range
    train.train_seg(model.net, **train_kwargs)

    print(f"\nTraining done. Checkpoints in: {args.output}")
    print(f"Best model: {args.output / args.name}")
    print(f"\nTo use in pipeline.py, replace:")
    print(f"  models.CellposeModel(gpu=..., model_type='cyto3')")
    print(f"with:")
    print(f"  models.CellposeModel(gpu=..., pretrained_model=r'{args.output / args.name}')")


if __name__ == "__main__":
    main()
