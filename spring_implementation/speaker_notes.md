# Speaker Notes

## Slide: Background Subtracted Partition Coefficient

"To quantify how strongly condensates are enriched inside the nucleus, we compute the Partition Coefficient. The image on the left shows what we're actually measuring — the green regions are pixels that fall inside both a condensate mask and a nucleus mask, the blue regions are the nuclear dilute phase, and the red-tinted regions outside the nuclei represent the background.

Before we compute anything, we subtract B — the minimum intensity value across the entire field of view. This removes the camera dark current and autofluorescence, which act as a constant floor on every pixel. Without this correction, that floor inflates the dilute phase denominator much more than the condensate numerator — because the dilute phase is dim, so B is a large fraction of it — and that artificially pulls the PC toward 1.

Once we have background-subtracted values, we compute two densities. A quick note on terminology — we use the word voxel here rather than pixel. A pixel is 2D, just width and height. A voxel is the 3D equivalent — width, height, and depth, meaning one unit of volume spanning one XY pixel and one Z-slice. Since we're working with a 3D Z-stack, every measurement is over voxels, not flat pixels.

The condensate density is the mean corrected intensity over all voxels that are inside both a nucleus and a condensate. The dilute phase density is sampled from a small 10×10×10 voxel cube — a thousand voxels — entirely within the nuclear dilute region. We use a patch rather than averaging all dilute voxels for a specific reason: voxels sitting right next to a condensate boundary pick up bleed-through fluorescence from the bright condensate next door, due to the microscope's point spread function. If we averaged all dilute voxels we'd include those contaminated edge voxels and inflate the denominator. The 10×10×10 size is large enough to average out pixel-level noise but small enough to fit comfortably inside the dilute phase away from any edges. It gives us a clean, representative sample of the true nuclear background.

Dividing the two gives us PC = 6.775, which essentially matches the manually measured reference value of 6.32. This tells us the condensates are about 7 times more fluorescently dense than the surrounding nucleoplasm — a strong enrichment signal consistent with phase separation."
