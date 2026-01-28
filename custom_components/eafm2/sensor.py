"""Support for Environment Agency Flood Monitoring sensors."""
import logging
from homeassistant.components.sensor import SensorEntity
from . import aioeafm_local as aioeafm

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensors via the config entry."""
    session = async_get_clientsession(hass) # Note: ensure this helper is imported or used as before
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    session = async_get_clientsession(hass)
    
    station_ref = entry.data["station"]
    
    try:
        station = await aioeafm.get_station(session, station_ref)
        
        if not station.measures:
            return

        entities = []
        # Add the standard level/flow sensors
        for measure in station.measures:
            entities.append(EafmSensor(station, measure))
            
        # Add the NEW Status Sensor
        if station.stage_scale:
            entities.append(EafmStatusSensor(station))
            
        async_add_entities(entities, True)
    except Exception as err:
        _LOGGER.error("Error setting up sensors: %s", err)

class EafmSensor(SensorEntity):
    """Representation of an EAFM sensor."""

    def __init__(self, station, measure):
        self._station = station
        self._measure = measure
        
        # Naming: "Station Name - Level"
        self._attr_name = f"{station.label} {measure.label}"
        # Unique ID: "StationRef_Parameter_Qualifier"
        self._attr_unique_id = f"{station.station_reference}_{measure.data.get('parameter', 'unknown')}_{measure.data.get('qualifier', '')}"
        
        # Extract the reading value
        reading = measure.data.get("latestReading")
        if isinstance(reading, dict):
            self._state = reading.get("value")
            # If the reading date is needed later, it is reading.get("dateTime")
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
    
class EafmStatusSensor(SensorEntity):
    """A sensor that reports the 'State' of the river (Normal, High, Low)."""

    def __init__(self, station):
        self._station = station
        self._attr_name = f"{station.label} River Status"
        self._attr_unique_id = f"{station.station_reference}_status"
        self._attr_icon = "mdi:waves"
        self._state = "Unknown"

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        """Determine the status by comparing current level to typical range."""
        scale = self._station.stage_scale
        high = scale.get("typicalRangeHigh")
        low = scale.get("typicalRangeLow")
        
        # We need a reading to compare. We'll find the primary 'level' measure.
        current_level = None
        for m in self._station.measures:
            if m.data.get("parameter") == "level":
                reading = m.data.get("latestReading")
                if isinstance(reading, dict):
                    current_level = reading.get("value")
                break

        if current_level is None or high is None or low is None:
            self._state = "Unknown"
            return

        if current_level > high:
            self._state = "High"
        elif current_level < low:
            self._state = "Low"
        else:
            self._state = "Normal"

    @property
    def extra_state_attributes(self):
        scale = self._station.stage_scale
        return {
            "typical_range_high": scale.get("typicalRangeHigh"),
            "typical_range_low": scale.get("typicalRangeLow"),
            "highest_recent": scale.get("highestRecent", {}).get("value")
        }