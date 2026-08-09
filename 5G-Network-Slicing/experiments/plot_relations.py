import json
import matplotlib.pyplot as plt

with open("experiment_results/dataset_with_health.json") as f:
    data = json.load(f)

bw = [d["bandwidth_guaranteed"] for d in data]
block = [d["block_ratio"] for d in data]
health = [d["health"] for d in data]
load = [d["slice_load"] for d in data]

plt.figure()
plt.plot(bw, block, marker='o')
plt.xlabel("Bandwidth Guaranteed")
plt.ylabel("Block Ratio")
plt.title("Bandwidth vs Block Ratio")
plt.show()

plt.figure()
plt.plot(bw, health, marker='o')
plt.xlabel("Bandwidth Guaranteed")
plt.ylabel("Health Score")
plt.title("Bandwidth vs Health")
plt.show()

plt.figure()
plt.plot(load, block, marker='o')
plt.xlabel("Slice Load")
plt.ylabel("Block Ratio")
plt.title("Load vs Block Ratio")
plt.show()
