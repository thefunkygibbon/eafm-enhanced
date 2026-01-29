import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from . import aioeafm_local as aioeafm

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)
DOMAIN = "eafm_enhanced"

async def async_setup_entry(hass, entry, async_add_entities):
    session = async_get_clientsession(hass)
    station_ref = entry.data["station"]
    station = await aioeafm.get_station(session, station_ref)

    if not station or not station.measures:
        return

    entities = []
    for measure in station.measures:
        entities.append(EafmSensor(session, station_ref, measure, station))
    
    if station.stage_scale:
        entities.append(EafmStatusSensor(session, station_ref, station))

    async_add_entities(entities, True)

class EafmSensor(SensorEntity):
    def __init__(self, session, station_ref, measure, initial_station):
        self._session = session
        self._station_ref = station_ref
        self._measure_id = measure.data.get("@id")
        self._station = initial_station
        
        # Identity
        measure_label = measure.data.get('qualifier', 'Level')
        self._attr_name = f"{initial_station.label} {measure_label}"
        self._attr_unique_id = f"{station_ref}_{self._measure_id}"
        self._attr_icon = "mdi:waves"
        self._state = None
        self._previous_state = None

    @property
    def device_info(self):
        """Group all sensors into a single Device."""
        name_id = self._station.rloi_id or self._station_ref
        return {
            "identifiers": {(DOMAIN, self._station_ref)},
            "name": f"{self._station.label} ({name_id})",
            "manufacturer": "Environment Agency",
            "model": self._station.catchment_name,
        }

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {
            "river": self._station.data.get("riverName"),
            "catchment": self._station.catchment_name,
            "station_url": f"https://check-for-flooding.service.gov.uk/station/{self._station_ref}",
            "highest_recent": self._station.highest_recent,
            "highest_recent_date": self._station.highest_recent_date
        }

    async def async_update(self):
        try:
            self._station = await aioeafm.get_station(self._session, self._station_ref)
            for m in self._station.measures:
                if m.data.get("@id") == self._measure_id:
                    reading = m.data.get("latestReading")
                    if isinstance(reading, dict):
                        new_val = reading.get("value")
                        # Trend Logic
                        if self._state is not None:
                            if new_val > self._state:
                                self._attr_icon = "mdi:trending-up"
                            elif new_val < self._state:
                                self._attr_icon = "mdi:trending-down"
                            else:
                                self._attr_icon = "mdi:waves"
                        self._state = new_val
                    break
        except Exception as err:
            _LOGGER.error("Error updating %s: %s", self.entity_id, err)

class EafmStatusSensor(SensorEntity):
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

    @property
    def extra_state_attributes(self):
        scale = self._station.stage_scale
        return {
            "typical_range_high": scale.get("typicalRangeHigh"),
            "typical_range_low": scale.get("typicalRangeLow"),
        }

    async def async_update(self):
        try:
            self._station = await aioeafm.get_station(self._session, self._station_ref)
            scale = self._station.stage_scale
            high = scale.get("typicalRangeHigh")
            low = scale.get("typicalRangeLow")

            current_level = None
            for m in self._station.measures:
                if m.data.get("parameter") == "level":
                    reading = m.data.get("latestReading")
                    if isinstance(reading, dict):
                        current_level = reading.get("value")
                    break

            if current_level is None or high is None:
                self._state = "Unknown"
            elif current_level > high:
                self._state = "High"
            elif low and current_level < low:
                self._state = "Low"
            else:
                self._state = "Normal"
        except Exception as err:
            _LOGGER.error("Error: %s", err)