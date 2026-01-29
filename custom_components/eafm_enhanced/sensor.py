import logging
from datetime import timedelta
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength
from . import aioeafm_local as aioeafm

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)
DOMAIN = "eafm_enhanced"

async def async_setup_entry(hass, entry, async_add_entities):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    session = async_get_clientsession(hass)
    station_ref = entry.data["station"]
    station = await aioeafm.get_station(session, station_ref)

    if not station or not station.measures:
        _LOGGER.error("Could not find measures for station %s", station_ref)
        return

    entities = []
    for measure in station.measures:
        entities.append(EafmSensor(session, station_ref, measure, station))
    
    # Only add status sensor if stageScale exists
    if station.stage_scale:
        entities.append(EafmStatusSensor(session, station_ref, station))

    async_add_entities(entities, True)

class EafmSensor(SensorEntity):
    """Sensor for water levels (Stage/Tidal etc) with line-graph support."""
    
    def __init__(self, session, station_ref, measure, initial_station):
        self._session = session
        self._station_ref = station_ref
        self._measure_id = measure.data.get("@id")
        self._station = initial_station
        
        # 1. Identity & Naming
        m_label = measure.data.get('qualifier', 'Level')
        self._attr_name = f"{initial_station.label} {m_label}"
        self._attr_unique_id = f"{station_ref}_{self._measure_id}"
        self._attr_icon = "mdi:waves"
        self._state = None

        # 2. Graph Fix: Set Unit and State Class
        # Uses mASD/mAOD from API, falls back to 'm' if missing
        api_unit = measure.data.get("unitName")
        self._attr_native_unit_of_measurement = api_unit if api_unit else "m"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        """Groups all entities under a Device named 'Label (RLOIid)'."""
        name_id = self._station.rloi_id or self._station_ref
        return {
            "identifiers": {(DOMAIN, self._station_ref)},
            "name": f"{self._station.label} ({name_id})",
            "manufacturer": "Environment Agency",
            "model": self._station.catchment_name,
            "configuration_url": f"https://check-for-flooding.service.gov.uk/station/{self._station_ref}",
        }

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Historical data stored in attributes to avoid clutter."""
        return {
            "river": self._station.data.get("riverName"),
            "catchment": self._station.catchment_name,
            "highest_recent": self._station.highest_recent,
            "highest_recent_date": self._station.highest_recent_date,
            "typical_range_high": self._station.stage_scale.get("typicalRangeHigh"),
        }

    async def async_update(self):
        """Fetch latest data and update trend icons."""
        try:
            old_val = self._state
            self._station = await aioeafm.get_station(self._session, self._station_ref)
            
            for m in self._station.measures:
                if m.data.get("@id") == self._measure_id:
                    reading = m.data.get("latestReading")
                    if isinstance(reading, dict):
                        self._state = reading.get("value")
                        
                        # Apply Trend Arrows (↗️ ↘️ ➡️)
                        if old_val is not None and self._state is not None:
                            if self._state > old_val:
                                self._attr_icon = "mdi:trending-up"
                            elif self._state < old_val:
                                self._attr_icon = "mdi:trending-down"
                            else:
                                self._attr_icon = "mdi:waves"
                    break
        except Exception as err:
            _LOGGER.error("Error updating %s: %s", self._attr_name, err)

class EafmStatusSensor(SensorEntity):
    """The 'Normal/High/Low' status sensor."""
    
    def __init__(self, session, station_ref, initial_station):
        self._session = session
        self._station_ref = station_ref
        self._station = initial_station
        self._attr_name = f"{initial_station.label} River Status"
        self._attr_unique_id = f"{station_ref}_status"
        self._attr_icon = "mdi:alert-circle-check-outline"
        self._state = "Unknown"

    @property
    def device_info(self):
        name_id = self._station.rloi_id or self._station_ref
        return {
            "identifiers": {(DOMAIN, self._station_ref)},
            "name": f"{self._station.label} ({name_id})",
        }

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        try:
            self._station = await aioeafm.get_station(self._session, self._station_ref)
            scale = self._station.stage_scale
            high = scale.get("typicalRangeHigh")
            low = scale.get("typicalRangeLow")
            
            curr = None
            for m in self._station.measures:
                if m.data.get("parameter") == "level":
                    reading = m.data.get("latestReading")
                    if isinstance(reading, dict):
                        curr = reading.get("value")
                    break
            
            if curr is None or high is None:
                self._state = "Unknown"
            elif curr > high:
                self._state = "High"
                self._attr_icon = "mdi:alert-circle-outline"
            elif low and curr < low:
                self._state = "Low"
                self._attr_icon = "mdi:alert-circle-outline"
            else:
                self._state = "Normal"
                self._attr_icon = "mdi:check-circle-outline"
        except Exception as err:
            _LOGGER.error("Status update error: %s", err)
            self._state = "Error"