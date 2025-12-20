from __future__ import annotations
import logging
# from typing import Any

logger = logging.getLogger(__name__)


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

    # Extract from monitor
    if monitor and "data" in monitor:
        data = monitor["data"]
        merged["percent"] = data.get("percent")
        merged["w_cha"] = data.get("w_cha")
        merged["power_pv"] = data.get("power_pv")

    # Extract from production
    if production and "data" in production:
        data = production["data"]
        merged["today_generation"] = data.get("today_generation")
        merged["month_generation"] = data.get("month_generation")
        merged["year_generation"] = data.get("year_generation")
        merged["total_generation"] = data.get("total_generation")
        merged["co2"] = data.get("co2")
        merged["tree"] = data.get("tree")
        merged["diesel"] = data.get("diesel")
        merged["today_revenue"] = data.get("today_revenue")
        merged["month_revenue"] = data.get("month_revenue")
        merged["total_revenue"] = data.get("total_revenue")

    # Extract from status
    if status and "data" in status:
        data = status["data"]
        if "gateway" in data:
            merged["gateway_online"] = data["gateway"].get("online")
            merged["gateway_offline"] = data["gateway"].get("offline")
        if "inverter" in data:
            merged["inverter_online"] = data["inverter"].get("online")
            merged["inverter_normal"] = data["inverter"].get("normal")
            merged["inverter_offline"] = data["inverter"].get("offline")
            merged["inverter_fault"] = data["inverter"].get("fault")
            merged["inverter_wait"] = data["inverter"].get("wait")

    return merged
