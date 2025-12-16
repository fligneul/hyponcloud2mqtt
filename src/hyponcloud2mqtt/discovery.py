"""Home Assistant Discovery module."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import Config
    from .mqtt_client import MqttClient

logger = logging.getLogger(__name__)

# Sensor definitions hardcoded for Hypon inverters
SENSORS = {
    "today_earning": {"name": "Today Earning", "icon": "mdi:currency-usd"},
    "month_earning": {"name": "Month Earning", "icon": "mdi:currency-usd"},
    "total_earning": {"name": "Total Earning", "icon": "mdi:currency-usd"},
    "e_total": {
        "name": "Total Energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing"
    },
    "e_month": {
        "name": "Month Energy",
        "unit": "kWh",
        "device_class": "energy"
    },
    "e_today": {
        "name": "Today Energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing"
    },
    "e_year": {
        "name": "Year Energy",
        "unit": "kWh",
        "device_class": "energy"
    },
    "total_tree": {"name": "Trees Planted", "unit": "trees", "icon": "mdi:tree"},
    "total_co2": {"name": "CO2 Saved", "unit": "kg", "icon": "mdi:molecule-co2"},
    "total_diesel": {"name": "Diesel Saved", "unit": "L", "icon": "mdi:barrel"},
    "percent": {"name": "Capacity Percentage", "unit": "%", "icon": "mdi:percent"},
    "meter_power": {"name": "Meter Power", "unit": "W", "device_class": "power"},
    "power_load": {"name": "Power Load", "unit": "W", "device_class": "power"},
    "w_cha": {"name": "Charging Power", "unit": "W", "device_class": "power"},
    "power_pv": {"name": "PV Power", "unit": "W", "device_class": "power"},
    "soc": {"name": "State of Charge", "unit": "%", "device_class": "battery"},
    "micro": {"name": "Microinverters", "icon": "mdi:chip"},
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

        # Publish with retain=True so HA finds it on restart
        client.publish(payload, topic=discovery_topic, retain=True)
        logger.debug(f"Published discovery for {key} to {discovery_topic}")
