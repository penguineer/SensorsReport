#!/usr/bin/env python3
# Author: Stefan Haun <tux@netz39.de>

import signal
import sys
import json
import time
import os

import mqtt

import sensors

import logging
import util

running = True


def sigint_handler(_signal, _frame):
    global running

    if running:
        logging.info("SIGINT received. Stopping the queue.")
        running = False
    else:
        logging.info("Receiving SIGINT the second time. Exit.")
        sys.exit(0)

def mqtt_disconnect_handler(rc):
    if running:  # Only warn if the app is still running
        logging.warning("MQTT client disconnected unexpectedly with code %s", rc)


def verify_sensor_config(cfg):
    """
    Verifies the structure of the updated sensor configuration.

    Args:
        cfg (dict): The sensor configuration to verify.

    Returns:
        bool: True if the configuration is valid, False otherwise.
    """

    # Define required fields for each sensor
    REQUIRED_FIELDS = ["label", "topic"]

    # Define required fields for each configuration type
    PROVIDER_FIELDS = {
        "lm-sensors": ["chip", "feature"]
    }

    if not isinstance(cfg, dict):
        logging.error("Configuration must be a dictionary.")
        return False

    sensors = cfg.get("sensors")
    if not isinstance(sensors, list):
        logging.error("Configuration must contain a 'sensors' list.")
        return False

    for sensor in sensors:
        if not isinstance(sensor, dict):
            logging.error("Each sensor must be a dictionary.")
            return False

        # Validate required fields
        if not all(isinstance(sensor.get(field), str) for field in REQUIRED_FIELDS):
            missing = [field for field in REQUIRED_FIELDS if field not in sensor]
            logging.error("Sensor is missing required fields: %s", ", ".join(missing))
            return False

        # Ensure exactly one provider field is specified
        specified_providers = [key for key in PROVIDER_FIELDS if key in sensor]
        if len(specified_providers) != 1:
            if not specified_providers:
                logging.error(
                    "Sensor must contain exactly one provider configuration. Possible providers: %s",
                    ", ".join(PROVIDER_FIELDS.keys())
                )
            else:
                logging.error(
                    "Sensor must not contain more than one provider configuration. Found: %s",
                    ", ".join(specified_providers)
                )
            return False

        # Validate the fields of the specified provider
        provider = specified_providers[0]
        config = sensor[provider]
        if not isinstance(config, dict):
            logging.error("'%s' must be a dictionary.", provider)
            return False
        if not all(isinstance(config.get(field), str) for field in PROVIDER_FIELDS[provider]):
            missing = [field for field in PROVIDER_FIELDS[provider] if field not in config]
            logging.error("'%s' is missing required fields: %s", provider, ", ".join(missing))
            return False

    if not cfg["sensors"]:
        logging.warning("No sensors defined in the configuration!")

    return True


def read_lm_sensors_data():
    """
    Reads sensor data using the lm-sensors library and organizes them into a dictionary.

    Returns:
        dict: A dictionary where each key is a sensor chip name, and the value is another dictionary
              containing 'adapter_name' and 'features' (a dictionary of feature names and their values).
    """
    sensor_data = {}

    for sensor_chip in sensors.iter_detected_chips():
        chip_name = str(sensor_chip)
        adapter_name = sensor_chip.adapter_name
        features = {}

        for feature in sensor_chip:
            try:
                feature_value = feature.get_value()
                features[feature.name] = feature_value
            except Exception as e:
                logging.error("Failed to read value for feature '%s' on chip '%s': %s", feature.name, chip_name, e)

        sensor_data[chip_name] = {
            "adapter_name": adapter_name,
            "features": features
        }

    return sensor_data


def emit_labels(mqtt_client, mqtt_prefix, cfg_sensors):
    for sensor in cfg_sensors:
        topic = mqtt_prefix + sensor['topic']
        label = sensor.get('label')
        if label is not None:
            mqtt_client.publish(
                "{}/Label".format(topic),
                label
            )


def emit_sensor_data(mqtt_client, mqtt_prefix, lm_sensor_data, cfg_sensors):
    """
    Emits sensor data to MQTT topics based on the provided configuration.

    Args:
        mqtt_client: The MQTT client used for publishing.
        mqtt_prefix (str): The prefix for MQTT topics.
        lm_sensor_data (dict): The dictionary containing sensor data.
        cfg_sensors (list): The configuration for sensors.
    """
    for sensor_cfg in cfg_sensors:
        provider = sensor_cfg.get("lm-sensors")
        if not provider:
            continue

        chip_name = provider.get("chip")
        feature_name = provider.get("feature")

        if not chip_name in lm_sensor_data:
            logging.warning("Chip '%s' not found in lm-sensors data.", chip_name)
        else:
            chip_data = lm_sensor_data[chip_name]
            feature_value = chip_data["features"].get(feature_name)

            if feature_value is None:
                logging.warning("Feature '%s' in chip '%s' did not provide a value.", feature_name, chip_name)
            else:
                topic = mqtt_prefix + sensor_cfg["topic"]

                logging.info(
                    "Emitting chip='%s', feature='%s', value=%.2f, adapter='%s' to '%s'",
                    chip_name, feature_name, feature_value, chip_data["adapter_name"], topic
                )

                mqtt_client.publish(
                    f"{topic}/Value",
                    feature_value
                )


def get_log_level():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return levels.get(log_level, logging.INFO)

def main():
    # Configure logging
    logging.basicConfig(
        level=get_log_level(),  # Set the logging level to INFO
        format='%(asctime)s - %(levelname)s - %(message)s',  # Define the log message format
        handlers=[logging.StreamHandler()]  # Add a handler to output logs to the console
    )

    cfg_sensors = json.loads(util.load_env("SENSORS", "{}"))
    if not verify_sensor_config(cfg_sensors):
        logging.error("Invalid sensor configuration. Exiting.")
        sys.exit(1)
    logging.info("Running with sensors config:\n %s", json.dumps(cfg_sensors, indent=4))

    global running
    signal.signal(signal.SIGINT, sigint_handler)

    mqtt_config = mqtt.MqttConfig.from_env("MQTT_")
    logging.info("Running with MQTT config: %s", mqtt_config)
    mqtt_client = mqtt.create_client(mqtt_config, on_disconnect_cb=mqtt_disconnect_handler)

    mqtt_prefix = mqtt_config.prefix

    emit_labels(mqtt_client, mqtt_prefix, cfg_sensors['sensors'])

    sensors.init()
    try:
        while running:
            lm_sensor_data = read_lm_sensors_data()
            emit_sensor_data(mqtt_client, mqtt_prefix, lm_sensor_data, cfg_sensors['sensors'])

            timer = 5
            while timer > 0 and running:
                time.sleep(1)
                timer = timer - 1

    finally:
        sensors.cleanup()

    # noinspection PyUnreachableCode
    if mqtt_client.is_connected():
        mqtt_client.disconnect()
        mqtt_client.loop_stop()

    logging.info("Exiting.")


if __name__ == '__main__':
    main()
