"""Async Python client for EA Flood Monitoring API."""
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)

class Measure:
    def __init__(self, data):
        self.data = data

class Station:
    def __init__(self, data):
        self.data = data

    @property
    def label(self):
        return self.data.get("label", "Unknown Station")

    @property
    def station_reference(self):
        return self.data.get("stationReference")

    @property
    def catchment_name(self):
        return self.data.get("catchmentName", "Unknown Catchment")

    @property
    def rloi_id(self):
        return self.data.get("RLOIid")

    @property
    def stage_scale(self):
        scale = self.data.get("stageScale")
        return scale if isinstance(scale, dict) else {}

    @property
    def highest_recent(self):
        """Get the highest recent reading value."""
        hr = self.stage_scale.get("highestRecent", {})
        return hr.get("value") if isinstance(hr, dict) else None

    @property
    def highest_recent_date(self):
        """Get the date/time of the highest recent reading."""
        hr = self.stage_scale.get("highestRecent", {})
        return hr.get("dateTime") if isinstance(hr, dict) else None

    @property
    def measures(self):
        m_list = self.data.get("measures", [])
        if isinstance(m_list, list):
            return [Measure(m) for m in m_list]
        # Handle the case where a single measure is a dict, not a list
        if isinstance(m_list, dict):
            return [Measure(m_list)]
        return []

async def get_stations(session: aiohttp.ClientSession, **kwargs):
    """Get stations. Defaults to status=Active."""
    kwargs.setdefault("status", "Active")
    url = "https://environment.data.gov.uk/flood-monitoring/id/stations"
    async with session.get(url, params=kwargs) as response:
        json_data = await response.json()
        return [Station(item) for item in json_data.get("items", [])]

async def get_station(session: aiohttp.ClientSession, station_id: str):
    """Get a single station by ID with robust error handling."""
    url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{station_id}"
    try:
        async with session.get(url) as response:
            if response.status != 200:
                _LOGGER.error("API Error %s for station %s", response.status, station_id)
                return None
            
            json_data = await response.json()
            
            # ATTEMPT 1: Standard 'items' list wrapper
            items = json_data.get("items")
            if isinstance(items, list) and len(items) > 0:
                return Station(items[0])
            
            # ATTEMPT 2: 'items' is just a dictionary (rare but possible)
            if isinstance(items, dict):
                return Station(items)
            
            # ATTEMPT 3: No 'items' wrapper, maybe the root is the station?
            # We check if it looks like a station (has 'stationReference')
            if "stationReference" in json_data:
                return Station(json_data)
                
            # If we get here, the data structure is unexpected. Log it.
            _LOGGER.error("Unexpected JSON structure for %s: %s", station_id, str(json_data)[:200])
            return None

    except Exception as err:
        _LOGGER.error("Exception fetching station %s: %s", station_id, err)
        return None