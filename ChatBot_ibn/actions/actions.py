
# from rasa_sdk import Action, Tracker
# from rasa_sdk.events import SlotSet
# from rasa_sdk.executor import CollectingDispatcher
# from typing import Any, Dict, List, Optional
# from influxdb import InfluxDBClient
# import uuid
# import re
# import datetime


# # ─────────────────────────────────────────────
# # Helper Functions
# # ─────────────────────────────────────────────

# def extract_number(val) -> Optional[float]:
#     """Safely extract a numeric value from a slot. Returns None if not parseable."""
#     if val is None:
#         return None
#     match = re.search(r"[\d.]+", str(val))
#     return float(match.group()) if match else None


# def normalize_service_type(service_type: Optional[str]) -> str:
#     """Strip trailing digits and lowercase the service type."""
#     return re.sub(r"\d+$", "", service_type.lower()) if service_type else "unknown"


# def parse_user_intent(tracker: Tracker) -> str:
#     """
#     Reliably resolve the user's yes/no response from BOTH intent AND raw text.
#     Returns: 'yes', 'no', or 'unknown'.

#     IMPORTANT design decision:
#     - We check intent first (Rasa NLU is the authoritative signal).
#     - We fall back to keyword text matching ONLY when the intent is ambiguous
#       (i.e., not confirm_yes / confirm_no).
#     - 'reuse' is intentionally NOT in yes_words — it is a noun the user
#       might say negatively ("don't reuse") and should not bypass intent.
#     """
#     intent = tracker.latest_message.get("intent", {}).get("name", "")
#     text = tracker.latest_message.get("text", "").strip().lower()

#     if intent == "confirm_yes":
#         return "yes"
#     if intent == "confirm_no":
#         return "no"

#     # Fallback keyword matching only for truly ambiguous intents
#     yes_words = ["yes", "y", "ok", "okay", "sure", "yep", "yup", "go ahead", "proceed"]
#     no_words  = ["no", "n", "nope", "cancel", "stop", "don't", "dont", "abort"]

#     if any(text == w or text.startswith(w + " ") for w in yes_words):
#         return "yes"
#     if any(text == w or text.startswith(w + " ") for w in no_words):
#         return "no"

#     return "unknown"


# def get_db_client() -> InfluxDBClient:
#     """Create and return a connected InfluxDB client."""
#     client = InfluxDBClient(host="localhost", port=8086)
#     client.switch_database("rasa_slices")
#     return client


# def validate_id(val: Optional[str]) -> Optional[str]:
#     """
#     Reject any slice_id that contains characters outside [a-zA-Z0-9_-].
#     This prevents InfluxQL injection through slot values.
#     Returns the sanitised value, or None if invalid.
#     """
#     if not val:
#         return None
#     if re.fullmatch(r"[a-zA-Z0-9_\-]+", val):
#         return val
#     return None


# CLEAR_PENDING = [
#     SlotSet("pending_decision", None),
#     SlotSet("target_slice_id", None),
# ]


# # ═════════════════════════════════════════════════════════
# # ACTION 1: CREATE / MERGE SLICE
# # ═════════════════════════════════════════════════════════
# class ActionSubmitSlice(Action):

#     def name(self) -> str:
#         return "action_submit_slice"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict):

#         pending     = tracker.get_slot("pending_decision")
#         target_slice = tracker.get_slot("target_slice_id")

#         # ──────────────────────────────
#         # PHASE 2  (pending is already set from a previous turn)
#         # ──────────────────────────────
#         if pending:
#             user_response = parse_user_intent(tracker)

#             # User hasn't given a clear yes/no yet — keep waiting
#             if user_response == "unknown":
#                 dispatcher.utter_message(
#                     text="Please reply with yes or no."
#                 )
#                 return []

#             # User said NO to whatever was proposed
#             if user_response == "no":
#                 dispatcher.utter_message(text="Operation cancelled.")
#                 return CLEAR_PENDING

#             # User said YES
#             # pending == "reuse" → confirm reuse of existing slice
#             if pending == "reuse":
#                 dispatcher.utter_message(
#                     text=f"You can now re-use this slice. Slice ID: {target_slice}"
#                 )
#                 return CLEAR_PENDING

