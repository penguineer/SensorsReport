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


def emit_labels(mqtt_client, mqtt_prefix, cfg_sensors):
    for sensor in cfg_sensors:
        topic = mqtt_prefix + sensor['topic']
        label = sensor.get('label')
        if label is not None:
            mqtt_client.publish(
                "{}/Label".format(topic),
                label
            )


def emit_chip_values(mqtt_client, mqtt_prefix, cfg_chips, sensor_chip):
    if str(sensor_chip) in cfg_chips:
        cfg_features = cfg_chips.get(str(sensor_chip), list())
        for sensor_feature in sensor_chip:
            cfg_feature = cfg_features['features'].get(sensor_feature.name)
            if cfg_feature is not None:
                topic = mqtt_prefix + cfg_feature['mqtt']
                logging.info("%s  %s: %.2f", topic, sensor_feature.label, sensor_feature.get_value())
                mqtt_client.publish(
                    "{}/Value".format(topic),
                    sensor_feature.get_value()
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

    cfg_chips = json.loads(util.load_env("SENSORS", "{}"))
    if not verify_sensor_config(cfg_chips):
        logging.error("Invalid sensor configuration. Exiting.")
        sys.exit(1)
    logging.info("Running with sensors config:\n %s", json.dumps(cfg_chips, indent=4))

    global running
    signal.signal(signal.SIGINT, sigint_handler)

    mqtt_config = mqtt.MqttConfig.from_env("MQTT_")
    logging.info("Running with MQTT config: %s", mqtt_config)
    mqtt_client = mqtt.create_client(mqtt_config, on_disconnect_cb=mqtt_disconnect_handler)

    mqtt_prefix = mqtt_config.prefix

    emit_labels(mqtt_client, mqtt_prefix, cfg_chips['sensors'])

    sensors.init()
    try:
        while running:
            for sensor_chip in sensors.iter_detected_chips():
                logging.info("%s at %s", sensor_chip, sensor_chip.adapter_name)
                emit_chip_values(mqtt_client, mqtt_prefix, cfg_chips, sensor_chip)

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
