def clamp(x):
    return max(0.0, min(1.0, x))

def compute_health(stats):
    rho = stats["avg_slice_load"]
    b = stats["block_ratio"]
    h = stats["handover_ratio"]
    c = stats["coverage_ratio"]
    l = stats["connected_ratio"]

    # Thresholds (policy knobs)
    RHO_SAFE = 0.8
    B_MAX = 0.1
    H_MAX = 0.02

    H_rho = 1.0 if rho <= RHO_SAFE else clamp(1 - (rho - RHO_SAFE) / (1 - RHO_SAFE))
    H_b = clamp(1 - b / B_MAX)
    H_h = clamp(1 - h / H_MAX)
    H_c = c
    H_l = l

    # Weighted health
    H = (
        0.35 * H_b +
        0.25 * H_rho +
        0.15 * H_h +
        0.15 * H_c +
        0.10 * H_l
    )

    return H
