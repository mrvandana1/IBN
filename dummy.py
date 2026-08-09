from influxdb import InfluxDBClient
import time

client = InfluxDBClient(host="localhost", port=8086)
client.switch_database("rasa_slices")

def now():
    return int(time.time() * 1e9)

def insert(points, label):
    print(f"\n--- {label} ---")
    client.write_points(points)
    print(f"{len(points)} points inserted.")

# =========================================================
# NETWORK SLICE TABLE
# =========================================================
def seed_network_slices():
    points = [

        # ✅ REUSE CASE (good slice)
        {
            "measurement": "network_slice",
            "time": now(),
            "tags": {
                "slice_id": "slice_reuse1",
                "service_type": "video"
            },
            "fields": {
                "bandwidth": int(100),
                "latency": int(5),
                "reliability": float(99.999),
                "duration": int(3)
            }
        },

        # ❗ MODIFY HIGH LOAD
        {
            "measurement": "network_slice",
            "time": now(),
            "tags": {
                "slice_id": "slice_mod_high",
                "service_type": "video"
            },
            "fields": {
                "bandwidth": int(100),
                "latency": int(5),
                "reliability": float(99.999),
                "duration": int(3)
            }
        },

        # ✅ MODIFY LOW UTIL
        {
            "measurement": "network_slice",
            "time": now(),
            "tags": {
                "slice_id": "slice_mod_low",
                "service_type": "video"
            },
            "fields": {
                "bandwidth": int(50),
                "latency": int(5),
                "reliability": float(99.999),
                "duration": int(3)
            }
        },

        # ✅ DELETE SAFE
        {
            "measurement": "network_slice",
            "time": now(),
            "tags": {
                "slice_id": "slice_delete_safe",
                "service_type": "video"
            },
            "fields": {
                "bandwidth": int(30),
                "latency": int(5),
                "reliability": float(99.999),
                "duration": int(3)
            }
        },

        # ❗ DELETE BLOCK (busy slice)
        {
            "measurement": "network_slice",
            "time": now(),
            "tags": {
                "slice_id": "slice_delete_busy",
                "service_type": "video"
            },
            "fields": {
                "bandwidth": int(100),
                "latency": int(5),
                "reliability": float(99.999),
                "duration": int(3)
            }
        }
    ]

    insert(points, "NETWORK SLICE SEEDED")


# =========================================================
# SLICE SIM RESULT TABLE
# IMPORTANT: ALL FIELDS MUST BE FLOATS (your engine casts float)
# =========================================================
def seed_sim_results():

    points = [

        # =========================
        # CREATE → REUSE
        # =========================
        {
            "measurement": "slice_sim_result",
            "time": now(),
            "fields": {
                "slice_name": "video_slice_slice_reuse1",
                "load_ratio": float(0.3),
                "success": float(0.95),
                "used_bandwidth": float(40),
                "connected_ratio": float(0.3)
            }
        },

        # =========================
        # CREATE → HIGH RISK
        # =========================
        {
            "measurement": "slice_sim_result",
            "time": now(),
            "fields": {
                "slice_name": "video_slice_slice_fail1",
                "load_ratio": float(0.9),
                "success": float(0.4),
                "used_bandwidth": float(90),
                "connected_ratio": float(0.8)
            }
        },

        # =========================
        # DELETE → SAFE
        # =========================
        {
            "measurement": "slice_sim_result",
            "time": now(),
            "fields": {
                "slice_name": "video_slice_slice_delete_safe",
                "load_ratio": float(0.2),
                "success": float(0.9),
                "used_bandwidth": float(20),
                "connected_ratio": float(0.2)
            }
        },

        # =========================
        # DELETE → BLOCK
        # =========================
        {
            "measurement": "slice_sim_result",
            "time": now(),
            "fields": {
                "slice_name": "video_slice_slice_delete_busy",
                "load_ratio": float(0.85),
                "success": float(0.95),
                "used_bandwidth": float(80),
                "connected_ratio": float(0.9)
            }
        },

        # =========================
        # MODIFY → HIGH LOAD
        # =========================
        {
            "measurement": "slice_sim_result",
            "time": now(),
            "fields": {
                "slice_name": "video_slice_slice_mod_high",
                "load_ratio": float(0.9),
                "success": float(0.85),
                "used_bandwidth": float(95),
                "connected_ratio": float(0.7)
            }
        },

        # =========================
        # MODIFY → LOW UTIL
        # =========================
        {
            "measurement": "slice_sim_result",
            "time": now(),
            "fields": {
                "slice_name": "video_slice_slice_mod_low",
                "load_ratio": float(0.3),
                "success": float(0.95),
                "used_bandwidth": float(20),
                "connected_ratio": float(0.2)
            }
        }
    ]

    insert(points, "SIM RESULTS SEEDED")


if __name__ == "__main__":
    seed_network_slices()
    seed_sim_results()
    print("\nDONE")