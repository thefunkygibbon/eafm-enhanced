import aiohttp
from typing import List, Dict, Any
from enum import Enum

class Status(Enum):
    ACTIVE = "Active"
    CLOSED = "Closed"
    SUSPENDED = "Suspended"

class Base:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        # This is why 'label' and 'station_reference' seemed missing! 
        # The library uses this to automatically find keys in the JSON.
        return self.data.get(name)

class Measure(Base):
    @property
    def label(self):
        return self.data.get("label")

class Station(Base):
    """A monitoring station."""

    @property
    def label(self):
        return self.data.get("label")

    @property
    def station_reference(self):
        return self.data.get("stationReference")

    @property
    def catchment_name(self):
        """Return the catchment name of the station."""
        # This is your new custom addition!
        return self.data.get("catchmentName", "Unknown Catchment")

    @property
    def measures(self):
        return [Measure(m) for m in self.data.get("measures", [])]

async def get_stations(
    session: aiohttp.ClientSession,
    parameter_name: str = None,
    parameter: str = None,
    qualifier: str = None,
    label: str = None,
    town: str = None,
    river_name: str = None,
    station: str = None,
    status: Status = Status.ACTIVE,
) -> List[Station]:
    """Returns a list of stations."""
    params = {}
    if parameter_name: params["parameterName"] = parameter_name
    if parameter: params["parameter"] = parameter
    if qualifier: params["qualifier"] = qualifier
    if label: params["label"] = label
    if town: params["town"] = town
    if river_name: params["riverName"] = river_name
    if station: params["stationReference"] = station
    if status: params["status"] = status.value

    url = "https://environment.data.gov.uk/flood-monitoring/id/stations"
    async with session.get(url, params=params) as response:
        data = await response.json()
        return [Station(item) for item in data.get("items", [])]

async def get_station(session: aiohttp.ClientSession, station_reference: str) -> Station:
    """Returns a single station."""
    url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{station_reference}"
    async with session.get(url) as response:
        data = await response.json()
        return Station(data.get("items", {}))