"""Support for Environment Agency Flood Monitoring sensors."""
from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import aioeafm_local as aioeafm

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensors via the config entry."""
    session = async_get_clientsession(hass)
    station_ref = entry.data["station"]
    
    try:
        # Fetch the station data
        station = await aioeafm.get_station(session, station_ref)
        
        if not station.measures:
            _LOGGER.warning("Station %s has no measures available", station_ref)
            return

        # Create entities for each measure (Level, Flow, etc.)
        entities = [EafmSensor(station, measure) for measure in station.measures]
        
        # async_add_entities is the 3rd argument that was causing the error!
        async_add_entities(entities, True)
        
    except Exception as err:
        _LOGGER.error("Error setting up EAFM2 sensors for %s: %s", station_ref, err)

class EafmSensor(SensorEntity):
    """Representation of an EAFM sensor."""

    def __init__(self, station, measure):
        self._station = station
        self._measure = measure
        
        # Identity
        self._attr_name = f"{station.label} {measure.label}"
        self._attr_unique_id = f"{station.station_reference}_{measure.label}"
        
        # Attempt to get the latest value from the initial data
        # 'latestReading' is the standard key in the EA API
        reading = measure.data.get("latestReading", {})
        self._state = reading.get("value")
        self._attr_native_unit_of_measurement = measure.data.get("unitName")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Add the Catchment Name as an attribute for extra clarity."""
        return {
            "catchment": self._station.catchment_name,
            "river": self._station.data.get("riverName"),
            "station_reference": self._station.station_reference
        }

    async def async_update(self):
        """Update data - in this basic version, we rely on the initial fetch or a reload."""
        pass