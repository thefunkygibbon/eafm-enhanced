"""Async Python client for EA Flood Monitoring API."""
import aiohttp

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
    def measures(self):
        m_list = self.data.get("measures", [])
        if isinstance(m_list, list):
            return [Measure(m) for m in m_list]
        return []

async def get_stations(session: aiohttp.ClientSession, **kwargs):
    """Get stations. Defaults to status=Active."""
    kwargs.setdefault("status", "Active")
    url = "https://environment.data.gov.uk/flood-monitoring/id/stations"
    async with session.get(url, params=kwargs) as response:
        json_data = await response.json()
        return [Station(item) for item in json_data.get("items", [])]

async def get_station(session: aiohttp.ClientSession, station_id: str):
    """Get a single station by ID."""
    url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{station_id}"
    async with session.get(url) as response:
        json_data = await response.json()
        items = json_data.get("items")
        
        # Robust handling: If it's a list, grab the first. If it's a dict, use it.
        if isinstance(items, list) and len(items) > 0:
            return Station(items[0])
        elif isinstance(items, dict):
            return Station(items)
            
        return None