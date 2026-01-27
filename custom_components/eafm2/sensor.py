"""Support for Environment Agency Flood Monitoring sensors."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from . import aioeafm_local as aioeafm

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensors via the config entry."""
    session = async_get_clientsession(hass)
    station_ref = entry.data["station"]
    
    try:
        station = await aioeafm.get_station(session, station_ref)
        measures = station.measures
        
        if not measures:
            _LOGGER.warning("Station %s has no measures available", station_ref)
            return

        entities = [EafmSensor(station, m) for m in measures]
        async_add_entities(entities, True)
    except Exception as err:
        _LOGGER.error("Error setting up sensors for %s: %s", station_ref, err)

class EafmSensor(SensorEntity):
    """Representation of an EAFM sensor."""

    def __init__(self, station, measure):
        self._station = station
        self._measure = measure
        
        # Identity
        self._attr_name = f"{station.label} {measure.label}"
        self._attr_unique_id = f"{station.station_reference}_{measure.parameter}_{measure.data.get('qualifier', '')}"
        
        # Get the value safely
        reading = measure.data.get("latestReading")
        if isinstance(reading, dict):
            self._state = reading.get("value")
        else:
            self._state = None
            
        self._attr_native_unit_of_measurement = measure.data.get("unitName")

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {
            "catchment": self._station.catchment_name,
            "river": self._station.data.get("riverName"),
            "qualifier": self._measure.data.get("qualifier")
        }

    async def async_update(self):
        """Update logic can be added later if needed."""
        pass