#             # pending == "create" → actually write the new slice
#             if pending == "create":
#                 # Re-extract and validate slots (they must still be set)
#                 bandwidth_raw  = extract_number(tracker.get_slot("bandwidth"))
#                 latency_raw    = extract_number(tracker.get_slot("latency"))
#                 reliability_raw = extract_number(tracker.get_slot("reliability"))
#                 duration_raw   = extract_number(tracker.get_slot("duration"))
#                 service_type   = normalize_service_type(tracker.get_slot("service_type"))

#                 if any(v is None for v in [bandwidth_raw, latency_raw, reliability_raw, duration_raw]):
#                     dispatcher.utter_message(
#                         text="Some required slot values are missing. Please start over."
#                     )
#                     return CLEAR_PENDING

#                 bandwidth   = int(bandwidth_raw)
#                 latency     = int(latency_raw)
#                 reliability = reliability_raw
#                 duration    = int(duration_raw)

#                 slice_id = f"slice_{uuid.uuid4().hex[:8]}"
#                 client = get_db_client()
#                 try:
#                     client.write_points([{
#                         "measurement": "network_slice",
#                         "tags": {
#                             "slice_id": slice_id,
#                             "service_type": service_type,
#                         },
#                         "fields": {
#                             "bandwidth":   bandwidth,
#                             "latency":     latency,
#                             "reliability": reliability,
#                             "duration":    duration,
#                         },
#                     }])
#                 finally:
#                     client.close()

#                 dispatcher.utter_message(text=f"New slice created: {slice_id}")
#                 return CLEAR_PENDING

#             # Defensive: unexpected pending value — clear state
#             dispatcher.utter_message(text="Unexpected state. Operation cancelled.")
#             return CLEAR_PENDING

#         # ──────────────────────────────
#         # PHASE 1  (first call — no pending decision yet)
#         # ──────────────────────────────

#         # Validate all required slots before doing anything
#         bandwidth_raw   = extract_number(tracker.get_slot("bandwidth"))
#         latency_raw     = extract_number(tracker.get_slot("latency"))
#         reliability_raw = extract_number(tracker.get_slot("reliability"))
#         duration_raw    = extract_number(tracker.get_slot("duration"))
#         service_type    = normalize_service_type(tracker.get_slot("service_type"))

#         missing = []
#         if bandwidth_raw   is None: missing.append("bandwidth")
#         if latency_raw     is None: missing.append("latency")
#         if reliability_raw is None: missing.append("reliability")
#         if duration_raw    is None: missing.append("duration")

#         if missing:
#             dispatcher.utter_message(
#                 text=f"Missing or invalid values for: {', '.join(missing)}. Please provide them."
#             )
#             return []

#         bandwidth = int(bandwidth_raw)

#         # Import here to avoid circular imports in tests
#         from .decision_engine import DecisionEngine
#         engine = DecisionEngine()
#         advice = engine.analyze_create(service_type, bandwidth)

#         dispatcher.utter_message(
#             text=f"Advisory ({advice['risk']} risk):\n{advice['message']}"
#         )

#         if advice["decision"] == "reuse":
#             dispatcher.utter_message(
#                 text="An existing slice matches your requirements. Do you want to reuse it? (yes / no)"
#             )
#             return [
#                 SlotSet("pending_decision", "reuse"),
#                 SlotSet("target_slice_id", advice["target_slice_id"]),
#             ]
#         else:
#             dispatcher.utter_message(
#                 text="Do you want to create a new slice? (yes / no)"
#             )
#             return [SlotSet("pending_decision", "create")]


# # ═════════════════════════════════════════════════════════
# # ACTION 2: DELETE SLICE
# # ═════════════════════════════════════════════════════════
# class ActionDeleteSpecificSlice(Action):

#     def name(self) -> str:
#         return "action_delete_specific_slice"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict):

#         pending  = tracker.get_slot("pending_decision")
#         slice_id = validate_id(tracker.get_slot("slice_id"))

#         if not slice_id:
#             dispatcher.utter_message(
#                 text="Please provide a valid slice ID (letters, numbers, hyphens and underscores only)."
#             )
#             return []

#         # ──────────────────────────────
#         # PHASE 2
#         # ──────────────────────────────
#         if pending == "delete":
#             user_response = parse_user_intent(tracker)

#             if user_response == "unknown":
#                 dispatcher.utter_message(text="Please reply with yes or no.")
#                 return []

#             if user_response == "no":
#                 dispatcher.utter_message(text="Deletion cancelled.")
#                 return CLEAR_PENDING

