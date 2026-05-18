"""
watch_system.py — Live terminal monitor for GPU / CPU / RAM during training.

Prints a compact, in-place updating dashboard:

    [01:42:15]
    GPU util  [############........]  62%   68C  245/320W  fan 65%
    VRAM      [######..............]  4.2 / 16.0 GB
    CPU       [###.................]  15%
    RAM       [##########..........]  12.3 / 31.1 GB

Run in a separate terminal while training is going:
    python spring_implementation/training/watch_system.py

Ctrl-C to stop. Does not interact with the training process — only reads sensors.
"""

import argparse
import shutil
import subprocess
import sys
import time
from datetime import datetime

import psutil


GPU_QUERY = [
    "utilization.gpu",
    "memory.used",
    "memory.total",
    "temperature.gpu",
    "power.draw",
    "power.limit",
    "fan.speed",
]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", default=2.0, type=float,
                   help="Seconds between samples (default 2)")
    p.add_argument("--bar-width", default=20, type=int,
                   help="Width of each progress bar in chars (default 20)")
    return p.parse_args()


def read_gpu():
    """Return dict of GPU stats via nvidia-smi, or None on failure."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi",
             f"--query-gpu={','.join(GPU_QUERY)}",
             "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL, timeout=5,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    parts = [p.strip() for p in out.strip().splitlines()[0].split(",")]
    def _f(x):
        try: return float(x)
        except ValueError: return 0.0
    return {
        "util":      _f(parts[0]),
        "mem_used":  _f(parts[1]) / 1024.0,   # MiB -> GiB
        "mem_total": _f(parts[2]) / 1024.0,
        "temp":      _f(parts[3]),
        "power":     _f(parts[4]),
        "power_lim": _f(parts[5]),
        "fan":       _f(parts[6]),
    }


def bar(frac: float, width: int) -> str:
    frac = max(0.0, min(1.0, frac))
    filled = int(round(frac * width))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def main():
    args = parse_args()
    psutil.cpu_percent(interval=None)  # prime
    ram_total_gb = psutil.virtual_memory().total / 1024**3

    # 5 lines: timestamp + 4 metric rows
    n_lines = 5
    # Print blank lines once so we can move cursor up on every refresh
    sys.stdout.write("\n" * n_lines)

    try:
        while True:
            cpu = psutil.cpu_percent(interval=None)
            ram_used_gb = psutil.virtual_memory().used / 1024**3
            gpu = read_gpu()

            # Move cursor up to overwrite previous block
            sys.stdout.write(f"\033[{n_lines}A")

            ts = datetime.now().strftime("%H:%M:%S")
            lines = [f"[{ts}]"]

            w = args.bar_width
            if gpu is not None:
                lines.append(
                    f"GPU util  {bar(gpu['util']/100, w)}  {gpu['util']:3.0f}%   "
                    f"{gpu['temp']:.0f}C  {gpu['power']:.0f}/{gpu['power_lim']:.0f}W  "
                    f"fan {gpu['fan']:.0f}%"
                )
                lines.append(
                    f"VRAM      {bar(gpu['mem_used']/gpu['mem_total'], w)}  "
                    f"{gpu['mem_used']:.1f} / {gpu['mem_total']:.1f} GB"
                )
            else:
                lines.append("GPU util  (nvidia-smi unavailable)")
                lines.append("VRAM      (nvidia-smi unavailable)")

            lines.append(f"CPU       {bar(cpu/100, w)}  {cpu:3.0f}%")
            lines.append(
                f"RAM       {bar(ram_used_gb/ram_total_gb, w)}  "
                f"{ram_used_gb:.1f} / {ram_total_gb:.1f} GB  "
                f"({ram_used_gb/ram_total_gb*100:.0f}%)"
            )

            term_w = shutil.get_terminal_size((100, 20)).columns
            for line in lines:
                # Clear line then write, so shorter lines don't leave stale chars
                sys.stdout.write("\033[2K" + line[:term_w] + "\n")
            sys.stdout.flush()

            time.sleep(args.refresh)
    except KeyboardInterrupt:
        sys.stdout.write("\nStopped.\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
