---
tags: [reference, construct, JABr]
construct: JABr
regions: [cytoplasmic, nuclear]
n_cytoplasmic: 30
n_nuclear: 30
---

# JABr Reference Data

Source: Box › Condensate Volume Quantification › JABr
See also: [[JABr Experiments]]

## Cytoplasmic

| File         | Condensate Density | Dilute Density | Partition Coefficient |
| ------------ | ------------------ | -------------- | --------------------- |
| Sample1_1_1  | 614.56             | 79.99          | 7.683                 |
| Sample1_1_2  | 972.96             | 160.44         | 6.064                 |
| Sample1_1_3  | 265.66             | 75.78          | 3.505                 |
| Sample1_1_4  | 567.86             | 73.77          | 7.698                 |
| Sample1_2_1  | 325.21             | 66.05          | 4.924                 |
| Sample1_2_2  | 174.05             | 71.28          | 2.442                 |
| Sample1_2_3  | 99.17              | 56.51          | 1.755                 |
| Sample1_4_1  | 235.26             | 59.68          | 3.942                 |
| Sample1_4_2  | 243.07             | 74.47          | 3.264                 |
| Sample1_4_3  | 234.73             | 62.48          | 3.757                 |
| Sample1_4_4  | 283.53             | 57.32          | 4.946                 |
| Sample2_5_1  | 411.70             | 85.14          | 4.836                 |
| Sample2_5_2  | 212.39             | 61.12          | 3.475                 |
| Sample2_5_3  | 289.37             | 70.18          | 4.123                 |
| Sample2_5_4  | 298.08             | 73.13          | 4.076                 |
| Sample2_5_5  | 259.89             | 62.52          | 4.157                 |
| Sample2_5_6  | 388.44             | 67.07          | 5.791                 |
| Sample3_3_1  | 280.76             | 62.75          | 4.475                 |
| Sample3_3_2  | 154.32             | 68.10          | 2.266                 |
| Sample3_3_3  | 468.87             | 68.28          | 6.867                 |
| Sample3_3_4  | 237.35             | 69.67          | 3.407                 |
| Sample3_3_5  | 787.46             | 66.95          | 11.761                |
| Sample3_3_6  | 226.58             | 82.30          | 2.753                 |
| Sample3_3_7  | 317.80             | 63.43          | 5.010                 |
| Sample3_3_8  | 411.18             | 65.28          | 6.298                 |
| Sample3_3_9  | 233.25             | 71.88          | 3.245                 |
| Sample3_3_10 | 1351.58            | 93.56          | 14.446                |
| Sample3_3_11 | 658.92             | 92.78          | 7.102                 |
| Sample3_3_14 | 212.48             | 66.59          | 3.191                 |
| Sample3_3_15 | 110.00             | 67.56          | 1.628                 |

## Nuclear

| File         | Condensate Density | Dilute Density | Partition Coefficient |
| ------------ | ------------------ | -------------- | --------------------- |
| Sample1_1_1  | 390.42             | 81.67          | 4.780                 |
| Sample1_1_2  | 827.87             | 91.60          | 9.038                 |
| Sample1_1_3  | 1516.55            | 76.69          | 19.774                |
| Sample1_1_4  | 793.32             | 74.96          | 10.584                |
| Sample1_2_1  | 619.05             | 77.16          | 8.023                 |
| Sample1_2_2  | 339.36             | 73.78          | 4.599                 |
| Sample1_2_3  | 162.87             | 63.99          | 2.545                 |
| Sample1_4_1  | 540.60             | 88.20          | 6.129                 |
| Sample1_4_2  | 368.83             | 73.05          | 5.049                 |
| Sample1_4_3  | 1338.28            | 95.84          | 13.963                |
| Sample1_4_4  | 584.31             | 62.68          | 9.322                 |
| Sample2_5_1  | 658.30             | 104.09         | 6.324                 |
| Sample2_5_2  | 483.19             | 70.30          | 6.873                 |
| Sample2_5_3  | 331.24             | 72.67          | 4.558                 |
| Sample2_5_4  | 415.30             | 68.99          | 6.020                 |
| Sample2_5_5  | 497.00             | 73.88          | 6.728                 |
| Sample2_5_6  | 894.09             | 73.58          | 12.151                |
| Sample3_3_1  | 534.27             | 65.28          | 8.185                 |
| Sample3_3_2  | 633.55             | 70.04          | 9.045                 |
| Sample3_3_3  | 788.77             | 89.38          | 8.825                 |
| Sample3_3_4  | 481.04             | 72.90          | 6.599                 |
| Sample3_3_5  | 627.55             | 74.59          | 8.413                 |
| Sample3_3_6  | 1365.81            | 107.64         | 12.689                |
| Sample3_3_7  | 719.19             | 82.84          | 8.681                 |
| Sample3_3_8  | 607.50             | 73.24          | 8.295                 |
| Sample3_3_9  | 455.50             | 76.94          | 5.920                 |
| Sample3_3_10 | 205.48             | 56.92          | 3.610                 |
| Sample3_3_11 | 1361.65            | 80.33          | 16.951                |
| Sample3_3_14 | 907.64             | 69.99          | 12.969                |
| Sample3_3_15 | 426.20             | 66.50          | 6.409                 |

