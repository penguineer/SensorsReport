from abc import ABC, abstractmethod
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

