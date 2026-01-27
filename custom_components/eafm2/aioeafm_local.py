import aiohttp
from typing import List

class Base:
    def __init__(self, data):
        self.data = data if isinstance(data, dict) else {}

    def __getattr__(self, name):
        return self.data.get(name)

class Measure(Base):
    @property
    def label(self):
        return self.data.get("qualifier") or self.data.get("parameterName") or "Measure"

class Station(Base):
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
    def measures(self):
        m_list = self.data.get("measures", [])
        if not isinstance(m_list, list):
            return []
        return [Measure(m) for m in m_list]

async def get_stations(session: aiohttp.ClientSession, **kwargs) -> List[Station]:
    url = "https://environment.data.gov.uk/flood-monitoring/id/stations"
    async with session.get(url, params=kwargs) as response:
        res_json = await response.json()
        items = res_json.get("items", [])
        return [Station(item) for item in items]

async def get_station(session: aiohttp.ClientSession, station_reference: str) -> Station:
    url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{station_reference}"
    async with session.get(url) as response:
        res_json = await response.json()
        # The API returns {"items": {...}} for a single station too
        item = res_json.get("items")
        if not item:
            item = res_json # Fallback
        return Station(item)