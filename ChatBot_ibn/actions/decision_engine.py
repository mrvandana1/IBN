
# from influxdb import InfluxDBClient
# import re
# from statistics import mean
# from typing import Optional


# class DecisionEngine:

#     # ─────────────────────────────────────────────
#     # Lifecycle
#     # ─────────────────────────────────────────────

#     def __init__(self, host="127.0.0.1", port=8086, db="rasa_slices"):
#         self._host = host
#         self._port = port
#         self._db   = db
#         # Do NOT open a persistent connection here.
#         # InfluxDB connections are opened per-query and closed immediately
#         # so the long-running Rasa action server never leaks sockets.

#     def _get_client(self) -> InfluxDBClient:
#         client = InfluxDBClient(host=self._host, port=self._port)
#         client.switch_database(self._db)
#         return client

#     def _query(self, q: str) -> list:
#         """Execute a query, always close the connection, return list of points."""
#         client = self._get_client()
#         try:
#             result = client.query(q)
#             return list(result.get_points())
#         finally:
#             client.close()

#     # ─────────────────────────────────────────────
#     # Utility: string helpers
#     # ─────────────────────────────────────────────

#     def _normalize_service_type(self, service_type: Optional[str]) -> str:
#         if not service_type:
#             return "unknown"
#         return re.sub(r"\d+$", "", service_type.strip().lower())

#     def _parse_slice_name(self, slice_name: str):
#         """
#         Parses names of the form:  {service_type}_slice_{slice_id}
#         Real examples from DB:
#             video_slice_slice_reuse1      → ("video", "slice_reuse1")
#             video_slice_slice_delete_safe → ("video", "slice_delete_safe")

#         The format is always:
#             <everything before the FIRST "_slice_"> + "_slice_" + <the rest>

#         We split on the FIRST occurrence only to handle service types that
#         contain underscores (e.g. "nr_video").
#         """
#         if not slice_name or "_slice_" not in slice_name:
#             return "unknown", "unknown"

#         # Split on the first "_slice_" only
#         idx = slice_name.index("_slice_")
#         service_type = slice_name[:idx]
#         slice_id_part = slice_name[idx + len("_slice_"):]

#         if not service_type or not slice_id_part:
#             return "unknown", "unknown"

#         return service_type, slice_id_part

#     # ─────────────────────────────────────────────
#     # Utility: table formatter for advisory output
#     # ─────────────────────────────────────────────

#     def _format_table(self, points: list) -> str:
#         """
#         Render a list of slice_sim_result dicts as a clean ASCII table.
#         Only the columns that are actually useful for the advisory are shown.

#         Example output:
#         slice_name                     | success | load  | used_bw | connected
#         ------------------------------ | ------- | ----- | ------- | ---------
#         video_slice_slice_reuse1       |    0.95 |  0.30 |    40.0 |      0.30
#         video_slice_slice_fail1        |    0.40 |  0.90 |    90.0 |      0.80
#         """
#         if not points:
#             return "(no historical records found)"

#         cols = [
#             ("slice_name",      "slice_name",       "%-30s"),
#             ("success",         "success",           "%7.2f"),
#             ("load_ratio",      "load",              "%5.2f"),
#             ("used_bandwidth",  "used_bw",           "%7.1f"),
#             ("connected_ratio", "connected",         "%9.2f"),
#         ]

#         header_parts = []
#         sep_parts    = []
#         for field, label, fmt in cols:
#             # Determine column width from the format string
#             col_w = max(len(label), int(re.search(r"\d+", fmt).group()))
#             header_parts.append(label.ljust(col_w))
#             sep_parts.append("-" * col_w)

#         header = " | ".join(header_parts)
#         sep    = "-+-".join(sep_parts)

#         rows = []
#         for p in points:
#             cells = []
#             for field, label, fmt in cols:
#                 val = p.get(field, "")
#                 try:
#                     cells.append((fmt % float(val)).strip() if val != "" else "n/a")
#                 except (TypeError, ValueError):
#                     cells.append(str(val)[:30])
#             rows.append(" | ".join(cells))

#         return "\n".join([header, sep] + rows)