## Pipeline — Nuclear (blob_log, current production)

Detector: `blob_log` threshold=0.03, min_sigma=1.5, max_sigma=6.0, num_sigma=8. Nuclei via Cellpose `cyto3` + connected-component relabel **+ per-nucleus void-filling** (`binary_fill_holes`, 3D + per-slice 2D) so condensates sitting in the donut holes Cellpose carves around them count as intra-nuclear. Calibration: linear `0.3540 * raw_pc + 2.9816` (full-data fit on JABr; LOO-CV MAE 14.6%). Source CSV: `spring_implementation/outputs/blob_JABr_filled/comparison.csv`. n=28 (Sample3_3_10 and Sample3_3_15 are in the reference but were skipped by the run — likely no transfected cell / segmentation failure).

Void-filling is PC-neutral vs the pre-fill production run (`blob_JABr_thresh03`): r, MAE, and within-±20% are unchanged; the largest single-ROI PC change is +0.95 (Sample3_3_5) and most move <0.2, both directions. Most condensate centroids already fell inside the nucleus mask even with the holes, so filling mainly makes the masks solid for review without distorting the metric.

| File         | Pipeline Cond Density | Pipeline Dilute Density | Background | Raw PC | Calibrated PC | Ref PC | \|err\|% |
| ------------ | --------------------- | ----------------------- | ---------- | ------ | ------------- | ------ | -------- |
| Sample1_1_1  | 588.5                 | 56.6                    | 89         | 10.39  | 6.66          | 4.78   | 39.3%    |
| Sample1_1_2  | 1151.2                | 64.7                    | 93         | 17.80  | 9.28          | 9.04   | 2.7%     |
| Sample1_1_3  | 2168.3                | 47.9                    | 99         | 45.28  | 19.01         | 19.77  | 3.9%     |
| Sample1_1_4  | 1369.7                | 53.8                    | 92         | 25.45  | 11.99         | 10.58  | 13.3%    |
| Sample1_2_1  | 632.2                 | 55.5                    | 92         | 11.40  | 7.02          | 8.02   | 12.6%    |
| Sample1_2_2  | 350.7                 | 63.1                    | 87         | 5.55   | 4.95          | 4.60   | 7.6%     |
| Sample1_2_3  | 162.1                 | 53.2                    | 95         | 3.05   | 4.06          | 2.55   | 59.5%    |
| Sample1_4_1  | 573.6                 | 54.8                    | 92         | 10.47  | 6.69          | 6.13   | 9.1%     |
| Sample1_4_2  | 364.0                 | 65.6                    | 87         | 5.55   | 4.95          | 5.05   | 2.0%     |
| Sample1_4_3  | 1765.7                | 58.1                    | 88         | 30.39  | 13.74         | 13.96  | 1.6%     |
| Sample1_4_4  | 957.1                 | 49.9                    | 91         | 19.19  | 9.78          | 9.32   | 4.9%     |
| Sample2_5_1  | 606.5                 | 70.1                    | 76         | 8.65   | 6.04          | 6.32   | 4.4%     |
| Sample2_5_2  | 544.3                 | 63.3                    | 84         | 8.60   | 6.02          | 6.87   | 12.4%    |
| Sample2_5_3  | 319.5                 | 71.4                    | 79         | 4.47   | 4.57          | 4.56   | 0.2%     |
| Sample2_5_4  | 414.2                 | 60.1                    | 86         | 6.89   | 5.42          | 6.02   | 10.0%    |
| Sample2_5_5  | 1260.0                | 58.5                    | 84         | 21.53  | 10.60         | 6.73   | 57.6%    |
| Sample2_5_6  | 1083.0                | 64.0                    | 82         | 16.92  | 8.97          | 12.15  | 26.2%    |
| Sample3_3_1  | 797.3                 | 54.9                    | 88         | 14.53  | 8.12          | 8.18   | 0.7%     |
| Sample3_3_11 | 2109.4                | 56.0                    | 84         | 37.68  | 16.32         | 16.95  | 3.7%     |
| Sample3_3_14 | 1149.6                | 59.2                    | 85         | 19.42  | 9.86          | 12.97  | 24.0%    |
| Sample3_3_2  | 689.3                 | 63.4                    | 89         | 10.88  | 6.83          | 9.05   | 24.5%    |
| Sample3_3_3  | 1361.7                | 59.2                    | 88         | 23.01  | 11.13         | 8.82   | 26.1%    |
| Sample3_3_4  | 453.8                 | 55.8                    | 89         | 8.13   | 5.86          | 6.60   | 11.2%    |
| Sample3_3_5  | 876.9                 | 53.3                    | 86         | 16.44  | 8.80          | 8.41   | 4.6%     |
| Sample3_3_6  | 1610.5                | 58.2                    | 88         | 27.68  | 12.78         | 12.69  | 0.7%     |
| Sample3_3_7  | 1018.8                | 56.8                    | 89         | 17.93  | 9.33          | 8.68   | 7.5%     |
| Sample3_3_8  | 814.6                 | 59.3                    | 87         | 13.73  | 7.84          | 8.29   | 5.4%     |
| Sample3_3_9  | 482.8                 | 49.6                    | 90         | 9.73   | 6.42          | 5.92   | 8.5%     |

