$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$ROOT = "C:\Users\Danie\Box\Condensate Volume Quantification"
$OUT  = "C:\storage\code\research\spring_implementation\outputs\hybrid_smoketest"
$CKPT = "C:\storage\code\research\spring_implementation\training\models\models\cond_cyto3_v3_balanced_epoch_0035"
$PIPE = "C:\storage\code\research\spring_implementation\pipeline.py"
New-Item -ItemType Directory -Force $OUT | Out-Null

$cases = @(
  @{c="JABr";      f="JABr\Cut ROI\20240516_JABr_40uMDFHBI_20-40_Sample3_3_8.tif"; ref=8.29},
  @{c="GABr";      f="GABr\Cut ROI\20240525_GABr_40uMDFHBI_Sample3_3_4.tif";        ref=6.60},
  @{c="AABr";      f="AABr\Cut ROI\20240516_AABr_10uMDFHBI_20-40_Sample3_4_2.tif";  ref=12.20},
  @{c="JABr_4arm"; f="JABr_4arm\Cut ROI\20240525_JABr_4arm_40uMDFHBI_Sample3_2_1-1.tif"; ref=14.71},
  @{c="Tornado";   f="Tornado\Cut ROI\20240614_40uMDFHBI_Tornado_Broccoli_Sample3_1_1.tif"; ref=2.73}
)

foreach ($x in $cases) {
  $cdir = Join-Path $OUT $x.c
  New-Item -ItemType Directory -Force $cdir | Out-Null
  $roi = Join-Path $ROOT $x.f
  Write-Host "=== $($x.c) (ref=$($x.ref)) ==="
  $args = @("--roi", $roi, "--output", $cdir, "--construct", $x.c, "--detector", "auto",
            "--cond-model", $CKPT, "--cond-cellprob", "-2.0")
  python $PIPE @args 2>&1 | Tee-Object -FilePath (Join-Path $cdir "run.log")
}
Write-Host "DONE"
