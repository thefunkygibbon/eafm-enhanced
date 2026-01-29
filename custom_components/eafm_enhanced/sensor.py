"""Support for EAFM-Enhanced sensors."""
import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import aioeafm_local as aioeafm

_LOGGER = logging.getLogger(__name__)

# This tells Home Assistant to run the update() loop every 15 minutes
SCAN_INTERVAL = timedelta(minutes=15)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensors via the config entry."""
    session = async_get_clientsession(hass)
    station_ref = entry.data["station"]

    # Initial fetch to build the sensors
    station = await aioeafm.get_station(session, station_ref)

    if not station or not station.measures:
        _LOGGER.error("Could not find measures for station %s", station_ref)
        return

    entities = []

    # 1. Create a sensor for every measure (Level, Flow, etc)
    for measure in station.measures:
        entities.append(EafmSensor(session, station_ref, measure, station))

    # 2. Create the Status Sensor (Normal/High/Low)
    if station.stage_scale:
        entities.append(EafmStatusSensor(session, station_ref, station))

    # The 'True' here triggers an immediate update
    async_add_entities(entities, True)


class EafmSensor(SensorEntity):
    """Standard sensor for River Level / Flow."""

    def __init__(self, session, station_ref, measure, initial_station):
        self._session = session
        self._station_ref = station_ref
        self._measure_id = measure.data.get("@id")
        
        # Identity
        self._attr_name = f"{initial_station.label} {measure.data.get('qualifier', 'Level')}"
        self._attr_unique_id = f"{station_ref}_{self._measure_id}"
        self._attr_native_unit_of_measurement = measure.data.get("unitName")
        self._attr_icon = "mdi:waves"
        
        # Store initial data
        self._station = initial_station
        self._state = None

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {
            "river": self._station.data.get("riverName"),
            "catchment": self._station.catchment_name,
            "station_url": f"https://check-for-flooding.service.gov.uk/station/{self._station_ref}"
        }

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            # Re-fetch the station data
            self._station = await aioeafm.get_station(self._session, self._station_ref)
            
            # Find the specific measure in the fresh data
            for m in self._station.measures:
                if m.data.get("@id") == self._measure_id:
                    reading = m.data.get("latestReading")
                    if isinstance(reading, dict):
                        self._state = reading.get("value")
                    break
        except Exception as err:
            _LOGGER.error("Error updating sensor %s: %s", self.entity_id, err)


class EafmStatusSensor(SensorEntity):
    """Sensor for 'Normal', 'High', 'Low' status."""

    def __init__(self, session, station_ref, initial_station):
        self._session = session
        self._station_ref = station_ref
        
        self._attr_name = f"{initial_station.label} River Status"
        self._attr_unique_id = f"{station_ref}_status"
        self._attr_icon = "mdi:alert-circle-check-outline"
        
        self._station = initial_station
        self._state = "Unknown"

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        """Fetch new data and calculate status."""
        try:
            # Re-fetch station data
            self._station = await aioeafm.get_station(self._session, self._station_ref)
            scale = self._station.stage_scale
            high = scale.get("typicalRangeHigh")
            low = scale.get("typicalRangeLow")

            # Find current level
            current_level = None
            for m in self._station.measures:
                if m.data.get("parameter") == "level":
                    reading = m.data.get("latestReading")
                    if isinstance(reading, dict):
                        current_level = reading.get("value")
                    break

            # Calculate Logic
            if current_level is None or high is None:
                self._state = "Unknown"
            elif current_level > high:
                self._state = "High"
            elif low and current_level < low:
                self._state = "Low"
            else:
                self._state = "Normal"

        except Exception as err:
            _LOGGER.error("Error updating status for %s: %s", self.entity_id, err)
    
    @property
    def extra_state_attributes(self):
        scale = self._station.stage_scale
        return {
            "typical_range_high": scale.get("typicalRangeHigh"),
            "typical_range_low": scale.get("typicalRangeLow")
        }