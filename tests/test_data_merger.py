from __future__ import annotations
from hyponcloud2mqtt.data_merger import merge_api_data


def test_merge_api_data():
    monitor = {
        "code": 20000,
        "data": {
            "percent": 5.39,
            "meter_power": 0,
            "power_load": 41,
            "w_cha": 0,
            "power_pv": 41
        }
    }

    production = {
        "code": 20000,
        "data": {
            "today_generation": 0.02,
            "month_generation": 0.09,
            "year_generation": 94.42,
            "total_generation": 94.42,
            "co2": 2.83,
            "tree": 0.16,
            "diesel": 10.49,
            "today_revenue": 0,
            "month_revenue": 0.02,
            "total_revenue": 16.16
        }
    }

    status = {
        "code": 20000,
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

    merged = merge_api_data(monitor, production, status)

    assert merged["percent"] == 5.39
    assert merged["power_pv"] == 41
    assert merged["today_generation"] == 0.02
    assert merged["co2"] == 2.83
    assert merged["gateway_online"] == 1
    assert merged["inverter_normal"] == 1


def test_merge_api_data_with_none():
    # Test with some endpoints returning None
    merged = merge_api_data(None, None, None)
    assert merged == {}


def test_repro_strings_in_output():
    status_data = {
        "data": {
            "gateway": {
                "online": 1,
                "offline": "0",
            },
            "inverter": {
                "online": 1,
                "normal": "1",
                "offline": 0,
                "fault": "",      # Should be removed
                "wait": None      # Should be removed
            }
        }
    }
    merged = merge_api_data(None, None, status_data)

    # Assert they are integers
    assert isinstance(merged["gateway_online"], int)
    assert merged["gateway_online"] == 1
    assert isinstance(merged["inverter_normal"], int)
    assert merged["inverter_normal"] == 1

    # Assert invalid/None values are removed
    assert "inverter_fault" not in merged
    assert "inverter_wait" not in merged
