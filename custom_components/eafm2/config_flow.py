"""Config flow for Environment Agency Flood Gauges Fixed."""
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import aioeafm_local as aioeafm
from .const import DOMAIN

class EafmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EAFM2."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        # We need to fetch stations for both the form and the final selection
        session = async_get_clientsession(self.hass)
        try:
            all_stations = await aioeafm.get_stations(session)
        except (aiohttp.ClientError, Exception):
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            # Find the actual label of the station they picked
            selected_ref = user_input["station"]
            # Look through our list to find the matching station object
            selected_station = next((s for s in all_stations if s.station_reference == selected_ref), None)
            
            # Use the station's label as the entry title automatically
            title = selected_station.label if selected_station else "Flood Gauge"
            
            return self.async_create_entry(
                title=title, 
                data={"station": selected_ref}
            )

        # Build the dropdown list for the UI
        stations_dropdown = {}
        for station in all_stations:
            # We build the string: "Label, Catchment (ID)"
            # We use .get() or a fallback just in case some data is missing
            display_name = f"{station.label}, {station.catchment_name}"
            
            if station.rloi_id:
                display_name += f" ({station.rloi_id})"
            
            stations_dropdown[station.station_reference] = display_name
        
        # Sort them alphabetically by the new display name
        sorted_stations = dict(sorted(stations_dropdown.items(), key=lambda item: item[1]))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("station"): vol.In(sorted_stations),
            }),
            errors=errors,
        )