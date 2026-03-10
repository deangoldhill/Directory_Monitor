import logging
from datetime import timedelta
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity, UpdateFailed
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

CONF_SERVERS = "servers"
CONF_UPDATE_INTERVAL = "update_interval"

SERVER_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SERVERS): vol.All(cv.ensure_list, [SERVER_SCHEMA]),
    vol.Optional(CONF_UPDATE_INTERVAL, default=300): cv.positive_int,
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    servers = config[CONF_SERVERS]
    update_interval = config[CONF_UPDATE_INTERVAL]
    session = async_get_clientsession(hass)

    entities = []

    for server in servers:
        host = server[CONF_HOST]
        api_key = server[CONF_API_KEY]
        url = f"http://{host}:7112/api/stats"

        def create_fetch_method(fetch_url, fetch_key):
            async def async_fetch_data():
                try:
                    async with session.get(fetch_url, headers={"X-API-Key": fetch_key}, timeout=10) as response:
                        response.raise_for_status()
                        data = await response.json()
                        return {item["directory"]: item for item in data}
                except Exception as err:
                    raise UpdateFailed(f"Error communicating with {fetch_url}: {err}")
            return async_fetch_data

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"dir_monitor_{host}",
            update_method=create_fetch_method(url, api_key),
            update_interval=timedelta(seconds=update_interval),
        )

        await coordinator.async_config_entry_first_refresh()

        if coordinator.data:
            for directory in coordinator.data.keys():
                entities.append(DirMonitorSensor(coordinator, host, directory))

    if entities:
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
            "identifiers": {("dir_monitor", self._host)},
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
