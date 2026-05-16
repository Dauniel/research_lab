"""
watch_training.py — Live plot of Cellpose training loss curves.

Tails ~/.cellpose/run.log, parses each epoch-summary line, and plots train_loss
and test_loss against epoch in a self-updating matplotlib window.

Run in a separate terminal while train_cellpose.py is running:
    python spring_implementation/training/watch_training.py

The window refreshes every 30 seconds. Close it any time — does not affect
the training process.
"""

import argparse
import re
import time
from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt


DEFAULT_LOG = Path.home() / ".cellpose" / "run.log"

# Matches lines like:
#   2026-05-15 00:53:42,633 [INFO] 0, train_loss=1.2522, test_loss=0.9319, LR=0.000000, time 378.20s
LOSS_RE = re.compile(
    r"(\d+),\s*train_loss=([\d.]+),\s*test_loss=([\d.]+),\s*LR=([\d.]+),\s*time\s*([\d.]+)s"
)
SAVE_RE = re.compile(r"saving network parameters to .*?(_epoch_\d+)?$")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--log",    default=DEFAULT_LOG, type=Path,
                   help="Path to ~/.cellpose/run.log")
    p.add_argument("--total",  default=150, type=int,
                   help="Total epoch count to scale x-axis + ETA")
    p.add_argument("--refresh", default=30, type=int,
                   help="Seconds between log polls (loss lines come every ~5 min)")
    return p.parse_args()


def parse_log(path: Path):
    epochs, train_l, test_l, times = [], [], [], []
    saves = 0
    if not path.exists():
        return epochs, train_l, test_l, times, saves
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = LOSS_RE.search(line)
            if m:
                epochs.append(int(m.group(1)))
                train_l.append(float(m.group(2)))
                test_l.append(float(m.group(3)))
                times.append(float(m.group(5)))
            elif "saving network parameters" in line:
                saves += 1
    return epochs, train_l, test_l, times, saves


def fmt_eta(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))


def main():
    args = parse_args()

    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    train_line, = ax.plot([], [], "o-", color="tab:blue",   label="train_loss", linewidth=1.6)
    val_line,   = ax.plot([], [], "o-", color="tab:orange", label="val_loss (test)", linewidth=1.6)
    best_marker = ax.axvline(x=0, color="green", linestyle=":", linewidth=1, alpha=0)

    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")
    ax.set_xlim(-2, args.total + 2)

    print(f"Watching: {args.log}")
    print(f"Total epochs target: {args.total}")
    print(f"Refresh every {args.refresh}s. Close the window or Ctrl-C to stop.\n")

    while True:
        epochs, train_l, test_l, times, saves = parse_log(args.log)

        if epochs:
            train_line.set_data(epochs, train_l)
            val_line.set_data(epochs, test_l)
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)

            # Mark the best-val-loss epoch with a vertical dashed line
            best_idx = min(range(len(test_l)), key=lambda i: test_l[i])
            best_marker.set_xdata([epochs[best_idx], epochs[best_idx]])
            best_marker.set_alpha(0.6)

            latest_epoch = epochs[-1]
            latest_time  = times[-1]
            # Cumulative time covers epochs 0..latest_epoch inclusive, so divide
            # by (latest_epoch + 1) — handles the epoch=0 case correctly.
            sec_per_epoch = latest_time / (latest_epoch + 1)
            remaining = max(0, args.total - 1 - latest_epoch)
            eta_sec = remaining * sec_per_epoch

            title = (
                f"Cellpose training  |  epoch {latest_epoch}/{args.total - 1}  "
                f"({(latest_epoch + 1) / args.total * 100:.1f}%)  |  "
                f"train={train_l[-1]:.4f}  val={test_l[-1]:.4f}  |  "
                f"best val={test_l[best_idx]:.4f} @ epoch {epochs[best_idx]}  |  "
                f"saves={saves}  |  ETA: {fmt_eta(eta_sec)}"
            )
            ax.set_title(title, fontsize=9)
        else:
            ax.set_title("Waiting for first loss line (epoch 5)...")

        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.5)

        # If the matplotlib window has been closed, exit cleanly
        if not plt.fignum_exists(fig.number):
            print("Window closed. Exiting.")
            return

        time.sleep(args.refresh)


if __name__ == "__main__":
    main()
