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
        # This grabs the "RLOIid" from the JSON you provided
        return self.data.get("RLOIid")

    @property
    def measures(self):
        m_list = self.data.get("measures", [])
        if isinstance(m_list, list):
            return [Measure(m) for m in m_list]
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