#     # ─────────────────────────────────────────────
#     # DB fetch: similar slices from slice_sim_result
#     # ─────────────────────────────────────────────

#     def _fetch_similar_slices(self, service_type: str) -> list:
#         """
#         Fetch all rows from slice_sim_result whose slice_name starts with
#         {service_type}_slice_.

#         slice_name is a FIELD in InfluxDB (not a tag), so we must use
#         a regex match.  The =~ operator in InfluxQL applies to string fields.
#         """
#         service_type = self._normalize_service_type(service_type)
#         # Safe: service_type has already been normalised to [a-z0-9_] only
#         # (normalize strips digits from end and lowercases — no injection surface)
#         pattern = f"^{re.escape(service_type)}_slice_"
#         q = f"SELECT * FROM slice_sim_result WHERE slice_name =~ /{pattern}/"
#         points = self._query(q)

#         # Secondary filter: reject rows whose slice_name we cannot parse
#         valid = []
#         for p in points:
#             stype, sid = self._parse_slice_name(p.get("slice_name", ""))
#             if stype != "unknown" and sid != "unknown":
#                 valid.append(p)
#         return valid

#     # ─────────────────────────────────────────────
#     # Bandwidth math (fixed)
#     # ─────────────────────────────────────────────

#     def _calc_free_bandwidth(self, used_bw: float, load_ratio: float) -> float:
#         """
#         The original code computed:   available = used_bw * (1 - load_ratio)
#         That is WRONG.

#         Correct reasoning:
#             load_ratio = used_bw / total_capacity
#             => total_capacity = used_bw / load_ratio   (when load_ratio > 0)
#             => free_bw = total_capacity - used_bw
#                        = used_bw / load_ratio - used_bw
#                        = used_bw * (1/load_ratio - 1)

#         Example with reuse1 row (used=40, load=0.3):
#             total = 40 / 0.3 = 133.3 Mbps
#             free  = 133.3 - 40 = 93.3 Mbps   ← correct
#             (original formula gave: 40 * 0.7 = 28 Mbps ← wrong)
#         """
#         if load_ratio <= 0:
#             # load_ratio == 0 means slice is completely idle;
#             # we cannot know total capacity, so treat as "unknown — don't reuse"
#             return 0.0
#         if load_ratio >= 1:
#             # Fully saturated
#             return 0.0
#         total_capacity = used_bw / load_ratio
#         return total_capacity - used_bw

#     # ─────────────────────────────────────────────
#     # CREATE — reuse detection
#     # ─────────────────────────────────────────────

#     def _find_reusable_slice(self, service_type: str, requested_bw: float) -> Optional[str]:
#         """
#         Return the slice_id of the first existing slice that has enough
#         free bandwidth to accommodate requested_bw, or None if none found.

#         Only slices with success >= 0.8 are considered for reuse to avoid
#         directing traffic to historically problematic slices.
#         """
#         points = self._fetch_similar_slices(service_type)

#         for p in points:
#             _, slice_id = self._parse_slice_name(p.get("slice_name", ""))
#             if slice_id == "unknown":
#                 continue

#             used_bw    = float(p.get("used_bandwidth", 0) or 0)
#             load_ratio = float(p.get("load_ratio", 1) or 1)
#             success    = float(p.get("success", 0) or 0)

#             # Skip slices with poor historical success
#             if success < 0.8:
#                 continue

#             free_bw = self._calc_free_bandwidth(used_bw, load_ratio)
#             if free_bw >= requested_bw:
#                 return slice_id

#         return None

#     # ─────────────────────────────────────────────
#     # PUBLIC: analyze_create
#     # ─────────────────────────────────────────────

#     def analyze_create(self, service_type: str, req_bandwidth: float) -> dict:
#         """
#         Advisory for creating (or reusing) a network slice.

#         Returns a dict with keys: decision, risk, message, [target_slice_id]
#         Always includes a table of historical similar slices when they exist.
#         """
#         service_type = self._normalize_service_type(service_type)

#         # Step 1: check for reusable slice
#         reusable = self._find_reusable_slice(service_type, req_bandwidth)
#         points   = self._fetch_similar_slices(service_type)
#         table    = self._format_table(points)

