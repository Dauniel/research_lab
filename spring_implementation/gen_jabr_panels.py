"""
Generate 6-panel figures (MIP) for every JABr ROI.
Panels (left-to-right): merged-channel reference | nuclei raw | cond raw |
                       nucleus mask | condensate mask | classification overlay.
Outputs to Research/reference_data/jabr_panels/<short>.png.
"""
import sys, re, csv
from pathlib import Path
import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import torch
from cellpose import models, core, denoise as cp_denoise
from skimage.feature import blob_log

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import denoise_stack, segment_nuclei, detect_condensates_blob

ROI_DIR  = Path("C:/Users/Danie/Box/Condensate Volume Quantification/JABr/Cut ROI")
MASK_DIR = Path("C:/Users/Danie/Box/Condensate Volume Quantification/JABr/Masks")
OUT_DIR  = Path("C:/storage/code/research/Research/reference_data/jabr_panels")
COMPARE  = Path("C:/storage/code/research/spring_implementation/outputs/blob_JABr_thresh03/comparison.csv")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def short(name: str) -> str:
    m = re.search(r"(Sample\d+_\d+_\d+)", name)
    return m.group(1) if m else name

def norm01(a, lo=2, hi=99.5):
    a = a.astype(np.float32)
    p_lo, p_hi = np.percentile(a, [lo, hi])
    if p_hi <= p_lo: return np.zeros_like(a)
    return np.clip((a - p_lo) / (p_hi - p_lo), 0, 1)

def main():
    use_gpu = core.use_gpu()
    print(f"GPU: {torch.cuda.get_device_name(0) if use_gpu else 'cpu'}")

    rows = [r for r in csv.DictReader(open(COMPARE)) if r["ref_pc"] and r["pipeline_pc"]]
    targets = sorted({r["filename"] for r in rows})
    print(f"{len(targets)} JABr ROIs")

    nuc_model = models.CellposeModel(gpu=use_gpu, model_type="cyto3")
    dn_model  = cp_denoise.DenoiseModel(model_type="denoise_cyto3", gpu=use_gpu)

    for i, fn in enumerate(targets, 1):
        s = short(fn)
        out = OUT_DIR / f"{s}.png"
        if out.exists():
            print(f"[{i}/{len(targets)}] {s} (cached)")
            continue
        tif_path = ROI_DIR / fn
        if not tif_path.exists():
            print(f"[{i}/{len(targets)}] {s} MISSING TIF")
            continue
        print(f"[{i}/{len(targets)}] {s}")

        roi = tiff.imread(tif_path)
        if roi.ndim != 4 or roi.shape[1] != 2:
            print(f"  skipping, bad shape {roi.shape}"); continue
        nuc_stack  = roi[:, 0]
        cond_stack = roi[:, 1]

        # Segment nuclei (Cellpose cyto3 + connected-component relabel)
        nuc_restored = denoise_stack(nuc_stack, dn_model, "nuclei")
        nuc_masks = segment_nuclei(nuc_restored, nuc_model, diameter=None, cellprob_threshold=-2.0)

        # Detect condensates (blob_log inside nuclei)
        cond_masks = detect_condensates_blob(cond_stack, nuc_masks > 0,
                                             threshold=0.03, min_sigma=1.5,
                                             max_sigma=6.0, num_sigma=8)

        # MIPs
        nuc_mip  = nuc_stack.max(axis=0)
        cond_mip = cond_stack.max(axis=0)
        nuc_bin  = (nuc_masks > 0).max(axis=0)
        cond_bin = (cond_masks > 0).max(axis=0)

        # Reference (Imaris) condensate mask: value 1 = nuclear condensates
        ref_mask_path = MASK_DIR / fn
        if ref_mask_path.exists():
            ref_mask = tiff.imread(ref_mask_path)
            ref_cond_bin = (ref_mask == 1).max(axis=0)
        else:
            ref_cond_bin = np.zeros_like(cond_bin)
            print(f"  warn: no reference mask at {ref_mask_path.name}")

        # Classification overlay (matches user's example image)
        # background everywhere, dilute = nuc & ~cond, condensate = cond
        klass = np.zeros_like(nuc_bin, dtype=np.uint8)        # 0 = background
        klass[nuc_bin & ~cond_bin] = 1                         # 1 = dilute
        klass[cond_bin] = 2                                    # 2 = condensate
        cmap = ListedColormap([(0.65, 0.40, 0.32), (0.18, 0.25, 0.66), (0.45, 0.85, 0.30)])

        # Figure
        fig, axes = plt.subplots(1, 7, figsize=(28, 4.2))
        # 1. Reference merge (cyan nuclei + magenta cond)
        rgb = np.zeros((*nuc_mip.shape, 3), dtype=np.float32)
        n01, c01 = norm01(nuc_mip), norm01(cond_mip)
        rgb[..., 0] = c01                # R = cond (magenta R+B)
        rgb[..., 1] = n01                # G = nuc (cyan G+B)
        rgb[..., 2] = np.maximum(n01, c01)
        axes[0].imshow(rgb); axes[0].set_title("Reference (nuc=cyan, cond=magenta)")
        # 2. Nuclei channel
        axes[1].imshow(n01, cmap="gray"); axes[1].set_title("Nuclei channel (MIP)")
        # 3. Condensate channel
        axes[2].imshow(c01, cmap="gray"); axes[2].set_title("Condensate channel (MIP)")
        # 4. Pipeline nuclei mask
        axes[3].imshow(nuc_bin, cmap="gray"); axes[3].set_title("Pipeline nuclei mask")
        # 5. Pipeline condensate mask
        axes[4].imshow(cond_bin, cmap="gray"); axes[4].set_title("Pipeline cond mask")
        # 6. Reference (Imaris) condensate mask — nuclear class only
        axes[5].imshow(ref_cond_bin, cmap="gray"); axes[5].set_title("Reference cond mask (Imaris)")
        # 7. Classification overlay
        axes[6].imshow(klass, cmap=cmap, vmin=0, vmax=2); axes[6].set_title("Classification (MIP)")

        for ax in axes:
            ax.set_xticks([]); ax.set_yticks([])

        fig.suptitle(f"JABr {s}", fontsize=14, y=1.02)
        fig.tight_layout()
        fig.savefig(out, dpi=110, bbox_inches="tight")
        plt.close(fig)

    print("DONE")

if __name__ == "__main__":
    main()
