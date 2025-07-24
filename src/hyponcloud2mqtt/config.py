"""Configuration loading module."""

import yaml


def load_config():
    """Loads configuration from config.yaml."""
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