#         if reusable:
#             return {
#                 "decision":        "reuse",
#                 "risk":            "low",
#                 "target_slice_id": reusable,
#                 "message": (
#                     f"Existing slice '{reusable}' has enough free capacity "
#                     f"for {req_bandwidth} Mbps.\n\n"
#                     f"Historical similar slices:\n{table}"
#                 ),
#             }

#         # Step 2: no reusable slice — advise on creating a new one
#         if not points:
#             return {
#                 "decision": "create",
#                 "risk":     "low",
#                 "message":  "No historical data found. Safe exploratory creation.",
#             }

#         avg_success = mean(float(p.get("success",        0) or 0) for p in points)
#         avg_load    = mean(float(p.get("load_ratio",     0) or 0) for p in points)
#         avg_used    = mean(float(p.get("used_bandwidth", 0) or 0) for p in points)

#         base_stats = (
#             f"Avg success rate : {avg_success:.2f}\n"
#             f"Avg load ratio   : {avg_load:.2f}\n"
#             f"Avg used BW      : {avg_used:.1f} Mbps\n"
#             f"Requested BW     : {req_bandwidth} Mbps\n\n"
#             f"Historical similar slices:\n{table}"
#         )

#         if avg_success < 0.6:
#             return {
#                 "decision": "create",
#                 "risk":     "high",
#                 "message": (
#                     "Similar slices have a high failure rate.\n"
#                     "Consider reducing bandwidth or relaxing QoS constraints.\n\n"
#                     + base_stats
#                 ),
#             }

#         if avg_load > 0.85:
#             return {
#                 "decision": "create",
#                 "risk":     "high",
#                 "message":  "Network is heavily loaded. New slice creation is risky.\n\n" + base_stats,
#             }

#         return {
#             "decision": "create",
#             "risk":     "medium",
#             "message":  "Network conditions are moderate. Proceed with caution.\n\n" + base_stats,
#         }

#     # ─────────────────────────────────────────────
#     # PUBLIC: analyze_modify
#     # ─────────────────────────────────────────────

#     def analyze_modify(self, service_type: str, old_value: float, new_value: float) -> dict:
#         """
#         Advisory for modifying any numeric parameter on a slice.

#         The caller passes old_value / new_value for whichever parameter is
#         being changed (bandwidth, latency, reliability, or duration).
#         The network load context is always fetched from similar slices so
#         the advisory is meaningful regardless of which parameter changed.
#         """
#         service_type = self._normalize_service_type(service_type)
#         points       = self._fetch_similar_slices(service_type)
#         table        = self._format_table(points)

#         if not points:
#             return {
#                 "risk":    "medium",
#                 "message": "No historical data available. Impact of change is unknown.",
#             }

#         avg_load    = mean(float(p.get("load_ratio",     0) or 0) for p in points)
#         avg_used    = mean(float(p.get("used_bandwidth", 0) or 0) for p in points)
#         avg_success = mean(float(p.get("success",        0) or 0) for p in points)

#         base_stats = (
#             f"Avg load ratio   : {avg_load:.2f}\n"
#             f"Avg used BW      : {avg_used:.1f} Mbps\n"
#             f"Avg success rate : {avg_success:.2f}\n"
#             f"Old value        : {old_value}\n"
#             f"New value        : {new_value}\n\n"
#             f"Historical similar slices:\n{table}"
#         )

#         # Increasing a parameter (e.g. more bandwidth, higher reliability target)
#         if new_value > old_value:
#             if avg_load > 0.85:
#                 return {
#                     "risk": "high",
#                     "message": (
#                         "Network load is already high (avg load ratio > 0.85).\n"
#                         "Increasing this parameter may degrade network performance.\n\n"
#                         + base_stats
#                     ),
#                 }
#             return {
#                 "risk":    "medium",
#                 "message": "Increase is feasible under current load conditions.\n\n" + base_stats,
#             }

