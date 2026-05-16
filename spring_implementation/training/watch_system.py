"""
watch_system.py — Live monitor for GPU / CPU / RAM during training.

Plots a rolling window of:
    - GPU utilization (%)         (top-left)
    - GPU memory used (GB)        (top-right)
    - CPU load (%)                (bottom-left)
    - System RAM used (GB)        (bottom-right)

The window title shows current GPU temp, power draw, and fan speed.

Run in a separate terminal while training is going:
    python spring_implementation/training/watch_system.py

Close the window or Ctrl-C to stop. Does not interact with the training
process in any way — it only reads sensors.
"""

import argparse
import subprocess
import time
from collections import deque
from datetime import datetime

import matplotlib.pyplot as plt
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
    p.add_argument("--history", default=300, type=int,
                   help="Number of samples to keep on screen (default 300 = 10 min at 2s)")
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
    return {
        "util":      float(parts[0]),
        "mem_used":  float(parts[1]) / 1024.0,   # MiB -> GiB
        "mem_total": float(parts[2]) / 1024.0,
        "temp":      float(parts[3]),
        "power":     float(parts[4]),
        "power_lim": float(parts[5]),
        "fan":       float(parts[6]),
    }


def main():
    args = parse_args()

    # Prime psutil's CPU counter so the first reading isn't 0.0
    psutil.cpu_percent(interval=None)

    history = args.history
    t_hist        = deque(maxlen=history)
    gpu_util_hist = deque(maxlen=history)
    gpu_mem_hist  = deque(maxlen=history)
    cpu_hist      = deque(maxlen=history)
    ram_hist      = deque(maxlen=history)

    ram_total_gb = psutil.virtual_memory().total / 1024**3

    plt.ion()
    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    (ax_gpu, ax_vram), (ax_cpu, ax_ram) = axes

    line_gpu,  = ax_gpu.plot([],  [], "-", color="tab:green")
    line_vram, = ax_vram.plot([], [], "-", color="tab:purple")
    line_cpu,  = ax_cpu.plot([],  [], "-", color="tab:blue")
    line_ram,  = ax_ram.plot([],  [], "-", color="tab:red")

    for ax, ylabel, ymax in [
        (ax_gpu,  "GPU util (%)",     100),
        (ax_vram, "GPU VRAM (GB)",    None),  # set after first sample
        (ax_cpu,  "CPU load (%)",     100),
        (ax_ram,  "RAM used (GB)",    ram_total_gb),
    ]:
        ax.set_ylabel(ylabel)
        ax.set_xlabel("seconds ago")
        ax.grid(True, alpha=0.3)
        if ymax is not None:
            ax.set_ylim(0, ymax)

    fig.tight_layout()

    start = time.time()
    print(f"Sampling every {args.refresh:.1f}s, keeping last {history} samples")
    print(f"System RAM total: {ram_total_gb:.1f} GB")
    print("Close the window or Ctrl-C to stop.\n")

    gpu_warned = False

    while True:
        now = time.time() - start
        cpu = psutil.cpu_percent(interval=None)
        ram_used_gb = psutil.virtual_memory().used / 1024**3

        gpu = read_gpu()
        if gpu is None and not gpu_warned:
            print("nvidia-smi unavailable — GPU panels will stay empty")
            gpu_warned = True

        t_hist.append(now)
        cpu_hist.append(cpu)
        ram_hist.append(ram_used_gb)
        if gpu is not None:
            gpu_util_hist.append(gpu["util"])
            gpu_mem_hist.append(gpu["mem_used"])
            # Cap VRAM panel at total VRAM (only need to do this once we know it)
            if ax_vram.get_ylim()[1] != gpu["mem_total"]:
                ax_vram.set_ylim(0, gpu["mem_total"])

        # x-axis = seconds-ago, so the newest sample is at 0 and history scrolls left
        xs = [now - t for t in t_hist]
        line_cpu.set_data(xs, list(cpu_hist))
        line_ram.set_data(xs, list(ram_hist))
        if gpu_util_hist:
            # GPU history may be shorter if nvidia-smi briefly failed mid-run
            xs_gpu = xs[-len(gpu_util_hist):]
            line_gpu.set_data(xs_gpu, list(gpu_util_hist))
            line_vram.set_data(xs_gpu, list(gpu_mem_hist))

        window = args.refresh * history
        for ax in (ax_gpu, ax_vram, ax_cpu, ax_ram):
            ax.set_xlim(window, 0)  # inverted so 0 (now) is on the right

        # Per-panel titles with current value
        ax_cpu.set_title(f"CPU: {cpu:.0f}%")
        ax_ram.set_title(f"RAM: {ram_used_gb:.1f} / {ram_total_gb:.1f} GB "
                         f"({ram_used_gb/ram_total_gb*100:.0f}%)")
        if gpu is not None:
            ax_gpu.set_title(f"GPU util: {gpu['util']:.0f}%")
            ax_vram.set_title(f"VRAM: {gpu['mem_used']:.2f} / {gpu['mem_total']:.2f} GB")
            fig.suptitle(
                f"{datetime.now():%H:%M:%S}   "
                f"GPU temp {gpu['temp']:.0f}°C  |  "
                f"power {gpu['power']:.0f} / {gpu['power_lim']:.0f} W  |  "
                f"fan {gpu['fan']:.0f}%",
                fontsize=10,
            )
        else:
            ax_gpu.set_title("GPU util: n/a")
            ax_vram.set_title("VRAM: n/a")
            fig.suptitle(f"{datetime.now():%H:%M:%S}   GPU: nvidia-smi not available",
                         fontsize=10)

        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.05)

        if not plt.fignum_exists(fig.number):
            print("Window closed. Exiting.")
            return

        time.sleep(max(0.0, args.refresh - 0.05))


if __name__ == "__main__":
    main()
