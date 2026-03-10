import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfInformation
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, CONF_HOST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up the sensor platform from a Config Flow entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]
    data = coordinator.data

    entities = []

    # 1. System Sensors
    entities.append(HostSystemSensor(coordinator, host, "hostname", "Hostname", None, None, "mdi:nas"))
    entities.append(HostSystemSensor(coordinator, host, "cpu_usage", "CPU Usage", PERCENTAGE, None, "mdi:cpu-64-bit"))
    entities.append(HostSystemSensor(coordinator, host, "memory_total_gb", "Total Memory", UnitOfInformation.GIGABYTES, SensorDeviceClass.DATA_SIZE, "mdi:memory"))
    entities.append(HostSystemSensor(coordinator, host, "memory_free_gb", "Free Memory", UnitOfInformation.GIGABYTES, SensorDeviceClass.DATA_SIZE, "mdi:memory"))

    # 2. Partition Sensors
    for part in data.get("system", {}).get("partitions", []):
        entities.append(PartitionSensor(coordinator, host, part["device"], part["mountpoint"]))

    # 3. Directory Sensors
    for directory in data.get("directories", {}).keys():
        entities.append(DirMonitorSensor(coordinator, host, directory))

    async_add_entities(entities)

class HostSystemSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, host, key, name, unit, device_class, icon):
        super().__init__(coordinator)
        self._host = host
        self._key = key
        
        self._attr_name = name
        self._attr_unique_id = f"dir_monitor_{host}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_has_entity_name = True
        
        # Strings (like hostname) don't have a state class
        if key != "hostname":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        """Link this entity to the server Device."""
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": f"Linux Server ({self._host})",
            "manufacturer": "Directory Monitor",
            "model": "Debian API Node",
        }

    @property
    def native_value(self):
        return self.coordinator.data.get("system", {}).get(self._key)

class PartitionSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, host, device, mountpoint):
        super().__init__(coordinator)
        self._host = host
        self._device = device
        
        # Extract the partition name (e.g., sda1 from /dev/sda1)
        dev_name = device.split('/')[-1]
        
        self._attr_name = f"Partition {dev_name} Free"
        self._attr_unique_id = f"dir_monitor_{host}_part_{dev_name}"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:harddisk"
        self._attr_has_entity_name = True
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        """Link this entity to the server Device."""
        return {"identifiers": {(DOMAIN, self._host)}}

    @property
    def native_value(self):
        parts = self.coordinator.data.get("system", {}).get("partitions", [])
        for p in parts:
            if p["device"] == self._device:
                return p["free_percent"]
        return None

class DirMonitorSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, host, directory):
        super().__init__(coordinator)
        self._host = host
        self._directory = directory
        
        # Only use the top-level name (e.g. /var/log/apt -> apt)
        base_name = directory.rstrip('/').split('/')[-1]
        
        self._attr_name = f"Dir: {base_name}" if base_name else "Dir: Root"
        self._attr_unique_id = f"dir_monitor_{host}_{directory}".replace("/", "_")
        self._attr_icon = "mdi:folder-information"
        self._attr_has_entity_name = True
        
        # State class + unit of measurement ensures HA graphs this as a continuous line
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "files" 

    @property
    def device_info(self):
        """Link this entity to the server Device."""
        return {"identifiers": {(DOMAIN, self._host)}}

    @property
    def native_value(self):
        """The state of the sensor is the number of files."""
        if self._directory in self.coordinator.data.get("directories", {}):
            return self.coordinator.data["directories"][self._directory]["num_files"]
        return None

    @property
    def extra_state_attributes(self):
        """Attach size in GB and timestamps as attributes."""
        if self._directory in self.coordinator.data.get("directories", {}):
            data = self.coordinator.data["directories"][self._directory]
            return {
                "size_gb": float(data["size_gb"]),
                "created_date": data["created_date"],
                "modified_date": data["modified_date"],
                "full_path": self._directory 
            }
        return {}
