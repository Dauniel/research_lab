# Speaker Notes

## Slide 1: Title

"Hi everyone, I'm Daniel Chang, an undergraduate researcher in the Franco Lab. My project this year has been building an automated image analysis pipeline for RNA condensates — so instead of a researcher sitting at a computer manually clicking through microscopy images, we can run a Python script and get quantitative results out the other end."

---

## Slide 2: RNA Condensates

"So first, what are condensates? They're dense, membrane-less droplets that form inside cells when certain molecules exceed a local concentration threshold — it's a process called phase separation, similar to how oil and water separate. The Franco Lab engineers synthetic versions of these using RNA nanostars, which are short single-stranded RNA molecules — around 100 to 200 nucleotides — that fold into multi-arm structures. The arms interact with each other through kissing loops, which are short complementary sequences at the tips. When enough of these nanostars are present, they start clustering together and phase-separate into a condensate. What's powerful about this system is that you can tune the behavior by changing design parameters: how long the arms are, how many arms there are, and which kissing loop sequence you use — each of those changes how strongly the nanostars interact and whether a condensate forms."

---

## Slide 3: The JABr Construct

"The specific construct I'm working with is called JABr. The name encodes its design — J for the 15-nucleotide stem length, A for kissing-loop variant A with sequence UCGCGA, Br for the Broccoli fluorescent aptamer tag that lets us see it under the microscope. The 15-nt arm length is biologically significant — it sits right at the nuclear pore permeability threshold, meaning these nanostars are small enough to pass through nuclear pores and form condensates in both the nucleus and the cytoplasm. To measure how strongly they're enriched in the nucleus relative to the surrounding nucleoplasm, we use the Partition Coefficient, or PC — it's essentially the fluorescence intensity of the condensate divided by the intensity of the surrounding nuclear background. A PC of 1 means no enrichment, and higher values mean stronger phase separation."

---

## Slide 4: The Problem — Manual Analysis Doesn't Scale

"The problem that motivated this project is that the existing analysis workflow was entirely manual. A researcher would open each image in ImageJ or Fiji, draw regions of interest by hand around nuclei and condensates, and record measurements one by one. That's slow, it's hard to reproduce because different people draw boundaries slightly differently, and it doesn't scale — if you want to analyze a dataset with hundreds of images or compare multiple constructs, manual analysis becomes a bottleneck. The goal of my project was to replace that with a fully automated Python pipeline: you give it raw microscopy Z-stacks as input, and it outputs segmentation masks, per-object measurement tables, and the partition coefficient. No manual clicking required."

---

## Slide 5: Image Analysis Pipeline

"Here's the full pipeline. The input is a raw Z-stack — a 3D fluorescence image with 55 slices and 2 channels. The first step is channel separation: channel 1 is the nuclei stained with a nuclear dye, channel 2 is the condensates tagged with Broccoli. Each channel goes into Cellpose, which is a deep learning segmentation model — it draws boundaries around each nucleus and each condensate and outputs a labeled mask. From there, we combine the two masks to do compartment classification — any condensate that spatially overlaps with a nucleus is labeled nuclear, and anything outside is cytoplasmic. Then we run feature extraction using scikit-image's regionprops, which gives us area, centroid, and mean intensity per object per Z-slice. Finally, we compute the partition coefficient from those intensity values. The outputs are three things: the segmentation masks saved as TIF stacks, measurement tables as CSVs, and summary visualizations."

---

## Slide 6: Quantifying Nuclear Enrichment

"To compute the PC, we need two numbers. The condensate density is the mean fluorescence intensity of all pixels that fall inside both a nucleus mask and a condensate mask — those are the bright, condensed-phase pixels. The dilute-phase density is the mean intensity of pixels that are inside the nucleus but outside any condensate mask — that's the dim nuclear background, the diffuse RNA floating around in the nucleoplasm. Dividing the two gives us PC. If PC is greater than 1, the condensates are brighter than the surrounding nucleoplasm, meaning the RNA is actively concentrating into those condensate structures. The image here shows a merged view with condensates in green overlaid on the nuclei in blue — you can see the bright green spots sitting inside the darker blue nuclear regions."

---

## Slide 7: Background Subtracted Partition Coefficient

"To quantify how strongly condensates are enriched inside the nucleus, we compute the Partition Coefficient. The image on the left shows what we're actually measuring — the green regions are pixels that fall inside both a condensate mask and a nucleus mask, the blue regions are the nuclear dilute phase, and the red-tinted regions outside the nuclei represent the background.x

Before we compute anything, we subtract B — the minimum intensity value across the entire field of view. This removes the camera dark current and autofluorescence, which act as a constant floor on every pixel. Without this correction, that floor inflates the dilute phase denominator much more than the condensate numerator — because the dilute phase is dim, so B is a large fraction of it — and that artificially pulls the PC toward 1.

Once we have background-subtracted values, we compute two densities. A quick note on terminology — we use the word voxel here rather than pixel. A pixel is 2D, just width and height. A voxel is the 3D equivalent — width, height, and depth, meaning one unit of volume spanning one XY pixel and one Z-slice. Since we're working with a 3D Z-stack, every measurement is over voxels, not flat pixels.

