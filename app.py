#!/usr/bin/env python3

# Author: Stefan Haun <tux@netz39.de>

import signal
import sys
import json

import mqtt

import sensors

running = True


def sigint_handler(_signal, _frame):
    global running

    if running:
        print("SIGINT received. Stopping the queue.")
        running = False
    else:
        print("Receiving SIGINT the second time. Exit.")
        sys.exit(0)


def main():
    signal.signal(signal.SIGINT, sigint_handler)

    with open("sensors-report-cfg.json", "r") as f:
        config = json.load(f)

    if 'mqtt' not in config:
        raise ValueError("Missing mqtt section in configuration! See template for an example.")
    mqtt_config = config.get('mqtt')
    mqtt_client = mqtt.create_client(mqtt_config)


if __name__ == '__main__':
    main()
