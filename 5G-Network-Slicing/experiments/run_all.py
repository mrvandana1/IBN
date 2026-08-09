import yaml
import subprocess
import json
import copy
from pathlib import Path
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/home/mohan/Desktop/IBN/5G-Network-Slicing")
BASE_YAML = PROJECT_ROOT / "experiments/base_config.yaml"
RESULTS_DIR = PROJECT_ROOT / "experiments/results"
RESULTS_DIR.mkdir(exist_ok=True)

# -------------------------------
# Health model
# -------------------------------
def clamp(x):
    return max(0.0, min(1.0, x))

def compute_health(stats):
    rho = stats["avg_slice_load"]
    b = stats["block_ratio"]
    h = stats["handover_ratio"]
    c = stats["coverage_ratio"]
    l = stats["connected_ratio"]

    RHO_SAFE = 0.8
    B_MAX = 0.1
    H_MAX = 0.02

    H_rho = 1.0 if rho <= RHO_SAFE else clamp(1 - (rho - RHO_SAFE) / (1 - RHO_SAFE))
    H_b = clamp(1 - b / B_MAX)
    H_h = clamp(1 - h / H_MAX)
    H_c = c
    H_l = l

    return (
        0.35 * H_b +
        0.25 * H_rho +
        0.15 * H_h +
        0.15 * H_c +
        0.10 * H_l
    )

# -------------------------------
# Experiment runner
# -------------------------------
BANDWIDTH_SWEEP = [
    200,
    500,
    1000,
    1500,
    2000,
    3000,
    4000,
    6000,
    8000,
]


def run_slicesim(cfg_path):
    subprocess.run(
        ["python", "-m", "slicesim", cfg_path],
        cwd=PROJECT_ROOT,
        check=True
    )

def main():
    with open(BASE_YAML) as f:
        base_cfg = yaml.safe_load(f)

    dataset = []

    for bw in BANDWIDTH_SWEEP:
        print(f"\n=== Running for bandwidth_guaranteed = {bw} ===")
        cfg = copy.deepcopy(base_cfg)

        # ---- modify slice parameter ----
        cfg["slices"]["video_slice_unknown"]["bandwidth_guaranteed"] = bw

        # ---- DISABLE plotting for batch runs ----
        cfg["settings"]["plotting_params"]["plot_show"] = False
        cfg["settings"]["plotting_params"]["plot_save"] = False
        cfg["settings"]["plotting_params"]["plotting"] = False
        cfg["settings"]["logging"] = False

    
        cfg["slices"]["video_slice_unknown"]["bandwidth_guaranteed"] = bw

        cfg_file = RESULTS_DIR / f"cfg_bw_{bw}.yaml"
        with open(cfg_file, "w") as f:
            yaml.safe_dump(cfg, f)

        # Run SliceSim
        run_slicesim(str(cfg_file))

        # Read stats.json produced by SliceSim
        with open(PROJECT_ROOT / "stats.json") as sf:
            stats = json.load(sf)

        health = compute_health(stats)

        record = {
            "bandwidth_guaranteed": bw,
            **stats,
            "health": health
        }

        dataset.append(record)

    # Save dataset
    out_file = RESULTS_DIR / "dataset.json"
    with open(out_file, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"\nDataset saved to {out_file}")

    # -------------------------------
    # Plot relations
    # -------------------------------
    bw = [d["bandwidth_guaranteed"] for d in dataset]
    block = [d["block_ratio"] for d in dataset]
    health = [d["health"] for d in dataset]
    load = [d["avg_slice_load"] for d in dataset]

    plt.figure()
    plt.plot(bw, block, marker="o")
    plt.xlabel("Bandwidth Guaranteed")
    plt.ylabel("Block Ratio")
    plt.title("Bandwidth vs Block Ratio")
    plt.grid()
    plt.show()

    plt.figure()
    plt.plot(bw, health, marker="o")
    plt.xlabel("Bandwidth Guaranteed")
    plt.ylabel("Health Score")
    plt.title("Bandwidth vs Health")
    plt.grid()
    plt.show()

    plt.figure()
    plt.plot(load, block, marker="o")
    plt.xlabel("Slice Load")
    plt.ylabel("Block Ratio")
    plt.title("Load vs Block Ratio")
    plt.grid()
    plt.show()

if __name__ == "__main__":
    main()
