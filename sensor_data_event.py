class SensorDataEvent:
    """
    Represents a measurement from one sensor.

    Attributes:
        sensor_config (dict): The configuration of the sensor that created the event, as provided in the sensors configuration.
        value (float): The measured value from the sensor.
    """
    def __init__(self, sensor_config, value):
        self.sensor_config = sensor_config
        self.value = value

    def __repr__(self):
        return f"SensorDataEvent(sensor_config={self.sensor_config}, value={self.value})"
