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

Detector: `blob_log` threshold=0.03, min_sigma=1.5, max_sigma=6.0, num_sigma=8. Nuclei via Cellpose `cyto3` + connected-component relabel. Calibration: linear `0.3541 * raw_pc + 2.9867` (full-data fit on JABr; LOO-CV MAE 14.7%). Source CSV: `spring_implementation/outputs/blob_JABr_thresh03/comparison.csv`. n=28 (Sample3_3_10 and Sample3_3_15 are in the reference but were skipped by the run — likely no transfected cell / segmentation failure).

| File         | Pipeline Cond Density | Pipeline Dilute Density | Background | Raw PC | Calibrated PC | Ref PC | \|err\|% |
| ------------ | --------------------- | ----------------------- | ---------- | ------ | ------------- | ------ | -------- |
| Sample1_1_1  | 588.52                | 56.63                   | 89.0       | 10.39  | 6.67          | 4.780  | 39.4%    |
| Sample1_1_2  | 1152.43               | 64.67                   | 93.0       | 17.82  | 9.30          | 9.038  | 2.9%     |
| Sample1_1_3  | 2168.32               | 47.89                   | 99.0       | 45.28  | 19.02         | 19.774 | 3.8%     |
| Sample1_1_4  | 1370.80               | 54.25                   | 92.0       | 25.27  | 11.93         | 10.584 | 12.8%    |
| Sample1_2_1  | 632.42                | 55.47                   | 92.0       | 11.40  | 7.02          | 8.023  | 12.5%    |
| Sample1_2_2  | 350.67                | 63.13                   | 87.0       | 5.55   | 4.95          | 4.599  | 7.7%     |
| Sample1_2_3  | 162.46                | 53.22                   | 95.0       | 3.05   | 4.07          | 2.545  | 59.8%    |
| Sample1_4_1  | 573.61                | 54.81                   | 92.0       | 10.47  | 6.69          | 6.129  | 9.2%     |
| Sample1_4_2  | 364.90                | 65.57                   | 87.0       | 5.57   | 4.96          | 5.049  | 1.8%     |
| Sample1_4_3  | 1765.67               | 58.10                   | 88.0       | 30.39  | 13.75         | 13.963 | 1.5%     |
| Sample1_4_4  | 957.10                | 49.87                   | 91.0       | 19.19  | 9.78          | 9.322  | 4.9%     |
| Sample2_5_1  | 606.25                | 70.11                   | 76.0       | 8.65   | 6.05          | 6.324  | 4.4%     |
| Sample2_5_2  | 544.39                | 63.33                   | 84.0       | 8.60   | 6.03          | 6.873  | 12.3%    |
| Sample2_5_3  | 317.62                | 71.41                   | 79.0       | 4.45   | 4.56          | 4.558  | 0.1%     |
| Sample2_5_4  | 408.12                | 60.11                   | 86.0       | 6.79   | 5.39          | 6.020  | 10.4%    |
| Sample2_5_5  | 1260.20               | 58.53                   | 84.0       | 21.53  | 10.61         | 6.728  | 57.7%    |
| Sample2_5_6  | 1082.97               | 64.02                   | 82.0       | 16.92  | 8.98          | 12.151 | 26.1%    |
| Sample3_3_1  | 843.02                | 55.28                   | 88.0       | 15.25  | 8.39          | 8.185  | 2.5%     |
| Sample3_3_2  | 689.68                | 63.35                   | 89.0       | 10.89  | 6.84          | 9.045  | 24.4%    |
| Sample3_3_3  | 1365.21               | 59.18                   | 88.0       | 23.07  | 11.16         | 8.825  | 26.4%    |
| Sample3_3_4  | 447.92                | 55.83                   | 89.0       | 8.02   | 5.83          | 6.599  | 11.7%    |
| Sample3_3_5  | 826.29                | 53.34                   | 86.0       | 15.49  | 8.47          | 8.413  | 0.7%     |
| Sample3_3_6  | 1610.49               | 58.19                   | 88.0       | 27.68  | 12.79         | 12.689 | 0.8%     |
| Sample3_3_7  | 1019.07               | 56.81                   | 89.0       | 17.94  | 9.34          | 8.681  | 7.6%     |
| Sample3_3_8  | 803.08                | 59.32                   | 87.0       | 13.54  | 7.78          | 8.295  | 6.2%     |
| Sample3_3_9  | 492.43                | 49.65                   | 90.0       | 9.92   | 6.50          | 5.920  | 9.8%     |
| Sample3_3_11 | 2109.39               | 55.99                   | 84.0       | 37.68  | 16.33         | 16.951 | 3.7%     |
| Sample3_3_14 | 1149.57               | 59.18                   | 85.0       | 19.42  | 9.86          | 12.969 | 23.9%    |

**Summary:** n=28, mean \|err\| = 13.7%, 21/28 within ±20%, Pearson r ≈ 0.93.

**Notable failures (>30% error):**
- Sample1_1_1 (+39%): pipeline dilute (56.6) < background (89) → bad nucleus mask drifting into dim region. Both blob_log and Cellpose V3 fail here.
- Sample1_2_3 (+60%): smallest ref PC (2.55) → calibration intercept dominates. Linear cal floor at intercept=2.99 makes %-error large even though absolute error is only 1.5 PC units.
- Sample2_5_5 (+58%): pipeline dilute (58.5) < background (84) **and** blob_log cond density inflated to 1260 vs ref 497 (Cellpose V3 gives 633 here — V3 is closer for this ROI specifically).

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

### Sample2_5_6  —  ref PC = 12.15  |  calibrated = 8.98  |  err = 26.1%

![[jabr_panels/Sample2_5_6.png]]

### Sample3_3_1  —  ref PC = 8.18  |  calibrated = 8.39  |  err = 2.5%

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