#         # Decreasing a parameter (e.g. reducing bandwidth)
#         if new_value < old_value:
#             if avg_used < old_value * 0.5:
#                 return {
#                     "risk":    "low",
#                     "message": "Slice appears underutilised. Safe to reduce.\n\n" + base_stats,
#                 }
#             return {
#                 "risk":    "medium",
#                 "message": (
#                     "Slice is actively used. Reducing this parameter may impact QoS.\n\n"
#                     + base_stats
#                 ),
#             }

#         # No change
#         return {
#             "risk":    "low",
#             "message": "Old and new values are identical. No change will be applied.\n\n" + base_stats,
#         }

#     # ─────────────────────────────────────────────
#     # PUBLIC: analyze_delete
#     # ─────────────────────────────────────────────

#     def analyze_delete(self, slice_name: str) -> dict:
#         """
#         Advisory for deleting a slice.

#         slice_name must be the full name as stored in slice_sim_result,
#         e.g. "video_slice_slice_1b60ff7f".

#         Queries the last 5 simulation results for this specific slice to
#         check whether it is actively used or carrying significant load.
#         """
#         # slice_name is passed in from actions.py which already validated
#         # slice_id via validate_id(), so the only injection surface is the
#         # service_type prefix — which is normalised to [a-z0-9_] by
#         # _normalize_service_type.  We still escape it in the regex for safety.
#         safe_name = re.escape(slice_name)
#         q = (
#             f"SELECT connected_ratio, load_ratio, success, used_bandwidth "
#             f"FROM slice_sim_result "
#             f"WHERE slice_name =~ /^{safe_name}$/ "
#             f"ORDER BY time DESC LIMIT 5"
#         )
#         points = self._query(q)
#         table  = self._format_table(points)

#         if not points:
#             return {
#                 "risk":    "low",
#                 "message": "No recent simulation data found for this slice. Safe to delete.",
#             }

#         avg_connected = mean(float(p.get("connected_ratio", 0) or 0) for p in points)
#         avg_load      = mean(float(p.get("load_ratio",      0) or 0) for p in points)
#         avg_success   = mean(float(p.get("success",         0) or 0) for p in points)

#         base_stats = (
#             f"Avg connected ratio : {avg_connected:.2f}\n"
#             f"Avg load ratio      : {avg_load:.2f}\n"
#             f"Avg success rate    : {avg_success:.2f}\n\n"
#             f"Recent slice activity:\n{table}"
#         )

#         # High connected ratio → active users will be dropped
#         if avg_connected > 0.7:
#             return {
#                 "risk": "high",
#                 "message": (
#                     f"Slice is actively serving users (connected ratio: {avg_connected:.2f}).\n"
#                     "Deletion will immediately impact connected devices.\n\n"
#                     + base_stats
#                 ),
#             }

#         # High load but lower connected ratio → slice is doing work but fewer users
#         if avg_load > 0.8:
#             return {
#                 "risk": "medium",
#                 "message": (
#                     f"Slice is under significant load (load ratio: {avg_load:.2f}).\n"
#                     "Monitor traffic before proceeding with deletion.\n\n"
#                     + base_stats
#                 ),
#             }

#         return {
#             "risk":    "low",
#             "message": "Slice has low utilisation and few active connections. Safe to delete.\n\n" + base_stats,
#         }

from influxdb import InfluxDBClient
import re
from statistics import mean
from typing import Optional


