"""Home Assistant Discovery module."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import Config
    from .mqtt_client import MqttClient

logger = logging.getLogger(__name__)

SENSORS = {
    "today_revenue": {"name": "Today Revenue", "icon": "mdi:currency-usd", "state_class": "total_increasing", "display_precision": 2},
    "month_revenue": {"name": "Month Revenue", "icon": "mdi:currency-usd", "state_class": "total_increasing", "display_precision": 2},
    "total_revenue": {"name": "Total Revenue", "icon": "mdi:currency-usd", "state_class": "total_increasing", "display_precision": 2},
    "total_generation": {
        "name": "Total Energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "display_precision": 2
    },
    "month_generation": {
        "name": "Month Energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "display_precision": 2
    },
    "today_generation": {
        "name": "Today Energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "display_precision": 2
    },
    "year_generation": {
        "name": "Year Energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "display_precision": 2
    },
    "tree": {"name": "Trees Planted", "icon": "mdi:tree", "state_class": "total_increasing", "display_precision": 2},
    "co2": {"name": "CO2 Saved", "unit": "kg", "icon": "mdi:molecule-co2", "state_class": "total_increasing", "display_precision": 2},
    "diesel": {"name": "Diesel Saved", "unit": "L", "icon": "mdi:barrel", "state_class": "total_increasing", "display_precision": 2},
    "percent": {"name": "Capacity Factor", "unit": "%", "icon": "mdi:percent", "state_class": "measurement", "display_precision": 2},
    "w_cha": {"name": "Charging Power", "unit": "W", "device_class": "power", "state_class": "measurement", "display_precision": 0},
    "power_pv": {"name": "PV Power", "unit": "W", "device_class": "power", "state_class": "measurement", "display_precision": 0},
    "gateway_online": {"name": "Gateway Online", "icon": "mdi:cloud-check", "entity_category": "diagnostic"},
    "gateway_offline": {"name": "Gateway Offline", "icon": "mdi:cloud-off-outline", "entity_category": "diagnostic"},
    "inverter_online": {"name": "Inverter Online", "icon": "mdi:solar-power-variant", "entity_category": "diagnostic"},
    "inverter_normal": {"name": "Inverter Normal", "icon": "mdi:check-circle-outline", "entity_category": "diagnostic"},
    "inverter_offline": {
        "name": "Inverter Offline",
        "icon": "mdi:solar-power-variant-outline",
        "entity_category": "diagnostic"
    },
    "inverter_fault": {"name": "Inverter Fault", "icon": "mdi:alert-circle-outline", "entity_category": "diagnostic"},
    "inverter_wait": {"name": "Inverter Wait", "icon": "mdi:clock-outline", "entity_category": "diagnostic"},
}


def publish_discovery_message(
    client: MqttClient,
    config: Config,
    system_id: str
) -> None:
    """Publishes Home Assistant discovery messages for a given system ID."""
    if not config.ha_discovery_enabled:
        return

    discovery_prefix = config.ha_discovery_prefix
    base_topic = config.mqtt_topic
    # Data topic where values will be published: <base_topic>/<system_id>
    # Note: main.py currently publishes to f"{config.mqtt_topic}/{system_id}"
    state_topic = f"{base_topic}/{system_id}"
    availability_topic = config.mqtt_availability_topic

    device_info = {
        "identifiers": [f"hypon_{system_id}"],
        "name": f"{config.device_name} {system_id}",
        "manufacturer": "Hypon",
        "model": "Hypon Inverter",
    }

    for key, attributes in SENSORS.items():
        sensor_name = attributes["name"]
        # Unique ID for the sensor entity in HA
        unique_id = f"hypon_{system_id}_{key}"
        # Discovery topic: <prefix>/sensor/<node_id>/<object_id>/config
        # We use system_id as node_id component
        discovery_topic = f"{discovery_prefix}/sensor/hypon_{system_id}/{unique_id}/config"

        payload: dict[str, Any] = {
            "name": f"{sensor_name}",
            "unique_id": unique_id,
            "state_topic": state_topic,
            "value_template": f"{{{{ value_json.{key} }}}}",
            "device": device_info,
            "availability_topic": availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",
        }

        if "unit" in attributes:
            payload["unit_of_measurement"] = attributes["unit"]
        if "device_class" in attributes:
            payload["device_class"] = attributes["device_class"]
        if "state_class" in attributes:
            payload["state_class"] = attributes["state_class"]
        if "icon" in attributes:
            payload["icon"] = attributes["icon"]
        if "entity_category" in attributes:
            payload["entity_category"] = attributes["entity_category"]
        if "display_precision" in attributes:
            payload["suggested_display_precision"] = attributes["display_precision"]

        # Publish with retain=True so HA finds it on restart
        client.publish(payload, topic=discovery_topic, retain=True)
        logger.debug(f"Published discovery for {key} to {discovery_topic}")
