"""
analyze_calibration.py — Per-construct accuracy with the best calibration
+ optional ensemble that's available.

For each construct: load the trained+tuned comparison.csv, and (when
available) the cyto3 baseline csv. Try linear, isotonic, and ensemble
calibrations under leave-one-out cross-validation. Report the best
per-construct combination and its accuracy table.

Usage:
    python spring_implementation/analyze_calibration.py
"""

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression


EXPERIMENTS = Path(__file__).parent / "outputs" / "experiments"

# (construct, trained_dir, cyto3_dir_for_ensemble_or_None)
CONSTRUCTS = [
    ("JABr",      "batch_JABr_trained_tuned",      "batch_JABr_overlap"),
    ("GABr",      "batch_GABr_trained_tuned",      None),
    ("AABr",      "batch_AABr_trained_tuned",      None),
    ("JABr_4arm", "batch_JABr_4arm_trained_tuned", None),
    ("Tornado",   "batch_Tornado_trained_tuned",   "batch_Tornado_cyto3"),
]


def metrics(ref: np.ndarray, pred: np.ndarray) -> dict:
    err = np.abs(pred - ref) / ref * 100
    return dict(
        n=len(ref),
        r=float(np.corrcoef(ref, pred)[0, 1]),
        rmse=float(np.sqrt(((pred - ref) ** 2).mean())),
        mean_abs_err_pct=float(err.mean()),
        within_20=float((err <= 20).mean() * 100),
    )


def loo_calibrate(pred: np.ndarray, ref: np.ndarray, kind: str) -> np.ndarray:
    n = len(pred); out = np.zeros(n)
    for i in range(n):
        m = np.ones(n, bool); m[i] = False
        p_fit, r_fit, x = pred[m], ref[m], pred[i]
        if kind == "linear":
            a, b = np.polyfit(p_fit, r_fit, 1)
            out[i] = a * x + b
        elif kind == "isotonic":
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(p_fit, r_fit)
            out[i] = float(iso.predict([x])[0])
        else:
            raise ValueError(kind)
    return out


def fit_full(pred: np.ndarray, ref: np.ndarray, kind: str):
    if kind == "linear":
        a, b = np.polyfit(pred, ref, 1)
        return {"kind": "linear", "slope": float(a), "intercept": float(b)}
    elif kind == "isotonic":
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(pred, ref)
        # Store sorted (x, y) for reproducibility
        idx = np.argsort(pred)
        return {"kind": "isotonic",
                "xs": pred[idx].tolist(),
                "ys": iso.predict(pred[idx]).tolist()}
    raise ValueError(kind)


def try_strategies(trained: np.ndarray, ref: np.ndarray,
                   cyto3: np.ndarray | None = None) -> list[dict]:
    """Return list of (label, calibrated_predictions, metrics)."""
    out = []
    out.append(("trained + linear",   loo_calibrate(trained, ref, "linear")))
    out.append(("trained + isotonic", loo_calibrate(trained, ref, "isotonic")))
    if cyto3 is not None:
        for w in (0.3, 0.5, 0.7):
            mix = cyto3 * (1 - w) + trained * w
            out.append((f"mix({w:.1f}t,{1-w:.1f}c) + linear",
                       loo_calibrate(mix, ref, "linear")))
            out.append((f"mix({w:.1f}t,{1-w:.1f}c) + isotonic",
                       loo_calibrate(mix, ref, "isotonic")))
    return [(label, pred, metrics(ref, pred)) for label, pred in out]