#             # user_response == "yes" → execute the delete
#             client = get_db_client()
#             try:
#                 # InfluxDB does not support parameterised queries, so we use
#                 # the validated slice_id (already confirmed safe by validate_id).
#                 delete_query = f"DELETE FROM network_slice WHERE slice_id='{slice_id}'"
#                 client.query(delete_query)
#             finally:
#                 client.close()

#             dispatcher.utter_message(text=f"Slice {slice_id} deleted successfully.")
#             return CLEAR_PENDING

#         # ──────────────────────────────
#         # PHASE 1
#         # ──────────────────────────────

#         # Fetch the slice first so we can run advisory analysis
#         client = get_db_client()
#         try:
#             query = f"SELECT * FROM network_slice WHERE slice_id='{slice_id}' ORDER BY time DESC LIMIT 1"
#             result = client.query(query)
#             points = list(result.get_points())
#         finally:
#             client.close()

#         if not points:
#             dispatcher.utter_message(text=f"Slice {slice_id} not found.")
#             return []

#         service_type = normalize_service_type(points[0].get("service_type"))
#         slice_name   = f"{service_type}_slice_{slice_id}"

#         from .decision_engine import DecisionEngine
#         engine = DecisionEngine()
#         advice = engine.analyze_delete(slice_name)

#         dispatcher.utter_message(
#             text=f"Advisory ({advice['risk']} risk):\n{advice['message']}"
#         )

#         # High-risk: block deletion entirely — no confirmation offered
#         if advice["risk"] == "high":
#             dispatcher.utter_message(
#                 text="Deletion blocked due to high risk. No changes were made."
#             )
#             return []

#         # Low / medium risk: ask for confirmation
#         dispatcher.utter_message(
#             text=f"Are you sure you want to delete slice {slice_id}? This cannot be undone. (yes / no)"
#         )
#         return [SlotSet("pending_decision", "delete")]


# # ═════════════════════════════════════════════════════════
# # ACTION 3: MODIFY SLICE
# # ═════════════════════════════════════════════════════════
# class ActionModifySpecificSlice(Action):

#     def name(self) -> str:
#         return "action_modify_specific_slice"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict):

#         pending   = tracker.get_slot("pending_decision")
#         slice_id  = validate_id(tracker.get_slot("slice_id"))
#         parameter = tracker.get_slot("parameter_to_modify")
#         new_value = extract_number(tracker.get_slot("new_value"))

#         # Validate slice_id
#         if not slice_id:
#             dispatcher.utter_message(
#                 text="Please provide a valid slice ID (letters, numbers, hyphens and underscores only)."
#             )
#             return []

#         # Validate parameter
#         allowed_parameters = {"bandwidth", "latency", "reliability", "duration"}
#         if not parameter or parameter.lower() not in allowed_parameters:
#             dispatcher.utter_message(
#                 text=f"Invalid parameter. Allowed values: {', '.join(sorted(allowed_parameters))}."
#             )
#             return []
#         parameter = parameter.lower()

#         # Validate new value
#         if new_value is None:
#             dispatcher.utter_message(text="Please provide a valid numeric value for the modification.")
#             return []

#         # ──────────────────────────────
#         # PHASE 2
#         # ──────────────────────────────
#         if pending == "modify":
#             user_response = parse_user_intent(tracker)

#             if user_response == "unknown":
#                 dispatcher.utter_message(text="Please reply with yes or no.")
#                 return []

#             if user_response == "no":
#                 dispatcher.utter_message(text="Modification cancelled.")
#                 return [SlotSet("pending_decision", None)]

#             # user_response == "yes" → fetch current record and write update
#             client = get_db_client()
#             try:
#                 query = (
#                     f"SELECT * FROM network_slice "
#                     f"WHERE slice_id='{slice_id}' ORDER BY time DESC LIMIT 1"
#                 )
#                 result = client.query(query)
#                 points = list(result.get_points())

#                 if not points:
#                     dispatcher.utter_message(text=f"Slice {slice_id} not found.")
#                     return [SlotSet("pending_decision", None)]

#                 current      = points[0]
#                 service_type = normalize_service_type(current.get("service_type"))

