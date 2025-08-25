# hyponcloud2mqtt

[![PyPI version](https://badge.fury.io/py/hyponcloud2mqtt.svg)](https://badge.fury.io/py/hyponcloud2mqtt)
[![Build Status](https://github.com/fligneul/hyponcloud2mqtt/actions/workflows/main.yml/badge.svg)](https://github.com/fligneul/hyponcloud2mqtt/actions/workflows/main.yml)

A bridge to connect the Hypon Cloud API to an MQTT broker. This application periodically fetches data from your Hypon system and publishes it to your MQTT broker, allowing for easy integration with home automation systems like Home Assistant.

This project was developed and tested using data from an **HMS800-C** inverter. If you are using a different Hypon inverter model and find that some data points are missing or incorrectly mapped, please open an issue on the GitHub repository. Your feedback will help improve compatibility for other users.

## Features

*   Fetches the latest data from the Hypon Cloud API.
*   Publishes data to a configurable MQTT topic.
*   Publishes service status (online/offline) using MQTT Last Will and Testament (LWT).
*   Automatically handles API token acquisition and renewal.
*   Configuration via a simple `config.yaml` file.
*   Support for environment variables for Dockerized deployments.
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

Configuration can be provided through a `config.yaml` file or environment variables. Environment variables will always override the values in the `config.yaml` file.

### `config.yaml`

Before running the application, you need to create a `config.yaml` file. A template is provided in `config.yaml.example`. Copy it and edit it with your details:

```bash
cp config.yaml.example config.yaml
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
```

### Environment Variables

You can also configure the application using environment variables. This is especially useful for Docker deployments.

**Hypon Cloud Configuration:**

*   `HYPON_USER`: Your Hypon Cloud username.
*   `HYPON_PASSWORD`: Your Hypon Cloud password.
*   `HYPON_API_BASE_URL`: Base URL for the Hypon Cloud API.
*   `HYPON_SYSTEM_IDS`: Comma-separated list of system IDs.
*   `HYPON_INTERVAL`: Interval in seconds for data fetching.
*   `HYPON_RETRIES`: Number of retries on fetch failure.

**MQTT Configuration:**

*   `MQTT_HOST`: MQTT broker hostname.
*   `MQTT_PORT`: MQTT broker port.
*   `MQTT_USER`: MQTT username.
*   `MQTT_PASSWORD`: MQTT password.
*   `MQTT_TOPIC`: Base MQTT topic.
*   `MQTT_RETAIN`: Set to `true` to retain MQTT messages.

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

    You can either mount a `config.yaml` file or provide the configuration through environment variables.

    **With `config.yaml`:**

    ```bash
docker run -d \
  --name hyponcloud2mqtt \
  --restart unless-stopped \
  -v $(pwd)/config.yaml:/app/config.yaml \
  hyponcloud2mqtt
    ```

    **With environment variables:**

    ```bash
docker run -d \
  --name hyponcloud2mqtt \
  --restart unless-stopped \
  -e HYPON_USER="YOUR_USER" \
  -e HYPON_PASSWORD="YOUR_PASSWORD" \
  -e HYPON_SYSTEM_IDS="YOUR_SYSTEM_ID" \
  -e MQTT_HOST="your_mqtt_broker" \
  hyponcloud2mqtt
    ```

## MQTT Output Example
Assuming a `topic` of `hyponcloud2mqtt` and `system_id` of `123456` in your `config.yaml`:

The entire data object will be published as a single JSON string to:
`hyponcloud2mqtt/123456`

Example Payload:

```json
{
  "monetary": "USD",
  "today_earning": 10.0,
  "month_earning": 100.0,
  "total_earning": 1000.0,
  "e_total": 5000.0,
  "e_month": 500.0,
  "e_today": 50.0,
  "e_year": 2000.0,
  "total_tree": 5,
  "total_co2": 10,
  "total_diesel": 20,
  "percent": 90.0,
  "meter_power": 5.0,
  "power_load": 2.0,
  "w_cha": 1.0,
  "power_pv": 3.0,
  "soc": 0,
  "micro": 1
}
```



## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
