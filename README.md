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

*   Python 3.12 or later.
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
  user: "YOUR_HYPON_USERNAME"
  password: "YOUR_HYPON_PASSWORD"
  # The following URLs are the defaults and may not need to be changed.
  login_url: "https://api.hypon.com/login"
  data_url: "https://api.hypon.com/data"

mqtt:
  host: "your-mqtt-broker-host"
  port: 1883
  user: "your-mqtt-user"       # Optional
  password: "your-mqtt-password" # Optional
  topic: "hyponcloud2mqtt/status"
  retain: false # Set to true to have messages retained by the broker
  publish_mode: full # Options: 'full' (default) or 'individual'
  dry_run: true # Set to true to prevent actual MQTT publishing (default: true)

# MQTT Publish Modes:
#   - 'full': Publishes the entire data object as a single JSON string to a topic like 'hyponcloud2mqtt/system_id/full_data'. (Default)
#   - 'individual': Publishes each data attribute to a dedicated topic, e.g., 'hyponcloud2mqtt/system_id/power_pv'.
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.