#                 # Build the updated fields — only the chosen parameter changes
#                 updated_fields = {
#                     "bandwidth":   int(new_value) if parameter == "bandwidth"   else int(current["bandwidth"]),
#                     "latency":     int(new_value) if parameter == "latency"     else int(current["latency"]),
#                     "reliability": new_value       if parameter == "reliability" else current["reliability"],
#                     "duration":    int(new_value) if parameter == "duration"    else int(current["duration"]),
#                 }

#                 client.write_points([{
#                     "measurement": "network_slice",
#                     "tags": {
#                         "slice_id":     slice_id,
#                         "service_type": service_type,
#                     },
#                     "time":   datetime.datetime.utcnow().isoformat(),
#                     "fields": updated_fields,
#                 }])
#             finally:
#                 client.close()

#             dispatcher.utter_message(text=f"Slice {slice_id} updated successfully.")
#             return [SlotSet("pending_decision", None)]

#         # ──────────────────────────────
#         # PHASE 1
#         # ──────────────────────────────

#         # Fetch the current slice to provide meaningful advisory context
#         client = get_db_client()
#         try:
#             query = (
#                 f"SELECT * FROM network_slice "
#                 f"WHERE slice_id='{slice_id}' ORDER BY time DESC LIMIT 1"
#             )
#             result = client.query(query)
#             points = list(result.get_points())
#         finally:
#             client.close()

#         if not points:
#             dispatcher.utter_message(text=f"Slice {slice_id} not found.")
#             return []

#         current      = points[0]
#         old_value    = current.get(parameter)
#         service_type = normalize_service_type(current.get("service_type"))

#         from .decision_engine import DecisionEngine
#         engine = DecisionEngine()

#         # Run advisory analysis for ALL parameters, not just bandwidth.
#         # Each parameter type calls the most appropriate analysis method.
#         if parameter == "bandwidth":
#             advice = engine.analyze_modify(service_type, old_value, new_value)
#             dispatcher.utter_message(
#                 text=f"Advisory ({advice['risk']} risk):\n{advice['message']}"
#             )
#         elif parameter == "latency":
#             # analyze_modify can be extended to cover latency; for now we surface
#             # a generic advisory so the user is always informed before confirming.
#             advice = engine.analyze_modify(service_type, old_value, new_value)
#             dispatcher.utter_message(
#                 text=f"Advisory ({advice['risk']} risk):\n{advice['message']}"
#             )
#         else:
#             # reliability / duration — inform the user of the change
#             dispatcher.utter_message(
#                 text=f"This will change {parameter} from {old_value} to {new_value}."
#             )

#         dispatcher.utter_message(
#             text="Do you want to proceed with this modification? (yes / no)"
#         )
#         return [SlotSet("pending_decision", "modify")]


from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from typing import Dict, List, Optional
from influxdb import InfluxDBClient
import uuid
import re
import datetime


# ─────────────────────────────────────────────────────────
# Slot reset helper
# ─────────────────────────────────────────────────────────
# Returns a fresh list every call (SlotSet objects are not reusable
# across requests — always generate a new list).

def all_flow_slots() -> List:
    """Wipe every slot that belongs to a slice workflow."""
    return [
        SlotSet("pending_decision",    None),
        SlotSet("target_slice_id",     None),
        SlotSet("bandwidth",           None),
        SlotSet("latency",             None),
        SlotSet("reliability",         None),
        SlotSet("duration",            None),
        SlotSet("service_type",        None),
        SlotSet("slice_id",            None),
        SlotSet("parameter_to_modify", None),
        SlotSet("new_value",           None),
    ]


# ─────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────

def extract_number(val) -> Optional[float]:
    """Safely extract a numeric value from a slot string."""
    if val is None:
        return None
    match = re.search(r"[\d.]+", str(val))
    return float(match.group()) if match else None


def normalize_service_type(service_type: Optional[str]) -> str:
    """Strip trailing digits and lowercase the service type."""
    return re.sub(r"\d+$", "", service_type.strip().lower()) if service_type else "unknown"


def validate_id(val: Optional[str]) -> Optional[str]:
    """
    Only allow slice IDs that consist of [a-zA-Z0-9_-].
    Returns the value unchanged if safe, or None to signal rejection.
    This prevents InfluxQL injection through slot values.
    """
    if not val:
        return None
    return val if re.fullmatch(r"[a-zA-Z0-9_\-]+", val) else None


