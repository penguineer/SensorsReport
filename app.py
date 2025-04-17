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


def emit_labels(mqtt_client, mqtt_prefix, cfg_chips):
    for chip in cfg_chips:
        features = cfg_chips.get(chip, list())
        for feature_name, feature in features['features'].items():
            topic = mqtt_prefix + feature['mqtt']
            label = feature.get('label')
            if label is not None:
                mqtt_client.publish(
                    "{}/Label".format(topic),
                    label
                )
            else:
                logging.warning("No label found for %s/%s", chip, feature_name)


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

    global running
    signal.signal(signal.SIGINT, sigint_handler)

    mqtt_config = mqtt.MqttConfig.from_env("MQTT_")
    logging.info("Running with MQTT config: %s", mqtt_config)
    mqtt_client = mqtt.create_client(mqtt_config, on_disconnect_cb=mqtt_disconnect_handler)

    mqtt_prefix = mqtt_config.prefix

    cfg_chips = json.loads(util.load_env("SENSORS", "{}"))
    logging.info("Running with sensors config:\n %s", json.dumps(cfg_chips, indent=4))

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
