from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _to_int(val: Any) -> int | None:
    """Safely cast value to int, return None on failure."""
    try:
        if val is None or val == "":
            return None
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _to_float(val: Any) -> float | None:
    """Safely cast value to float, return None on failure."""
    try:
        if val is None or val == "":
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


def merge_api_data(
        monitor: dict | None,
        production: dict | None,
        status: dict | None) -> dict:
    """
    Merge data from the 3 API endpoints into a single dict.

    Args:
        monitor: Response from /monitor?refresh=true
        production: Response from /production2
        status: Response from /status

    Returns:
        Merged dict with selected fields
    """
    merged = {}

    # Helper to only add if not None
    def add_if_not_none(key: str, val: Any) -> None:
        if val is not None:
            merged[key] = val

    # Extract from monitor
    if monitor and "data" in monitor:
        data = monitor["data"]
        add_if_not_none("percent", _to_float(data.get("percent")))
        add_if_not_none("w_cha", _to_int(data.get("w_cha")))
        add_if_not_none("power_pv", _to_int(data.get("power_pv")))

    # Extract from production
    if production and "data" in production:
        data = production["data"]
        add_if_not_none("today_generation", _to_float(data.get("today_generation")))
        add_if_not_none("month_generation", _to_float(data.get("month_generation")))
        add_if_not_none("year_generation", _to_float(data.get("year_generation")))
        add_if_not_none("total_generation", _to_float(data.get("total_generation")))
        add_if_not_none("co2", _to_float(data.get("co2")))
        add_if_not_none("tree", _to_float(data.get("tree")))
        add_if_not_none("diesel", _to_float(data.get("diesel")))
        add_if_not_none("today_revenue", _to_float(data.get("today_revenue")))
        add_if_not_none("month_revenue", _to_float(data.get("month_revenue")))
        add_if_not_none("total_revenue", _to_float(data.get("total_revenue")))

    # Extract from status
    if status and "data" in status:
        data = status["data"]
        if "gateway" in data:
            gateway = data["gateway"]
            add_if_not_none("gateway_online", _to_int(gateway.get("online")))
            add_if_not_none("gateway_offline", _to_int(gateway.get("offline")))
        if "inverter" in data:
            inverter = data["inverter"]
            add_if_not_none("inverter_online", _to_int(inverter.get("online")))
            add_if_not_none("inverter_normal", _to_int(inverter.get("normal")))
            add_if_not_none("inverter_offline", _to_int(inverter.get("offline")))
            add_if_not_none("inverter_fault", _to_int(inverter.get("fault")))
            add_if_not_none("inverter_wait", _to_int(inverter.get("wait")))

    return merged
