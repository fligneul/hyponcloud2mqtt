from __future__ import annotations

import logging
import os
import sys

from .config import Config
from .daemon import Daemon

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    config_path = os.getenv("CONFIG_FILE", "config.yaml")
    try:
        config = Config.load(config_path)
    except Exception as e:
        logger.critical("Configuration error: %s", e)
        sys.exit(1)

    daemon = Daemon(config)
    daemon.run()


if __name__ == "__main__":
    main()