class DecisionEngine:
    """
    Provides advisory analysis for the three slice lifecycle operations:
      - analyze_create  → should the bot reuse an existing slice or create a new one?
      - analyze_modify  → what is the risk of changing a slice parameter?
      - analyze_delete  → is it safe to delete this slice?

    Each public method returns a dict with at minimum:
        {
            "risk":    "low" | "medium" | "high",
            "message": str,           # human-readable advisory
        }
    analyze_create also returns:
        {
            "decision":        "reuse" | "create",
            "target_slice_id": str,   # only present when decision == "reuse"
        }

    InfluxDB connections are opened per-query and closed immediately so the
    long-running Rasa action server never leaks sockets.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8086, db: str = "rasa_slices"):
        self._host = host
        self._port = port
        self._db   = db

    # ─────────────────────────────────────────────
    # Private: DB access
    # ─────────────────────────────────────────────

    def _get_client(self) -> InfluxDBClient:
        client = InfluxDBClient(host=self._host, port=self._port)
        client.switch_database(self._db)
        return client

    def _query(self, q: str) -> list:
        """Execute a query, always close the connection, return list of points."""
        client = self._get_client()
        try:
            result = client.query(q)
            return list(result.get_points())
        finally:
            client.close()

    # ─────────────────────────────────────────────
    # Private: string helpers
    # ─────────────────────────────────────────────

    def _normalize_service_type(self, service_type: Optional[str]) -> str:
        if not service_type:
            return "unknown"
        return re.sub(r"\d+$", "", service_type.strip().lower())

    def _parse_slice_name(self, slice_name: str):
        """
        Parse names of the form:  {service_type}_slice_{slice_id}
        Examples:
            video_slice_slice_reuse1      → ("video", "slice_reuse1")
            video_slice_slice_delete_safe → ("video", "slice_delete_safe")

        Splits on the FIRST occurrence of "_slice_" only to handle service
        types that contain underscores (e.g. "nr_video").
        """
        if not slice_name or "_slice_" not in slice_name:
            return "unknown", "unknown"

        idx          = slice_name.index("_slice_")
        service_type = slice_name[:idx]
        slice_id_part = slice_name[idx + len("_slice_"):]

        if not service_type or not slice_id_part:
            return "unknown", "unknown"

        return service_type, slice_id_part

    # ─────────────────────────────────────────────
    # Private: table formatter
    # ─────────────────────────────────────────────

    def _format_table(self, points: list) -> str:
        """
        Render a list of slice_sim_result dicts as a clean ASCII table.

        Example output:
        slice_name                     | success | load  | used_bw | connected
        -------------------------------+---------+-------+---------+----------
        video_slice_slice_reuse1       |    0.95 |  0.30 |    40.0 |      0.30
        video_slice_slice_fail1        |    0.40 |  0.90 |    90.0 |      0.80
        """
        if not points:
            return "(no historical records found)"

        cols = [
            ("slice_name",      "slice_name", "%-30s"),
            ("success",         "success",    "%7.2f"),
            ("load_ratio",      "load",       "%5.2f"),
            ("used_bandwidth",  "used_bw",    "%7.1f"),
            ("connected_ratio", "connected",  "%9.2f"),
        ]

        header_parts = []
        sep_parts    = []
        for _field, label, fmt in cols:
            col_w = max(len(label), int(re.search(r"\d+", fmt).group()))
            header_parts.append(label.ljust(col_w))
            sep_parts.append("-" * col_w)

        header = " | ".join(header_parts)
        sep    = "-+-".join(sep_parts)

        rows = []
        for p in points:
            cells = []
            for field, _label, fmt in cols:
                val = p.get(field, "")
                try:
                    cells.append((fmt % float(val)).strip() if val != "" else "n/a")
                except (TypeError, ValueError):
                    cells.append(str(val)[:30])
            rows.append(" | ".join(cells))

        return "\n".join([header, sep] + rows)

    # ─────────────────────────────────────────────
    # Private: DB fetch
    # ─────────────────────────────────────────────

    def _fetch_similar_slices(self, service_type: str) -> list:
        """
        Fetch all rows from slice_sim_result whose slice_name starts with
        {service_type}_slice_.  slice_name is a FIELD (not a tag) in InfluxDB,
        so a regex match is required.
        """
        service_type = self._normalize_service_type(service_type)
        pattern = f"^{re.escape(service_type)}_slice_"
        q = f"SELECT * FROM slice_sim_result WHERE slice_name =~ /{pattern}/"
        points = self._query(q)

        # Secondary filter: reject rows whose slice_name cannot be parsed
        return [
            p for p in points
            if "unknown" not in self._parse_slice_name(p.get("slice_name", ""))
        ]

    # ─────────────────────────────────────────────
    # Private: bandwidth math
    # ─────────────────────────────────────────────

    def _calc_free_bandwidth(self, used_bw: float, load_ratio: float) -> float:
        """
        Correct free-bandwidth calculation.

            load_ratio = used_bw / total_capacity
            => total_capacity = used_bw / load_ratio
            => free_bw = total_capacity - used_bw

        Example (used=40, load=0.3):
            total = 40 / 0.3 = 133.3 Mbps
            free  = 133.3 - 40 = 93.3 Mbps
        """
        if load_ratio <= 0 or load_ratio >= 1:
            return 0.0
        total_capacity = used_bw / load_ratio
        return total_capacity - used_bw

    # ─────────────────────────────────────────────
    # Private: reuse detection
    # ─────────────────────────────────────────────

    def _find_reusable_slice(self, service_type: str, requested_bw: float) -> Optional[str]:
        """
        Return the slice_id of the first existing slice that has:
          - free bandwidth >= requested_bw
          - historical success rate >= 0.8  (avoid reusing poor-quality slices)

        Returns None if no suitable slice is found.
        """
        for p in self._fetch_similar_slices(service_type):
            _, slice_id = self._parse_slice_name(p.get("slice_name", ""))
            if slice_id == "unknown":
                continue

            used_bw    = float(p.get("used_bandwidth", 0) or 0)
            load_ratio = float(p.get("load_ratio",     1) or 1)
            success    = float(p.get("success",        0) or 0)

            if success < 0.8:
                continue

            if self._calc_free_bandwidth(used_bw, load_ratio) >= requested_bw:
                return slice_id

        return None

    # ─────────────────────────────────────────────
    # PUBLIC: analyze_create
    # ─────────────────────────────────────────────

    def analyze_create(self, service_type: str, req_bandwidth: float) -> dict:
        """
        Advisory for creating (or reusing) a network slice.

        Returns a dict with keys: decision, risk, message, [target_slice_id]
        Always includes a table of historical similar slices when they exist.
        """
        service_type = self._normalize_service_type(service_type)
        reusable     = self._find_reusable_slice(service_type, req_bandwidth)
        points       = self._fetch_similar_slices(service_type)
        table        = self._format_table(points)

        # ── Reuse path ──
        if reusable:
            return {
                "decision":        "reuse",
                "risk":            "low",
                "target_slice_id": reusable,
                "message": (
                    f"Existing slice '{reusable}' has enough free capacity "
                    f"for {req_bandwidth} Mbps.\n\n"
                    f"Historical similar slices:\n{table}"
                ),
            }

        # ── No historical data at all ──
        if not points:
            return {
                "decision": "create",
                "risk":     "low",
                "message":  "No historical data found. Safe exploratory creation.",
            }

        # ── Historical data available — compute stats ──
        avg_success = mean(float(p.get("success",        0) or 0) for p in points)
        avg_load    = mean(float(p.get("load_ratio",     0) or 0) for p in points)
        avg_used    = mean(float(p.get("used_bandwidth", 0) or 0) for p in points)

        base_stats = (
            f"Avg success rate : {avg_success:.2f}\n"
            f"Avg load ratio   : {avg_load:.2f}\n"
            f"Avg used BW      : {avg_used:.1f} Mbps\n"
            f"Requested BW     : {req_bandwidth} Mbps\n\n"
            f"Historical similar slices:\n{table}"
        )

        if avg_success < 0.6:
            return {
                "decision": "create",
                "risk":     "high",
                "message": (
                    "Similar slices have a high failure rate.\n"
                    "Consider reducing bandwidth or relaxing QoS constraints.\n\n"
                    + base_stats
                ),
            }

        if avg_load > 0.85:
            return {
                "decision": "create",
                "risk":     "high",
                "message":  "Network is heavily loaded. New slice creation is risky.\n\n" + base_stats,
            }

        return {
            "decision": "create",
            "risk":     "medium",
            "message":  "Network conditions are moderate. Proceed with caution.\n\n" + base_stats,
        }

    # ─────────────────────────────────────────────
    # PUBLIC: analyze_modify
    # ─────────────────────────────────────────────

    def analyze_modify(self, service_type: str, old_value: float, new_value: float) -> dict:
        """
        Advisory for modifying any numeric parameter on a slice.

        The caller passes old_value / new_value for whichever parameter is
        being changed (bandwidth, latency, reliability, or duration).
        Network load context is fetched from similar slices so the advisory
        is meaningful regardless of which parameter changed.
        """
        service_type = self._normalize_service_type(service_type)
        points       = self._fetch_similar_slices(service_type)
        table        = self._format_table(points)

        if not points:
            return {
                "risk":    "medium",
                "message": "No historical data available. Impact of change is unknown.",
            }

        avg_load    = mean(float(p.get("load_ratio",     0) or 0) for p in points)
        avg_used    = mean(float(p.get("used_bandwidth", 0) or 0) for p in points)
        avg_success = mean(float(p.get("success",        0) or 0) for p in points)

        base_stats = (
            f"Avg success rate : {avg_success:.2f}\n"
            f"Avg load ratio   : {avg_load:.2f}\n"
            f"Avg used BW      : {avg_used:.1f} Mbps\n"
            f"Old value        : {old_value}\n"
            f"New value        : {new_value}\n\n"
            f"Historical similar slices:\n{table}"
        )

        if new_value > old_value:
            if avg_load > 0.85:
                return {
                    "risk": "high",
                    "message": (
                        "Network load is already high (avg load ratio > 0.85).\n"
                        "Increasing this parameter may degrade network performance.\n\n"
                        + base_stats
                    ),
                }
            return {
                "risk":    "medium",
                "message": "Increase is feasible under current load conditions.\n\n" + base_stats,
            }

        if new_value < old_value:
            if avg_used < old_value * 0.5:
                return {
                    "risk":    "low",
                    "message": "Slice appears underutilised. Safe to reduce.\n\n" + base_stats,
                }
            return {
                "risk":    "medium",
                "message": (
                    "Slice is actively used. Reducing this parameter may impact QoS.\n\n"
                    + base_stats
                ),
            }

        # No change
        return {
            "risk":    "low",
            "message": "Old and new values are identical. No change will be applied.\n\n" + base_stats,
        }

    # ─────────────────────────────────────────────
    # PUBLIC: analyze_delete
    # ─────────────────────────────────────────────

    def analyze_delete(self, slice_name: str) -> dict:
        """
        Advisory for deleting a slice.

        slice_name must be the full name as stored in slice_sim_result,
        e.g. "video_slice_slice_1b60ff7f".

        Queries the last 5 simulation results for this specific slice to
        check whether it is actively used or carrying significant load.
        """
        safe_name = re.escape(slice_name)
        points = self._query(
            f"SELECT connected_ratio, load_ratio, success, used_bandwidth "
            f"FROM slice_sim_result "
            f"WHERE slice_name =~ /^{safe_name}$/ "
            f"ORDER BY time DESC LIMIT 5"
        )
        table = self._format_table(points)

        if not points:
            return {
                "risk":    "low",
                "message": "No recent simulation data found for this slice. Safe to delete.",
            }

        avg_connected = mean(float(p.get("connected_ratio", 0) or 0) for p in points)
        avg_load      = mean(float(p.get("load_ratio",      0) or 0) for p in points)
        avg_success   = mean(float(p.get("success",         0) or 0) for p in points)

        base_stats = (
            f"Avg connected ratio : {avg_connected:.2f}\n"
            f"Avg load ratio      : {avg_load:.2f}\n"
            f"Avg success rate    : {avg_success:.2f}\n\n"
            f"Recent slice activity:\n{table}"
        )

        if avg_connected > 0.7:
            return {
                "risk": "high",
                "message": (
                    f"Slice is actively serving users (connected ratio: {avg_connected:.2f}).\n"
                    "Deletion will immediately impact connected devices.\n\n"
                    + base_stats
                ),
            }

        if avg_load > 0.8:
            return {
                "risk": "medium",
                "message": (
                    f"Slice is under significant load (load ratio: {avg_load:.2f}).\n"
                    "Monitor traffic before proceeding with deletion.\n\n"
                    + base_stats
                ),
            }

        return {
            "risk":    "low",
            "message": "Slice has low utilisation and few active connections. Safe to delete.\n\n" + base_stats,
        }