**Summary:** n=28, mean \|err\| = 13.7%, 21/28 within ±20%, Pearson r = 0.926.

**Notable failures (>30% error):**
- Sample1_1_1 (+39%): pipeline dilute (56.6) < background (89) → bad nucleus mask drifting into dim region. Both blob_log and Cellpose V3 fail here.
- Sample1_2_3 (+60%): smallest ref PC (2.55) → calibration intercept dominates. Linear cal floor at intercept=2.98 makes %-error large even though absolute error is only 1.5 PC units.
- Sample2_5_5 (+58%): pipeline dilute (58.5) < background (84) **and** blob_log cond density inflated to 1260 vs ref 497 (Cellpose V3 gives 633 here — V3 is closer for this ROI specifically). Void-filling does not change this ROI's cond density.

The dilute < background pattern is a nucleus-mask quality issue, not a detector issue. See [[JABr Experiments#Bad Cases]] for full failure-mode notes.
## Visual Panels

Per-ROI 6-panel figures (max-intensity Z-projection): merged reference (nuc=cyan, cond=magenta) | nuclei channel | condensate channel | pipeline nuclei mask | pipeline condensate mask | classification overlay (brown=background, blue=dilute nuclear, green=condensate).

### Sample1_1_1  —  ref PC = 4.78  |  calibrated = 6.67  |  err = 39.4%

![[jabr_panels/Sample1_1_1.png]]

### Sample1_1_2  —  ref PC = 9.04  |  calibrated = 9.30  |  err = 2.9%

![[jabr_panels/Sample1_1_2.png]]

### Sample1_1_3  —  ref PC = 19.77  |  calibrated = 19.02  |  err = 3.8%

![[jabr_panels/Sample1_1_3.png]]

### Sample1_1_4  —  ref PC = 10.58  |  calibrated = 11.93  |  err = 12.8%

![[jabr_panels/Sample1_1_4.png]]

### Sample1_2_1  —  ref PC = 8.02  |  calibrated = 7.02  |  err = 12.5%

![[jabr_panels/Sample1_2_1.png]]

### Sample1_2_2  —  ref PC = 4.60  |  calibrated = 4.95  |  err = 7.7%

![[jabr_panels/Sample1_2_2.png]]

### Sample1_2_3  —  ref PC = 2.55  |  calibrated = 4.07  |  err = 59.8%

![[jabr_panels/Sample1_2_3.png]]

### Sample1_4_1  —  ref PC = 6.13  |  calibrated = 6.69  |  err = 9.2%

![[jabr_panels/Sample1_4_1.png]]

### Sample1_4_2  —  ref PC = 5.05  |  calibrated = 4.96  |  err = 1.8%

![[jabr_panels/Sample1_4_2.png]]

### Sample1_4_3  —  ref PC = 13.96  |  calibrated = 13.75  |  err = 1.5%

![[jabr_panels/Sample1_4_3.png]]

### Sample1_4_4  —  ref PC = 9.32  |  calibrated = 9.78  |  err = 4.9%

![[jabr_panels/Sample1_4_4.png]]

### Sample2_5_1  —  ref PC = 6.32  |  calibrated = 6.05  |  err = 4.4%

![[jabr_panels/Sample2_5_1.png]]

### Sample2_5_2  —  ref PC = 6.87  |  calibrated = 6.03  |  err = 12.3%

![[jabr_panels/Sample2_5_2.png]]

### Sample2_5_3  —  ref PC = 4.56  |  calibrated = 4.56  |  err = 0.1%

![[jabr_panels/Sample2_5_3.png]]

### Sample2_5_4  —  ref PC = 6.02  |  calibrated = 5.39  |  err = 10.4%

![[jabr_panels/Sample2_5_4.png]]

### Sample2_5_5  —  ref PC = 6.73  |  calibrated = 10.61  |  err = 57.7%

![[jabr_panels/Sample2_5_5.png]]

### Sample2_5_6  —  ref PC = 12.15  |  calibrated = 8.98  |  err = 26.1% okay

![[jabr_panels/Sample2_5_6.png]]

### Sample3_3_1  —  ref PC = 8.18  |  calibrated = 8.39  |  err = 2.5%
check why the 3rd condensate was not captured

![[jabr_panels/Sample3_3_1.png]]

### Sample3_3_11  —  ref PC = 16.95  |  calibrated = 16.33  |  err = 3.7%

![[jabr_panels/Sample3_3_11.png]]

### Sample3_3_14  —  ref PC = 12.97  |  calibrated = 9.86  |  err = 23.9%

![[jabr_panels/Sample3_3_14.png]]

### Sample3_3_2  —  ref PC = 9.05  |  calibrated = 6.84  |  err = 24.4%

![[jabr_panels/Sample3_3_2.png]]

### Sample3_3_3  —  ref PC = 8.82  |  calibrated = 11.16  |  err = 26.4%

![[jabr_panels/Sample3_3_3.png]]

### Sample3_3_4  —  ref PC = 6.60  |  calibrated = 5.83  |  err = 11.7%

![[jabr_panels/Sample3_3_4.png]]

### Sample3_3_5  —  ref PC = 8.41  |  calibrated = 8.47  |  err = 0.7%

![[jabr_panels/Sample3_3_5.png]]

### Sample3_3_6  —  ref PC = 12.69  |  calibrated = 12.79  |  err = 0.8%

![[jabr_panels/Sample3_3_6.png]]

### Sample3_3_7  —  ref PC = 8.68  |  calibrated = 9.34  |  err = 7.6%

![[jabr_panels/Sample3_3_7.png]]

### Sample3_3_8  —  ref PC = 8.29  |  calibrated = 7.78  |  err = 6.2%

![[jabr_panels/Sample3_3_8.png]]

### Sample3_3_9  —  ref PC = 5.92  |  calibrated = 6.50  |  err = 9.8%

![[jabr_panels/Sample3_3_9.png]]

