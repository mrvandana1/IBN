import yaml
import subprocess
import json
import copy
from pathlib import Path

BASE_YAML = "base_config.yaml"
OUTPUT_DIR = Path("experiment_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# Sweep space
BANDWIDTH_VALUES = [500, 1000, 2000, 3000, 4000]
RUNS_PER_CONFIG = 1   # increase later if needed

def run_slicesim(config_path):
    """
    Runs SliceSim and assumes stats are dumped to stats.json
    """
    subprocess.run(
        ["python", "-m", "slicesim", config_path],
        check=True
    )

def main():
    with open(BASE_YAML) as f:
        base_cfg = yaml.safe_load(f)

    all_results = []

    for bw in BANDWIDTH_VALUES:
        for run_id in range(RUNS_PER_CONFIG):

            cfg = copy.deepcopy(base_cfg)

            # MODIFY PARAMETER (example: video slice bandwidth)
            cfg["slices"]["video_slice_unknown"]["bandwidth_guaranteed"] = bw

            cfg_name = f"bw_{bw}_run_{run_id}.yaml"
            cfg_path = OUTPUT_DIR / cfg_name

            with open(cfg_path, "w") as f:
                yaml.safe_dump(cfg, f)

            # Run simulator
            run_slicesim(str(cfg_path))

            # Read stats dumped by SliceSim
            with open("stats.json") as sf:
                stats = json.load(sf)

            record = {
                "bandwidth_guaranteed": bw,
                "block_ratio": stats["block_ratio"],
                "handover_ratio": stats["handover_ratio"],
                "slice_load": stats["avg_slice_load"],
                "connected_ratio": stats["connected_ratio"],
                "coverage_ratio": stats["coverage_ratio"]
            }

            all_results.append(record)

    # Save all results
    with open(OUTPUT_DIR / "dataset.json", "w") as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    main()
