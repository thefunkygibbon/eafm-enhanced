"""Config flow for Environment Agency Flood Monitoring integration."""
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import aioeafm_local as aioeafm
from .const import DOMAIN

class EafmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EAFM."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["station_name"], 
                data={"station": user_input["station"]}
            )

        session = async_get_clientsession(self.hass)
        try:
            # This uses your local library to fetch all stations
            all_stations = await aioeafm.get_stations(session)
            
            # This builds the dropdown list: "Station Label (Catchment Name)"
            stations = {
                station.station_reference: f"{station.label} ({station.catchment_name})"
                for station in all_stations
            }
            
            # Sort them alphabetically by label
            sorted_stations = dict(sorted(stations.items(), key=lambda item: item[1]))

        except (aiohttp.ClientError, Exception):
            return self.async_abort(reason="cannot_connect")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("station"): vol.In(sorted_stations),
                vol.Required("station_name"): str,
            }),
            errors=errors,
        )