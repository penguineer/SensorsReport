import logging
from abc import ABC, abstractmethod

import sensors as lmsensors

from sensor_data_event import SensorDataEvent

class SensorDataProvider(ABC):
    """
    Abstract base class for a sensor data provider.
    """

    @abstractmethod
    def retrieve(self):
        """
        Retrieve sensor values and return a list of SensorDataEvent objects.

        Returns:
            list[SensorDataEvent]: A list of sensor data events.
        """
        pass


class LmSensorsDataProvider(SensorDataProvider):
    """
    A sensor data provider implementation for lm-sensors.
    """

    def __init__(self, sensors):
        """
        Initialize the LmSensorsDataProvider with a list of sensors.

        Args:
            sensors (list[dict]): A list of sensor configurations.
        """
        self.sensors = [sensor for sensor in sensors if 'lm-sensors' in sensor]
        logging.info("Lm-sensors provider initialized with %s sensors", len(self.sensors))

        lmsensors.init()

    def retrieve(self):
            """
            Retrieve sensor values and return a list of SensorDataEvent objects.

            Returns:
                list[SensorDataEvent]: A list of sensor data events.
            """
            sensor_data = self.read_lm_sensors_data()

            # Create SensorDataEvent objects for valid sensors
            events = [
                SensorDataEvent(sensor, sensor_data[config['chip']]['features'][config['feature']])
                for sensor in self.sensors
                if (config := sensor.get('lm-sensors'))  # Extract lm-sensors config
                and config['chip'] in sensor_data  # Check if chip exists
                and config['feature'] in sensor_data[config['chip']]['features']  # Check if feature exists
            ]

            # Log warnings for missing chips or features
            for sensor in self.sensors:
                config = sensor.get('lm-sensors')
                if not config:
                    continue
                if config['chip'] not in sensor_data:
                    logging.warning("Chip '%s' not found in lm-sensors data.", config['chip'])
                elif config['feature'] not in sensor_data[config['chip']]['features']:
                    logging.warning("Feature '%s' not found for chip '%s'.", config['feature'], config['chip'])

            return events

    def __del__(self):
        """
        Cleanup lm-sensors resources when the provider is deleted.
        """
        logging.info("Cleaning up lm-sensors resources.")
        lmsensors.cleanup()

    @staticmethod
    def read_lm_sensors_data():
        """
        Reads sensor data using the lm-sensors library and organizes them into a dictionary.

        Returns:
            dict: A dictionary where each key is a sensor chip name, and the value is another dictionary
                  containing 'adapter_name' and 'features' (a dictionary of feature names and their values).
        """
        sensor_data = {}

        for sensor_chip in lmsensors.iter_detected_chips():
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
