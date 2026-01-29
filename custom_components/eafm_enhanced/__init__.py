"""The EAFM-Enhanced integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import aioeafm_local as aioeafm
from .const import DOMAIN, CONF_STATION, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EAFM-Enhanced from a config entry."""
    session = async_get_clientsession(hass)
    station_ref = entry.data[CONF_STATION]

    # Initialize the coordinator
    coordinator = EafmUpdateCoordinator(hass, session, station_ref)

    # Fetch initial data so we don't spawn empty sensors
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator so sensor.py can access it
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class EafmUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, session, station_ref):
        """Initialize."""
        self.session = session
        self.station_ref = station_ref
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"EAFM Station {station_ref}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            # Fetches the full station data (measures, status, etc)
            station = await aioeafm.get_station(self.session, self.station_ref)
            if not station or not station.measures:
                raise UpdateFailed(f"No measures found for {self.station_ref}")
            return station
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")