def main():
    rows = []
    print("Loading construct results...\n")
    for label, trained_dir, cyto3_dir in CONSTRUCTS:
        tpath = EXPERIMENTS / trained_dir / "comparison.csv"
        if not tpath.exists():
            print(f"  [MISSING] {tpath}")
            continue

        tdf = pd.read_csv(tpath).dropna(subset=["pipeline_pc"]).set_index("filename")
        cdf = None
        if cyto3_dir is not None:
            cpath = EXPERIMENTS / cyto3_dir / "comparison.csv"
            if cpath.exists():
                cdf = pd.read_csv(cpath).dropna(subset=["pipeline_pc"]).set_index("filename")
                tdf, cdf = tdf.align(cdf, join="inner", axis=0)

        ref     = tdf["ref_pc"].to_numpy()
        trained = tdf["pipeline_pc"].to_numpy()
        cyto3   = cdf["pipeline_pc"].to_numpy() if cdf is not None else None

        base = metrics(ref, trained)
        results = try_strategies(trained, ref, cyto3)
        # Best by r, then RMSE
        results.sort(key=lambda x: (-x[2]["r"], x[2]["rmse"]))
        best_label, best_pred, best_m = results[0]

        rows.append({
            "construct":    label,
            "n":            base["n"],
            "r_raw":        base["r"],
            "rmse_raw":     base["rmse"],
            "err%_raw":     base["mean_abs_err_pct"],
            "in20%_raw":    base["within_20"],
            "best_strategy": best_label,
            "r_best":       best_m["r"],
            "rmse_best":    best_m["rmse"],
            "err%_best":    best_m["mean_abs_err_pct"],
            "in20%_best":   best_m["within_20"],
        })

        print(f"=== {label}  (n={base['n']}) ===")
        print(f"  raw trained:              r={base['r']:.3f}  RMSE={base['rmse']:.2f}  err%={base['mean_abs_err_pct']:5.1f}  in20%={base['within_20']:5.1f}")
        for lbl, _, m in results:
            print(f"  {lbl:30s}  r={m['r']:.3f}  RMSE={m['rmse']:.2f}  err%={m['mean_abs_err_pct']:5.1f}  in20%={m['within_20']:5.1f}")
        print(f"  -> BEST: {best_label}\n")

    if not rows:
        print("\nNo results yet.")
        return

    df = pd.DataFrame(rows)
    print("="*92)
    print("SUMMARY — best per-construct combination (leave-one-out cross-validated)")
    print("="*92)
    print(df[["construct","n","r_raw","r_best","err%_best","in20%_best","best_strategy"]]
          .to_string(index=False, float_format=lambda x: f"{x:.2f}"))

    # Success criteria check
    print("\n" + "="*92)
    print("SUCCESS CRITERIA (after best calibration)")
    print("  r >= 0.92,  mean abs err <= 10%,  >= 80% within 20%")
    print("="*92)
    for _, r in df.iterrows():
        g1 = "OK" if r["r_best"]    >= 0.92 else "FAIL"
        g2 = "OK" if r["err%_best"] <= 10   else "FAIL"
        g3 = "OK" if r["in20%_best"] >= 80   else "FAIL"
        print(f"  {r['construct']:12s}  r={r['r_best']:.3f} {g1}   "
              f"err={r['err%_best']:5.1f}% {g2}   "
              f"in20%={r['in20%_best']:5.1f}% {g3}")

    df.to_csv(EXPERIMENTS.parent / "calibration_summary.csv", index=False)
    print(f"\nSaved: {EXPERIMENTS.parent / 'calibration_summary.csv'}")

    # Save full-set isotonic fit per construct -> calibration_table.json
    # for pipeline.py to load at runtime.
    import json
    cal_table = {}
    for label, trained_dir, cyto3_dir in CONSTRUCTS:
        tpath = EXPERIMENTS / trained_dir / "comparison.csv"
        if not tpath.exists(): continue
        tdf = pd.read_csv(tpath).dropna(subset=["pipeline_pc"]).set_index("filename")
        ref     = tdf["ref_pc"].to_numpy()
        trained = tdf["pipeline_pc"].to_numpy()
        # Use trained + isotonic as the shipped calibrator (no ensemble at
        # inference time — keeps pipeline simple).
        idx = np.argsort(trained)
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(trained, ref)
        cal_table[label] = {
            "kind": "isotonic",
            "xs":   trained[idx].tolist(),
            "ys":   iso.predict(trained[idx]).tolist(),
        }
    out_json = EXPERIMENTS.parent / "calibration_table.json"
    out_json.write_text(json.dumps(cal_table, indent=2))
    print(f"Saved: {out_json}  ({len(cal_table)} constructs)")


if __name__ == "__main__":
    main()
