"""Support for Environment Agency Flood Monitoring sensors."""
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import aioeafm_local as aioeafm

SCAN_INTERVAL = timedelta(minutes=15)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensors."""
    session = async_get_clientsession(hass)
    station_ref = entry.data["station"]
    
    station = await aioeafm.get_station(session, station_ref)
    entities = [EafmSensor(session, station, measure) for measure in station.measures]
    async_add_entities(entities, True)

class EafmSensor(SensorEntity):
    """Representation of an EAFM sensor."""

    def __init__(self, session, station, measure):
        self._session = session
        self._station = station
        self._measure = measure
        self._state = None

    @property
    def name(self):
        return f"{self._station.label} {self._measure.label}"

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        """Fetch new state data."""
        # In a real scenario, you'd fetch the latest reading here
        # For this custom version, we are keeping it simple
        pass