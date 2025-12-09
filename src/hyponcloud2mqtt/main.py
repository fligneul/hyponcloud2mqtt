
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

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Daemon:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, stopping...")
        self.running = False

    def run(self):
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
            config.mqtt_ca_path
        )

        # Start Health Server
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
                            logger.info("Stopping before MQTT connection established")
                            sys.exit(0)
                        time.sleep(1)
                    
                    # Exponential backoff
                    retry_delay = min(retry_delay * 2, max_retry_delay)
            
            if not self.running:
                sys.exit(0)
        else:
            logger.info("[DRY RUN] Skipping MQTT connection")

        logger.info(
            f"Starting daemon, fetching every {config.http_interval} seconds")

        # Publish HA Discovery (only if connected or in dry run mode)
        if config.sensors and config.ha_discovery_enabled:
            if mqtt_client.connected or config.dry_run:
                logger.info("Publishing Home Assistant discovery messages...")
                for sensor in config.sensors:
                    mqtt_client.publish_discovery(
                        sensor,
                        config.device_name,
                        config.ha_discovery_prefix,
                        config.mqtt_topic
                    )
            else:
                logger.warning(
                    "Skipping Home Assistant discovery: MQTT not connected")

        # Initialize Data Fetcher
        data_fetcher = DataFetcher(config)

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

            # Fetch and Merge Data
            merged_data = data_fetcher.fetch_all()

            if merged_data:
                logger.debug(f"Publishing merged data to {config.mqtt_topic}")
                mqtt_client.publish(merged_data)
                logger.info("Data published successfully")
            else:
                logger.warning(
                    "No data to publish (all endpoints failed or returned empty)")

            # Sleep in short intervals to respond to signals faster
            for _ in range(config.http_interval):
                if not self.running:
                    break
                time.sleep(1)

        mqtt_client.disconnect()
        logger.info("Daemon stopped")


def main():
    daemon = Daemon()
    daemon.run()


if __name__ == "__main__":
    main()
