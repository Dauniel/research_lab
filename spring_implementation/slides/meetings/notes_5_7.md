# Pipeline Notes — May 7, 2026

---

## The Big Picture

The pipeline answers one question: **how much more concentrated is a protein inside a condensate compared to the surrounding nucleus?**
That ratio is the Partition Coefficient (PC). To compute it you need to know *where* the condensates are and *where* the nucleus is — that's what the pipeline figures out automatically.

---

## Step-by-Step

### 1. Load
Two 3D image stacks are read in from TIF files:
- **Ch1** — the nuclei channel (fluorescent signal from the nucleus)
- **Ch2** — the condensate channel (fluorescent signal from the protein of interest)

Each stack is 55 Z-slices × 185 × 259 pixels. Think of it as a 3D block of pixels, like a loaf of bread sliced 55 times.

---

### 2. Denoise
Before trying to find any boundaries, every Z-slice gets run through Cellpose's denoising model. This sharpens edges and suppresses shot noise so the segmentation model can draw tighter, more accurate boundaries.

**Key point:** the denoised image is thrown away after this step. It is only used to guide *where* the boundaries go — never to measure intensity values.

---

### 3. Segment
Cellpose 3 (cyto3 model, do_3D=True) processes the full 3D stack — not slice by slice, but all 55 slices simultaneously. This means it tracks the same object consistently across Z rather than redrawing boundaries independently on each slice.

The output is two sets of **masks**:
- **Condensate masks** — each condensate gets a unique integer label. Every pixel inside condensate #1 is labeled 1, every pixel inside condensate #2 is labeled 2, and so on.
- **Nuclei masks** — same idea for nuclei.

After segmentation, the nuclei masks go through one extra step: Cellpose tends to split each nucleus into 15–25 fragments because of internal texture (the condensates inside the nucleus confuse it). To fix this, the binary mask (any pixel labeled > 0 = "inside a nucleus") is run through 3D connected-component analysis. This collapses all the fragments back into the true connected regions — 76 Cellpose labels become 5 clean nuclei.

---

### 4. Measure
Using the masks as selection tools on the original raw image, regionprops extracts per-object measurements for every Z-slice: area, centroid, and mean intensity.

---

### 5. 3D Volume
Counts how many voxels (3D pixels) each labeled object occupies across all 55 slices. This gives a true 3D volume estimate for each condensate and nucleus rather than just a per-slice area.

---

### 6. Partition Coefficient

This is where the masks are used to select pixels from the **raw image** (Ch2, the condensate channel):

**Background (B)**
First, find the minimum pixel value across the entire 3D stack. This is the camera/autofluorescence floor — a baseline offset that has nothing to do with the protein. It gets subtracted from every pixel before any density is computed.

**Condensate density**
- Take all pixels that are inside *both* a condensate mask *and* a nucleus mask
- Subtract B from each, clip to 0
- Sort by intensity, keep only the top 75% brightest
- Take the mean

The top-75% trim is important: Cellpose draws slightly inflated boundaries that include a dim halo around the true bright core. Trimming the dimmest 25% of mask pixels recovers approximately what a researcher would have drawn by hand.

**Dilute density**
- Take all pixels inside a nucleus mask but *outside* any condensate mask — this is the quiet nuclear background
- Find all valid 10×10×10 voxel patches that fit entirely within this region (~88,000 patches)
- Sort by mean intensity, take the 50 lowest-intensity patches
- Average them

The lowest-50-patch approach mimics how a researcher manually picks a quiet, representative background spot. Using a single random patch was unstable (PC would swing from 4.3 to 6.0 depending on where it landed).

**PC**
```
PC = condensate_density / dilute_density
```

Interpretation: how many times brighter are condensates than the surrounding nuclear background, after removing the camera offset.

---

## Why Each Step Matters

| Step | What would break without it |
|---|---|
| Denoising | Blurry boundaries → masks include too much dim halo → PC underestimated |
| do_3D=True | Slice-by-slice segmentation gives inconsistent boundaries across Z → noisy intensity measurements |
| Connected-component nuclei fix | Fragmented nucleus labels leave gaps → condensates in gaps excluded from PC calculation |
| Background subtraction | PC systematically lower than reference (reference always subtracts B) |
| Top-75% trim | Cellpose halos drag cond_density down → PC underestimated vs manual reference |
| Lowest-50-patch dilute | Single random patch is seed-dependent → PC swings ±30% across runs |

---

## What PC Means Biologically

A PC of 1.0 means the protein is equally distributed inside condensates and in the surrounding nucleus — no enrichment.
A PC of 6.3 (our result, matching the manual reference) means the protein is ~6× more concentrated inside the condensate than in the nuclear background. Higher PC = tighter, more selective condensate.