The condensate density is the mean corrected intensity over all voxels that are inside both a nucleus and a condensate. The dilute phase density is sampled from a small 10×10×10 voxel cube — a thousand voxels — entirely within the nuclear dilute region. We use a patch rather than averaging all dilute voxels for a specific reason: voxels sitting right next to a condensate boundary pick up bleed-through fluorescence from the bright condensate next door, due to the microscope's point spread function. If we averaged all dilute voxels we'd include those contaminated edge voxels and inflate the denominator. The 10×10×10 size is large enough to average out pixel-level noise but small enough to fit comfortably inside the dilute phase away from any edges. It gives us a clean, representative sample of the true nuclear background.

Dividing the two gives us PC = 6.775, which essentially matches the manually measured reference value of 6.32. This tells us the condensates are about 7 times more fluorescently dense than the surrounding nucleoplasm — a strong enrichment signal consistent with phase separation."

---

## Slide 8: Segmentation Masks from Pipeline

"This slide shows the actual segmentation output from the pipeline on a single Z-slice at z = 20, which is near the middle of the stack where cells are most fully in frame. On the left is the nuclei mask — each white region is a detected nucleus. In the middle is the condensate mask — the small bright spots are individual condensates detected by Cellpose. And on the right is a merged overlay where you can see the spatial relationship directly: the green condensate spots sitting inside the blue nuclear regions. Across all 55 Z-slices, the pipeline detected 80 nuclei and 186 condensates total. The fact that most condensates land inside nuclei is consistent with what we'd expect from the JABr construct given its 15-nt arm length — it's small enough to enter the nucleus and form condensates there."

---

## Slide 9: Measurement Tables from Pipeline

"The pipeline outputs two CSV files — one for condensates and one for nuclei. Each row is one detected object on one Z-slice. The columns are: label, which is the unique ID for that object tracked across slices; area in pixels squared; the y and x centroid coordinates; mean intensity; and z, the slice index. So for example, condensate label 2 appears across z-slices 7 through 10 with increasing area as we move through the middle of the condensate, and its mean intensity varies slice to slice. This per-slice structure is what lets us compute 3D volumes — by summing the area of each label across all the slices it appears in, multiplied by the physical voxel depth, we get a true 3D volume estimate. These tables are what all the downstream analysis and visualizations are built from."

---

## Slide 10: Segmentation Measurements from Pipeline

"And finally here are the summary measurements. Top left: the PC is 6.775, just above the reference value of 6.32 marked by the red dashed line — so our automated pipeline essentially reproduces the manual result. Top right: objects detected per Z-slice across the stack. Nuclei are relatively stable across the middle slices, which makes sense since nuclei are large and span most of the stack. Condensates peak sharply around z = 30 and drop off toward the edges, which reflects where the focal plane best resolves the small condensate structures. The area and intensity histograms show that both condensates and nuclei have right-skewed distributions — most objects are small, with a few larger ones. The 3D volume histograms at the bottom are the new addition this quarter — condensate volumes range from near zero up to about 7000 voxels, and nuclei up to around 80,000 voxels. These volume estimates give us a more physically meaningful measure of condensate size than per-slice area alone."

Top row (per-slice measurements — each count is one
object on one Z-slice):                           
                                    
Condensate Area (px²) — Most condensates are tiny, 
under 50 px² per slice. The distribution is heavily
right-skewed with a long tail up to ~650 px². This
makes sense — condensates are small puncta, and   
you're only seeing a 2D cross-section of each one  
per slice.

Condensate Intensity — Nearly all condensates      
cluster around 150–200 mean intensity, with a sharp
drop-off after. The tight distribution suggests   
condensates are fairly uniform in brightness —   
they're all roughly the same fluorescent density.
The small tail past 400 is likely a few very bright
or large condensates.

Nuclei Area (px²) — Most nuclei per-slice          
cross-sections are small (under 200 px²), but the
tail extends to 5000 px². This reflects the 3D     
geometry — near the top and bottom of a nucleus you
see a tiny circular cross-section, and near the
equator you see the full large cross-section. So
one nucleus contributes many different area values
across its Z-slices.

---
Bottom row (per-object 3D measurements — each count
is one unique object across all slices):          
                                    
Nuclei Intensity — Unlike condensates, nuclei      
intensity is broadly distributed from ~200 to 600, 
roughly bell-shaped peaking around 400. Nuclei vary
more in brightness than condensates do, likely due
to differences in nuclear stain uptake across   
cells.

Condensate 3D Volume (voxels) — Most condensates   
are very small in 3D, under 500 voxels, with a few
reaching ~7000. This confirms condensates are      
genuinely small puncta in 3D space, not just     
artifacts of viewing thin slices.

Nuclei 3D Volume (voxels) — Most nuclei are small  
(under 2000 voxels) but there's a wide spread up to
~80,000. The large variance reflects real         
biological differences in cell size, plus some   
nuclei being only partially captured at the edges
of the Z-stack.
