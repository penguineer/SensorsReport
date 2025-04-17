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


def verify_sensor_config(cfg_chips):
    """
    Verifies the structure of a sensor configuration.

    Args:
        cfg_chips (dict): The sensor configuration to verify.

    Returns:
        bool: True if the configuration is valid, False otherwise.
    """
    if not isinstance(cfg_chips, dict):
        logging.error("Configuration must be a dictionary.")
        return False

    for chip_name, chip_data in cfg_chips.items():
        if not isinstance(chip_data, dict):
            logging.error("Chip data for '%s' must be a dictionary.", chip_name)
            return False

        if "features" not in chip_data or not isinstance(chip_data["features"], dict):
            logging.error("Chip '%s' must contain a 'features' dictionary.", chip_name)
            return False

        for feature_name, feature_data in chip_data["features"].items():
            if not isinstance(feature_data, dict):
                logging.error("Feature data for '%s/%s' must be a dictionary.", chip_name, feature_name)
                return False

            if "label" not in feature_data or not isinstance(feature_data["label"], str):
                logging.warning("Feature '%s/%s' does not have a label.", chip_name, feature_name)

            if "mqtt" not in feature_data or not isinstance(feature_data["mqtt"], str):
                logging.error("Feature '%s/%s' must contain an 'mqtt' string.", chip_name, feature_name)
                return False

    return True


def emit_labels(mqtt_client, mqtt_prefix, cfg_chips):
    for chip in cfg_chips:
        features = cfg_chips.get(chip, list())
        for feature in features['features'].values():
            topic = mqtt_prefix + feature['mqtt']
            label = feature.get('label')
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

    emit_labels(mqtt_client, mqtt_prefix, cfg_chips)

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
