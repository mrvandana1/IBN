from influxdb import InfluxDBClient
import yaml

client = InfluxDBClient(host="127.0.0.1", port=8086, database="rasa_slices")

# Query all slices stored in DB
results = client.query("SELECT * FROM network_slice")

# Load YAML
with open("example-input.yml", "r") as f:
    data = yaml.safe_load(f)

# ---------------------------
#  RESET SLICES SECTION
# ---------------------------
data["slices"] = {}
slice_keys = []

print("✔ Cleared old slice")

# ---------------------------
#  READ DB AND CREATE SLICES
# ---------------------------
#print(f"before loop")
for p in results.get_points():
    #print(f"after loop")
    slice_type = p.get("service_type") or "video"
    slice_id   = p.get("slice_id") or "unknown"

    yaml_key = f"{slice_type}_slice_{slice_id}"

    guaranteed  = p.get("bandwidth") or 500
    delay       = p.get("latency") or 5
    reliability = p.get("reliability") or 99.0
    #print(f"pretty print #########################################################################################")
    #print(f"Slice: {yaml_key} - Guaranteed: {guaranteed} - Delay: {delay} - Reliability: {reliability}")

    data["slices"][yaml_key] = {
        "bandwidth_guaranteed": guaranteed,
        "bandwidth_max": guaranteed * 100,
        "client_weight": 0.5,
        "delay_tolerance": delay,
        "qos_class": 3,
        "threshold": reliability / 100,
        "usage_pattern": {
            "distribution": "randint",
            "params": [4000000, 800000000]
        }
    }

    slice_keys.append(yaml_key)
    print(f"✔ Added slice: {yaml_key}")

# ---------------------------
#  REBUILD BASE-STATION RATIOS
# ---------------------------
if slice_keys:
    per_slice_ratio = round(1.0 / len(slice_keys), 4)

    for bs in data["base_stations"]:
        bs["ratios"] = {key: per_slice_ratio for key in slice_keys}

    print(f"✔ Updated base station ratios ({len(slice_keys)} slices)")

# Save YAML
with open("example-input.yml", "w") as f:
    yaml.dump(data, f, sort_keys=False)

print("✔ Sync complete!")
