# hyponcloud2mqtt

[![PyPI version](https://badge.fury.io/py/hyponcloud2mqtt.svg)](https://badge.fury.io/py/hyponcloud2mqtt)
[![Build Status](https://github.com/fligneul/hyponcloud2mqtt/actions/workflows/main.yml/badge.svg)](https://github.com/fligneul/hyponcloud2mqtt/actions/workflows/main.yml)

A bridge to connect the Hypon Cloud API to an MQTT broker. This application periodically fetches data from your Hypon system and publishes it to your MQTT broker, allowing for easy integration with home automation systems like Home Assistant.

## Features

*   Fetches the latest data from the Hypon Cloud API.
*   Publishes data to a configurable MQTT topic.
*   Automatically handles API token acquisition and renewal.
*   Configuration via a simple `config.yaml` file.
*   Support for retained MQTT messages.
*   Can be run directly with Python or as a Docker container.
*   Installable via PyPI.

## Prerequisites

*   Python 3.9 or later.
*   A Hypon Cloud account.
*   An MQTT broker.
*   Docker (optional, for containerized deployment).

## Installation

### From PyPI

You can install the package directly from PyPI:

```bash
pip install hyponcloud2mqtt
```

### From Source

For development, you can clone the repository and install the package in editable mode:

```bash
git clone https://github.com/fligneul/hyponcloud2mqtt.git
cd hyponcloud2mqtt
pip install -e .
```

## Configuration

Before running the application, you need to create a `config.yaml` file. A template is provided in `config.yaml.dist`. Copy it and edit it with your details:

```bash
cp config.yaml.dist config.yaml
```

Then, edit `config.yaml`:

```yaml
hypon:
  # Your Hypon Cloud username
  user: "YOUR_USER"
  # Your Hypon Cloud password
  password: "YOUR_PASSWORD"
  # Base URL for the Hypon Cloud API
  api_base_url: "https://api.hypon.cloud/v2"
  # List of system IDs to fetch data for (e.g., ["YOUR_SYSTEM_ID_1", "YOUR_SYSTEM_ID_2"])
  system_ids:
    - "YOUR_SYSTEM_ID"
  # Interval in seconds between data fetches from Hypon Cloud (default: 60)
  interval: 60

# MQTT broker configuration
mqtt:
  # MQTT broker hostname or IP address
  host: "localhost"
  # MQTT broker port (default: 1883)
  port: 1883
  # MQTT username (optional)
  user: ""
  # MQTT password (optional)
  password: ""
  # Base MQTT topic for publishing data (e.g., "hyponcloud2mqtt/status")
  topic: "hyponcloud2mqtt/status"
  # Set to true to have messages retained by the broker (default: false)
  retain: false
  # Set to true to prevent actual MQTT publishing (for testing purposes, default: true)
  dry_run: true
  # MQTT Publish Modes:
  #   - 'full': Publishes the entire data object as a single JSON string to a topic like 'hyponcloud2mqtt/system_id/full_data'. (Default)
  #   - 'individual': Publishes each data attribute to a dedicated topic, e.g., 'hyponcloud2mqtt/system_id/power_pv'.
  publish_mode: full
```

## Usage

### As a Command-Line Tool

If you installed the package via `pip`, you can run it directly:

```bash
hyponcloud2mqtt
```

Alternatively, you can run it as a Python module:

```bash
python -m hyponcloud2mqtt
```

### Using Docker

This is the recommended way to run the application as a long-running service.

1.  **Build the Docker image:**

    ```bash
    docker build -t hyponcloud2mqtt .
    ```

2.  **Run the container:**

    Make sure your `config.yaml` file is in the current directory. The command below will mount it into the container.

    ```bash
    docker run -d \
      --name hyponcloud2mqtt \
      --restart unless-stopped \
      -v $(pwd)/config.yaml:/app/config.yaml \
      hyponcloud2mqtt
    ```

    *   `-d`: Runs the container in detached mode.
    *   `--restart unless-stopped`: Ensures the container restarts automatically if it crashes.
    *   `-v $(pwd)/config.yaml:/app/config.yaml`: Mounts your local configuration file into the container.

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.