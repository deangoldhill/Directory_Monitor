import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_HOST, CONF_API_KEY, CONF_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_API_KEY): str,
    vol.Optional(CONF_UPDATE_INTERVAL, default=300): int,
})

class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""

async def validate_input(hass: HomeAssistant, data: dict):
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    url = f"http://{data[CONF_HOST]}:7112/api/stats"
    
    async with session.get(url, headers={"X-API-Key": data[CONF_API_KEY]}, timeout=10) as response:
        if response.status in (401, 403):
            raise InvalidAuth
        response.raise_for_status()
        return await response.json()

class DirMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Prevent adding the same host twice
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                await validate_input(self.hass, user_input)
                # Success! Create the entry in Home Assistant
                return self.async_create_entry(
                    title=f"Linux Server ({user_input[CONF_HOST]})", 
                    data=user_input
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
