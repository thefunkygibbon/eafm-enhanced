import aiohttp
from typing import List, Dict, Any

class Base:
    def __init__(self, data):
        # If we accidentally get a list, try to grab the first item, otherwise use empty dict
        if isinstance(data, list) and len(data) > 0:
            self.data = data[0] if isinstance(data[0], dict) else {}
        else:
            self.data = data if isinstance(data, dict) else {}

    def __getattr__(self, name):
        return self.data.get(name)

class Measure(Base):
    @property
    def label(self):
        # Tries different fields to find a good name for the measure
        return self.data.get("qualifier") or self.data.get("parameterName") or "Measure"

class Station(Base):
    """A monitoring station."""

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
        # This gets the scale dictionary which contains the high/low thresholds
        scale = self.data.get("stageScale")
        return scale if isinstance(scale, dict) else {}

    @property
    def measures(self):
        m_data = self.data.get("measures", [])
        if isinstance(m_data, list):
            return [Measure(m) for m in m_data]
        if isinstance(m_data, dict):
            return [Measure(m_data)]
        return []
    
async def get_stations(session: aiohttp.ClientSession, **kwargs) -> List[Station]:
    """Get all stations (for the config flow list)."""
    # FIX: Default to 'Active' stations only so we don't see closed ones
    kwargs.setdefault("status", "Active")
    
    url = "https://environment.data.gov.uk/flood-monitoring/id/stations"
    async with session.get(url, params=kwargs) as response:
        res_json = await response.json()
        items = res_json.get("items", [])
        return [Station(item) for item in items]

async def get_station(session: aiohttp.ClientSession, station_reference: str) -> Station:
    """Get a single station (for the sensor setup)."""
    url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{station_reference}"
    async with session.get(url) as response:
        res_json = await response.json()
        
        # CRITICAL FIX: The API returns {"items": [ {station_data} ]}
        # We must unpack that list to get the actual dictionary.
        items = res_json.get("items")
        
        if isinstance(items, list) and len(items) > 0:
            return Station(items[0])
            
        return Station(items)
