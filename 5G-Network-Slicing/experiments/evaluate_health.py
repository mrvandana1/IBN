import json
from health_model import compute_health

with open("experiment_results/dataset.json") as f:
    data = json.load(f)

for row in data:
    row["health"] = compute_health(row)

with open("experiment_results/dataset_with_health.json", "w") as f:
    json.dump(data, f, indent=2)
