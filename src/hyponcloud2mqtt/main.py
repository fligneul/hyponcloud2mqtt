
from __future__ import annotations
import os
import time
import logging
import signal
import sys
import threading
from .config import Config
from .mqtt_client import MqttClient
from .health_server import HealthServer, HealthContext, HealthHTTPHandler
from .data_fetcher import DataFetcher
from .discovery import publish_discovery_message

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Daemon:
    def __init__(self, config: Config | None = None):
        self.running = True
        self.config = config
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, stopping...")
        self.running = False

    def run(self):  # noqa: C901
        if self.config:
            config = self.config
        else:
            config_path = os.getenv("CONFIG_FILE", "config.yaml")
            try:
                config = Config.load(config_path)
            except Exception as e:
                logger.critical(f"Configuration error: {e}")
                sys.exit(1)

        mqtt_client = MqttClient(
            config.mqtt_broker,
            config.mqtt_port,
            config.mqtt_topic,
            config.mqtt_availability_topic,
            config.mqtt_username,
            config.mqtt_password,
            config.dry_run,
            config.mqtt_tls_enabled,
            config.mqtt_tls_insecure,
            config.mqtt_ca_path,
            config.mqtt_client_id
        )

        # Start Health Server
        if config.health_server_enabled:
            health_context = HealthContext(mqtt_client)
            health_server = HealthServer(
                ('0.0.0.0', 8080), HealthHTTPHandler, health_context)
            health_thread = threading.Thread(
                target=health_server.serve_forever, daemon=True)
            health_thread.start()
            logger.info("Health check server started on port 8080")

        # Connect to MQTT (with retry logic if not in dry run mode)
        if not config.dry_run:
            # Retry connection with exponential backoff
            retry_delay = 5
            max_retry_delay = 60

            while self.running:
                if mqtt_client.connect(timeout=10):
                    logger.info("Successfully connected to MQTT broker")
                    break
                else:
                    logger.warning(
                        f"MQTT connection failed, retrying in {retry_delay} seconds...")
                    # Sleep in short intervals to respond to signals
                    for _ in range(retry_delay):
                        if not self.running:
                            logger.info(
                                "Stopping before MQTT connection established")
                            sys.exit(0)
                        time.sleep(1)

                    # Exponential backoff
                    retry_delay = min(retry_delay * 2, max_retry_delay)

            if not self.running:
                sys.exit(0)
        else:
            logger.info("[DRY RUN] Skipping MQTT connection")

        # Publish HA Discovery (only if MQTT is connected)
        if config.ha_discovery_enabled:
            if mqtt_client.connected:
                logger.info("Publishing Home Assistant discovery messages...")
                for system_id in config.system_ids:
                    publish_discovery_message(mqtt_client, config, system_id)
            else:
                logger.warning(
                    "Skipping Home Assistant discovery: MQTT not connected")

        # Initialize Data Fetchers for each system ID
        data_fetchers = [DataFetcher(config, system_id)
                         for system_id in config.system_ids]
        logger.info(
            f"Initialized {len(data_fetchers)} data fetchers for system IDs: {config.system_ids}")

        logger.info(
            f"Starting daemon, fetching every {config.http_interval} seconds")

        while self.running:
            # Check MQTT connection before fetching (unless in dry run mode)
            if not config.dry_run and not mqtt_client.connected:
                logger.warning(
                    "MQTT disconnected, attempting to reconnect...")
                retry_delay = 5
                max_retry_delay = 60

                while self.running and not mqtt_client.connected:
                    if mqtt_client.connect(timeout=10):
                        logger.info("Reconnected to MQTT broker")
                        break
                    else:
                        logger.warning(
                            f"MQTT reconnection failed, retrying in {retry_delay} seconds...")
                        # Sleep in short intervals to respond to signals
                        for _ in range(retry_delay):
                            if not self.running:
                                break
                            time.sleep(1)

                        # Exponential backoff
                        retry_delay = min(retry_delay * 2, max_retry_delay)

                if not self.running:
                    break

            logger.debug(
                f"Starting fetch cycle (interval: {config.http_interval}s)")

            for fetcher in data_fetchers:
                if not self.running:
                    break

                system_id = fetcher.system_id
                logger.debug(f"Fetching data for system_id: {system_id}")

                # Fetch and Merge Data
                merged_data = fetcher.fetch_all()

                # Construct topic for this system_id
                # Append system_id to base topic
                system_topic = f"{config.mqtt_topic}/{system_id}"

                if merged_data:
                    logger.debug(
                        f"Publishing merged data for {system_id} to {system_topic}")
                    mqtt_client.publish(merged_data, topic=system_topic)
                    logger.info(
                        f"Data for {system_id} published successfully")
                else:
                    logger.warning(
                        f"No data to publish for system_id: {system_id} (endpoints failed or returned empty)")

            # Sleep in short intervals to respond to signals faster
            for _ in range(config.http_interval):
                if not self.running:
                    break
                time.sleep(1)

        mqtt_client.disconnect()
        logger.info("Daemon stopped")


def main():
    config_path = os.getenv("CONFIG_FILE", "config.yaml")
    try:
        config = Config.load(config_path)
    except Exception as e:
        logger.critical(f"Configuration error: {e}")
        sys.exit(1)

    daemon = Daemon(config)
    daemon.run()


if __name__ == "__main__":
    main()
