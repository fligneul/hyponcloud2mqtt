"""Main application entry point."""

import time
import logging
from .config import load_config
from .hypon_cloud import HyponCloudClient
from .mqtt import connect_mqtt, publish_data


def main():
    """Main function."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    config = load_config()
    hypon_client = HyponCloudClient(config=config)
    mqtt_client = connect_mqtt(config)

    # Publish online message to LWT topic
    lwt_topic = config.get("mqtt", {}).get("topic") + "/status"
    if lwt_topic:
        mqtt_client.publish(lwt_topic, "online", retain=True)

    mqtt_client.loop_start()
    while True:
        hypon_config = config.get("hypon", {})
        system_ids = hypon_config.get("system_ids", [])
        interval = hypon_config.get("interval", 60)  # Default to 60 seconds
        retries = hypon_config.get("retries", 0)  # Default to 0 retries

        all_monitor_data = hypon_client.get_data(system_ids, retries=retries)
        if all_monitor_data:
            for system_id, data in all_monitor_data.items():
                if data:
                    logging.info("Data received for system ID %s: %s", system_id, data)
                    publish_data(mqtt_client, config, system_id, data)
        time.sleep(interval)


if __name__ == "__main__":
    main()