def parse_user_intent(tracker: Tracker) -> str:
    """
    Resolve the user's yes/no answer from intent AND raw text.
    Returns: 'yes', 'no', or 'unknown'.

    Intent is checked first (authoritative).
    Keyword fallback only fires for ambiguous intents so that a user
    typing "sure" or "nope" still works even when NLU misfires.
    """
    intent = tracker.latest_message.get("intent", {}).get("name", "")
    text   = tracker.latest_message.get("text", "").strip().lower()

    if intent == "confirm_yes":
        return "yes"
    if intent == "confirm_no":
        return "no"

    yes_words = ["yes", "y", "ok", "okay", "sure", "yep", "yup",
                 "go ahead", "proceed", "confirm", "do it", "affirmative"]
    no_words  = ["no", "n", "nope", "cancel", "stop", "don't", "dont",
                 "abort", "reject", "nevermind", "never mind", "skip it"]

    if any(text == w or text.startswith(w + " ") for w in yes_words):
        return "yes"
    if any(text == w or text.startswith(w + " ") for w in no_words):
        return "no"

    return "unknown"


def get_db_client() -> InfluxDBClient:
    client = InfluxDBClient(host="localhost", port=8086)
    client.switch_database("rasa_slices")
    return client


# ═════════════════════════════════════════════════════════
# ACTION 1: CREATE / REUSE SLICE  — Phase 1 only
#
# Triggered by: "Submit slice request form" rule
# Runs advisory analysis and asks the user yes/no.
# Phase 2 (actual yes/no handling) is done by
# ActionHandleConfirmation below.
# ═════════════════════════════════════════════════════════
class ActionSubmitSlice(Action):

    def name(self) -> str:
        return "action_submit_slice"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict):

        bandwidth_raw   = extract_number(tracker.get_slot("bandwidth"))
        latency_raw     = extract_number(tracker.get_slot("latency"))
        reliability_raw = extract_number(tracker.get_slot("reliability"))
        duration_raw    = extract_number(tracker.get_slot("duration"))
        service_type    = normalize_service_type(tracker.get_slot("service_type"))

        missing = []
        if bandwidth_raw   is None: missing.append("bandwidth")
        if latency_raw     is None: missing.append("latency")
        if reliability_raw is None: missing.append("reliability")
        if duration_raw    is None: missing.append("duration")

        if missing:
            dispatcher.utter_message(
                text=f"Missing or invalid values for: {', '.join(missing)}. Please provide them."
            )
            return all_flow_slots()

        from .decision_engine import DecisionEngine
        engine = DecisionEngine()
        advice = engine.analyze_create(service_type, int(bandwidth_raw))

        dispatcher.utter_message(
            text=f"Advisory ({advice['risk']} risk):\n{advice['message']}"
        )

        if advice["decision"] == "reuse":
            dispatcher.utter_message(
                text="An existing slice matches your requirements. Do you want to reuse it? (yes / no)"
            )
            return [
                SlotSet("pending_decision", "reuse"),
                SlotSet("target_slice_id",  advice["target_slice_id"]),
            ]

        # decision == "create"
        dispatcher.utter_message(
            text="Do you want to create a new slice? (yes / no)"
        )
        return [SlotSet("pending_decision", "create")]


# ═════════════════════════════════════════════════════════
# ACTION 2: DELETE SLICE  — Phase 1 only
#
# Triggered by: "Handle slice deletion" rule
# Runs advisory and asks yes/no.
# Phase 2 is handled by ActionHandleConfirmation.
# ═════════════════════════════════════════════════════════
class ActionDeleteSpecificSlice(Action):

    def name(self) -> str:
        return "action_delete_specific_slice"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict):

        slice_id = validate_id(tracker.get_slot("slice_id"))

        if not slice_id:
            dispatcher.utter_message(
                text="Please provide a valid slice ID (letters, numbers, hyphens and underscores only)."
            )
            return all_flow_slots()

        client = get_db_client()
        try:
            result = client.query(
                f"SELECT * FROM network_slice WHERE slice_id='{slice_id}' ORDER BY time DESC LIMIT 1"
            )
            points = list(result.get_points())
        finally:
            client.close()

        if not points:
            dispatcher.utter_message(text=f"Slice {slice_id} not found.")
            return all_flow_slots()

        service_type = normalize_service_type(points[0].get("service_type"))
        slice_name   = f"{service_type}_slice_{slice_id}"

        from .decision_engine import DecisionEngine
        engine = DecisionEngine()
        advice = engine.analyze_delete(slice_name)

        dispatcher.utter_message(
            text=f"Advisory ({advice['risk']} risk):\n{advice['message']}"
        )

        # High risk: block outright — no confirmation prompt, no pending state set
        if advice["risk"] == "high":
            dispatcher.utter_message(
                text="Deletion blocked due to high risk. No changes were made."
            )
            return all_flow_slots()

        dispatcher.utter_message(
            text=f"Are you sure you want to delete slice {slice_id}? This cannot be undone. (yes / no)"
        )
        return [SlotSet("pending_decision", "delete")]


