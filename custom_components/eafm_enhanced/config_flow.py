"""Config flow for EAFM-Enhanced integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import aioeafm_local as aioeafm

_LOGGER = logging.getLogger(__name__)

class EafmConfigFlow(config_entries.ConfigFlow, domain="eafm_enhanced"):
    """Handle a config flow for EAFM-Enhanced."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input["station"])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Station {user_input['station']}", 
                data=user_input
            )

        session = async_get_clientsession(self.hass)
        try:
            all_stations = await aioeafm.get_stations(session)
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "cannot_connect"
            return self.async_abort(reason="cannot_connect")

        stations_dropdown = {}
        for station in all_stations:
            display_name = f"{station.label}, {station.catchment_name}"
            if station.rloi_id:
                display_name += f" ({station.rloi_id})"
            
            stations_dropdown[station.station_reference] = display_name
        
        sorted_stations = dict(sorted(stations_dropdown.items(), key=lambda item: item[1]))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("station"): vol.In(sorted_stations),
            }),
            errors=errors,
        )