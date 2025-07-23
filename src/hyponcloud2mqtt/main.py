"""Main application entry point."""
import time
import logging
from .config import load_config
from .hypon_cloud import HyponCloudClient
from .mqtt import connect_mqtt, publish_data

def main():
    """Main function."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    config = load_config()
    hypon_client = HyponCloudClient()
    mqtt_client = connect_mqtt(config)
    mqtt_client.loop_start()
    while True:
        hypon_config = config.get("hypon", {})
        system_ids = hypon_config.get("system_ids", [])
        interval = hypon_config.get("interval", 60) # Default to 60 seconds

        all_monitor_data = hypon_client.get_data(config, system_ids)
        if all_monitor_data:
            for system_id, data in all_monitor_data.items():
                if data:
                    logging.info("Data received for system ID %s: %s", system_id, data)
                    publish_data(mqtt_client, config, system_id, data)
        time.sleep(interval)

if __name__ == "__main__":
    main()
