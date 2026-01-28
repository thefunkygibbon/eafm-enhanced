"""Support for Environment Agency Flood Monitoring sensors."""
import logging
from datetime import timedelta

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
        station = await aioeafm.get_station(session, station_ref)
        
        if not station or not station.measures:
            _LOGGER.warning("Station %s found, but no measures were listed", station_ref)
            return

        entities = []
        
        # 1. Add standard level/flow sensors
        for measure in station.measures:
            entities.append(EafmSensor(station, measure))
            
        # 2. Add the Status Sensor (Normal/High/Low)
        # Check if stage_scale is a dict and not empty
        if hasattr(station, 'stage_scale') and station.stage_scale:
            entities.append(EafmStatusSensor(station))
            
        async_add_entities(entities, True)
    except Exception as err:
        _LOGGER.error("Error setting up sensors for %s: %s", station_ref, err)

class EafmSensor(SensorEntity):
    """Standard level/flow sensor."""

    def __init__(self, station, measure):
        self._station = station
        self._measure = measure
        self._attr_name = f"{station.label} {measure.label}"
        self._attr_unique_id = f"{station.station_reference}_{measure.data.get('parameter', 'unknown')}_{measure.data.get('qualifier', '')}"
        
        reading = measure.data.get("latestReading")
        self._state = reading.get("value") if isinstance(reading, dict) else None
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
        if not isinstance(scale, dict):
            return

        high = scale.get("typicalRangeHigh")
        low = scale.get("typicalRangeLow")
        
        current_level = None
        for m in self._station.measures:
            if m.data.get("parameter") == "level":
                reading = m.data.get("latestReading")
                if isinstance(reading, dict):
                    current_level = reading.get("value")
                break

        if current_level is None or high is None or low is None:
            self._state = "Unknown"
        elif current_level > high:
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
            "highest_recent": scale.get("highestRecent", {}).get("value") if isinstance(scale.get("highestRecent"), dict) else None
        }