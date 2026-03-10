import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_HOST, CONF_API_KEY, CONF_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Directory Monitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    api_key = entry.data[CONF_API_KEY]
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, 300)
    
    url = f"http://{host}:7112/api/stats"
    session = async_get_clientsession(hass)

    async def async_fetch_data():
        try:
            async with session.get(url, headers={"X-API-Key": api_key}, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Transform the directories list into a dictionary for easier access
                dirs_dict = {item["directory"]: item for item in data.get("directories", [])}
                
                return {
                    "system": data.get("system", {}),
                    "directories": dirs_dict
                }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with {host}: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"dir_monitor_{host}",
        update_method=async_fetch_data,
        update_interval=timedelta(seconds=update_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator so the sensor platform can access it
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