# ═════════════════════════════════════════════════════════
# ACTION 3: MODIFY SLICE  — Phase 1 only
#
# Triggered by: "Handle slice modification" rule
# Runs advisory and asks yes/no.
# Phase 2 is handled by ActionHandleConfirmation.
# ═════════════════════════════════════════════════════════
class ActionModifySpecificSlice(Action):

    def name(self) -> str:
        return "action_modify_specific_slice"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict):

        slice_id  = validate_id(tracker.get_slot("slice_id"))
        parameter = tracker.get_slot("parameter_to_modify")
        new_value = extract_number(tracker.get_slot("new_value"))

        if not slice_id:
            dispatcher.utter_message(
                text="Please provide a valid slice ID (letters, numbers, hyphens and underscores only)."
            )
            return all_flow_slots()

        allowed_parameters = {"bandwidth", "latency", "reliability", "duration"}
        if not parameter or parameter.strip().lower() not in allowed_parameters:
            dispatcher.utter_message(
                text=f"Invalid parameter. Allowed values: {', '.join(sorted(allowed_parameters))}."
            )
            return all_flow_slots()
        parameter = parameter.strip().lower()

        if new_value is None:
            dispatcher.utter_message(text="Please provide a valid numeric value for the modification.")
            return all_flow_slots()

        client = get_db_client()
        try:
            result = client.query(
                f"SELECT * FROM network_slice "
                f"WHERE slice_id='{slice_id}' ORDER BY time DESC LIMIT 1"
            )
            points = list(result.get_points())
        finally:
            client.close()

        if not points:
            dispatcher.utter_message(text=f"Slice {slice_id} not found.")
            return all_flow_slots()

        current      = points[0]
        old_value    = current.get(parameter)
        service_type = normalize_service_type(current.get("service_type"))

        from .decision_engine import DecisionEngine
        engine = DecisionEngine()

        if parameter in ("bandwidth", "latency"):
            advice = engine.analyze_modify(service_type, float(old_value or 0), new_value)
            dispatcher.utter_message(
                text=f"Advisory ({advice['risk']} risk):\n{advice['message']}"
            )
        else:
            # reliability / duration — just inform the user of the change
            dispatcher.utter_message(
                text=f"This will change {parameter} from {old_value} to {new_value}."
            )

        dispatcher.utter_message(
            text="Do you want to proceed with this modification? (yes / no)"
        )
        return [SlotSet("pending_decision", "modify")]


