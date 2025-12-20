from hyponcloud2mqtt.data_merger import merge_api_data
from hyponcloud2mqtt.discovery import SENSORS


def test_merger_and_discovery_sync():
    """
    Test that all fields produced by the data merger are managed by the discovery module.
    """
    # Mock data that includes all possible fields that the merger extracts
    monitor_data = {
        "data": {
            "percent": 50,
            "meter_power": 1000,
            "power_load": 500,
            "w_cha": 200,
            "power_pv": 1500,
            "soc": 80
        }
    }
    production_data = {
        "data": {
            "today_generation": 10,
            "month_generation": 100,
            "year_generation": 1000,
            "total_generation": 5000,
            "co2": 50,
            "tree": 2,
            "diesel": 500,
            "today_revenue": 5,
            "month_revenue": 50,
            "total_revenue": 500
        }
    }
    status_data = {
        "data": {
            "gateway": {
                "online": 1,
                "offline": 0
            },
            "inverter": {
                "online": 1,
                "normal": 1,
                "offline": 0,
                "fault": 0,
                "wait": 0
            }
        }
    }

    merged = merge_api_data(monitor_data, production_data, status_data)

    # Assert
    # 1. Ensure merger produced expected fields (and only those)
    expected_fields = {
        "percent", "w_cha", "power_pv",
        "today_generation", "month_generation", "year_generation", "total_generation",
        "co2", "tree", "diesel", "today_revenue", "month_revenue", "total_revenue",
        "gateway_online", "gateway_offline",
        "inverter_online", "inverter_normal", "inverter_offline", "inverter_fault", "inverter_wait"
    }

    merged_keys = set(merged.keys())
    assert merged_keys == expected_fields, f"Merger produced unexpected or missing fields: {merged_keys ^ expected_fields}"

    # 2. Ensure all fields in merged data are in SENSORS
    for key in merged_keys:
        assert key in SENSORS, f"Field '{key}' from merger is not managed by discovery.SENSORS"

    # 3. Ensure all SENSORS keys are present in the merged data (or at least handled)
    discovery_keys = set(SENSORS.keys())
    assert discovery_keys == merged_keys, (
        f"Discovery has extra or missing sensors compared to merger: {discovery_keys ^ merged_keys}"
    )
