import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform via Config Flow."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]

    entities = []
    if coordinator.data:
        for directory in coordinator.data.keys():
            entities.append(DirMonitorSensor(coordinator, host, directory))

    async_add_entities(entities)

class DirMonitorSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, host, directory):
        super().__init__(coordinator)
        self._host = host
        self._directory = directory
        
        self._attr_unique_id = f"dir_monitor_{host}_{directory}".replace("/", "_")
        self._attr_has_entity_name = True
        self._attr_name = directory 
        self._attr_icon = "mdi:folder-information"

    @property
    def device_info(self):
        """Link this entity to a device based on the host IP."""
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": f"Linux Server ({self._host})",
            "manufacturer": "Directory Monitor",
            "model": "Debian API Node",
            "sw_version": "1.0.0"
        }

    @property
    def native_value(self):
        """The state of the sensor is the number of files."""
        if self.coordinator.data and self._directory in self.coordinator.data:
            return self.coordinator.data[self._directory]["num_files"]
        return None

    @property
    def extra_state_attributes(self):
        """Attach size in GB and timestamps as attributes."""
        if self.coordinator.data and self._directory in self.coordinator.data:
            data = self.coordinator.data[self._directory]
            return {
                "size_gb": data["size_gb"],
                "created_date": data["created_date"],
                "modified_date": data["modified_date"]
            }
        return {}
