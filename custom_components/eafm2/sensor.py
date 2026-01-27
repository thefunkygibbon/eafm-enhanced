"""Support for Environment Agency Flood Monitoring sensors."""
from datetime import timedelta
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import aioeafm_local as aioeafm

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensors."""
    session = async_get_clientsession(hass)
    station_ref = entry.data["station"]
    
    try:
        station = await aioeafm.get_station(session, station_ref)
        # Create a sensor for every 'measure' (Level, Flow, etc.) the station has
        entities = [EafmSensor(session, station, measure) for measure in station.measures]
        async_add_entities(entities, True)
    except Exception as err:
        _LOGGER.error("Failed to set up EAFM sensors: %s", err)
        return False

class EafmSensor(SensorEntity):
    """Representation of an EAFM sensor."""

    def __init__(self, session, station, measure):
        self._session = session
        self._station = station
        self._measure = measure
        self._attr_name = f"{station.label} {measure.label}"
        self._attr_unique_id = f"{station.station_reference}_{measure.label}"
        self._state = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        """Update is handled by the data returned in the initial fetch for now."""
        # You can add logic here later to fetch specific readings
        pass