# ═════════════════════════════════════════════════════════
# ACTION 4: CONFIRMATION DISPATCHER  — Phase 2 for ALL flows
#
# WHY THIS EXISTS:
# Rasa's RulePolicy raises InvalidRule if two rules share the same
# intent → different action, even with slot-value conditions.
# The workaround: a single action for confirm_yes and confirm_no
# that reads pending_decision at runtime and delegates internally.
#
# Rules:
#   "User confirms pending action"  (confirm_yes) → this action
#   "User rejects pending action"   (confirm_no)  → this action
# ═════════════════════════════════════════════════════════
class ActionHandleConfirmation(Action):

    def name(self) -> str:
        return "action_handle_confirmation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict):

        pending       = tracker.get_slot("pending_decision")
        user_response = parse_user_intent(tracker)

        # Safety: no pending state — ignore stray yes/no messages
        if not pending:
            return []

        # User hasn't given a clear yes/no yet — keep waiting
        if user_response == "unknown":
            dispatcher.utter_message(text="Please reply with yes or no.")
            return []

        # ── USER SAID NO — cancel everything, wipe all slots ──
        if user_response == "no":
            dispatcher.utter_message(text="Operation cancelled.")
            return all_flow_slots()

        # ── USER SAID YES — delegate to the right handler ──
        if pending == "reuse":
            return self._handle_reuse(dispatcher, tracker)

        if pending == "create":
            return self._handle_create(dispatcher, tracker)

        if pending == "modify":
            return self._handle_modify(dispatcher, tracker)

        if pending == "delete":
            return self._handle_delete(dispatcher, tracker)

        # Defensive fallback
        dispatcher.utter_message(text="Unexpected state. Operation cancelled.")
        return all_flow_slots()

    # ── yes to REUSE ──────────────────────────────────────
    def _handle_reuse(self, dispatcher, tracker):
        target_slice = tracker.get_slot("target_slice_id")
        dispatcher.utter_message(
            text=f"You can now re-use this slice. Slice ID: {target_slice}"
        )
        return all_flow_slots()

    # ── yes to CREATE ─────────────────────────────────────
    def _handle_create(self, dispatcher, tracker):
        bandwidth_raw   = extract_number(tracker.get_slot("bandwidth"))
        latency_raw     = extract_number(tracker.get_slot("latency"))
        reliability_raw = extract_number(tracker.get_slot("reliability"))
        duration_raw    = extract_number(tracker.get_slot("duration"))
        service_type    = normalize_service_type(tracker.get_slot("service_type"))

        if any(v is None for v in [bandwidth_raw, latency_raw, reliability_raw, duration_raw]):
            dispatcher.utter_message(
                text="Some required slot values are missing. Please start over."
            )
            return all_flow_slots()

        slice_id = f"slice_{uuid.uuid4().hex[:8]}"
        client = get_db_client()
        try:
            client.write_points([{
                "measurement": "network_slice",
                "tags": {
                    "slice_id":     slice_id,
                    "service_type": service_type,
                },
                "fields": {
                    "bandwidth":   int(bandwidth_raw),
                    "latency":     int(latency_raw),
                    "reliability": reliability_raw,
                    "duration":    int(duration_raw),
                },
            }])
        finally:
            client.close()

        dispatcher.utter_message(text=f"New slice created successfully. Slice ID: {slice_id}")
        return all_flow_slots()

    # ── yes to MODIFY ─────────────────────────────────────
    def _handle_modify(self, dispatcher, tracker):
        slice_id  = validate_id(tracker.get_slot("slice_id"))
        parameter = tracker.get_slot("parameter_to_modify")
        new_value = extract_number(tracker.get_slot("new_value"))

        if not slice_id or not parameter or new_value is None:
            dispatcher.utter_message(text="Required information is missing. Please start over.")
            return all_flow_slots()

        parameter = parameter.strip().lower()

        client = get_db_client()
        try:
            result = client.query(
                f"SELECT * FROM network_slice "
                f"WHERE slice_id='{slice_id}' ORDER BY time DESC LIMIT 1"
            )
            points = list(result.get_points())

            if not points:
                dispatcher.utter_message(text=f"Slice {slice_id} not found.")
                return all_flow_slots()

            current      = points[0]
            service_type = normalize_service_type(current.get("service_type"))

            updated_fields = {
                "bandwidth":   int(new_value) if parameter == "bandwidth"   else int(current.get("bandwidth",   0)),
                "latency":     int(new_value) if parameter == "latency"     else int(current.get("latency",     0)),
                "reliability": new_value       if parameter == "reliability" else current.get("reliability", 0),
                "duration":    int(new_value) if parameter == "duration"    else int(current.get("duration",    0)),
            }

            client.write_points([{
                "measurement": "network_slice",
                "tags": {
                    "slice_id":     slice_id,
                    "service_type": service_type,
                },
                "time":   datetime.datetime.utcnow().isoformat(),
                "fields": updated_fields,
            }])
        finally:
            client.close()

        dispatcher.utter_message(
            text=f"Slice {slice_id} updated: {parameter} set to {new_value}."
        )
        return all_flow_slots()

    # ── yes to DELETE ─────────────────────────────────────
    def _handle_delete(self, dispatcher, tracker):
        slice_id = validate_id(tracker.get_slot("slice_id"))

        if not slice_id:
            dispatcher.utter_message(text="Slice ID is missing or invalid. Operation cancelled.")
            return all_flow_slots()

        client = get_db_client()
        try:
            client.query(f"DELETE FROM network_slice WHERE slice_id='{slice_id}'")
        finally:
            client.close()

        dispatcher.utter_message(text=f"Slice {slice_id} deleted successfully.")
        return all_flow_slots()