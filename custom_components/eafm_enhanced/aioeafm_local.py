"""Async Python client for EA Flood Monitoring API."""
import logging
from urllib.parse import quote

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://environment.data.gov.uk/flood-monitoring/id/stations"

# Station references the API can't look up directly, mapped to the station's
# notation (the ID in its URL). Filled in on first use.
_NOTATIONS: dict[str, str] = {}

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
    def notation(self):
        """The station's unique ID, as used in its API URL.

        Usually the same as stationReference, but not always: for example
        "055807_TG 320" is "055807_TG_320", and "E2900" is used by two
        stations whose notations are "E2900-anglian" and "E2900-southern".
        """
        return self.data.get("notation") or self.station_reference

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

async def _fetch_station(session: aiohttp.ClientSession, station_id: str):
    """Fetch one station by the ID in its URL. Returns None if it isn't found."""
    url = f"{BASE_URL}/{quote(station_id, safe='')}"
    async with session.get(url) as response:
        if response.status != 200:
            _LOGGER.debug("API Error %s for station %s", response.status, station_id)
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


async def _find_notation(session: aiohttp.ClientSession, station_reference: str):
    """Find the notation for a station reference the API can't look up directly."""
    async with session.get(BASE_URL, params={"stationReference": station_reference}) as response:
        if response.status != 200:
            return None
        items = (await response.json()).get("items", [])
    notations = [i.get("notation") for i in items if i.get("notation")]
    if len(notations) != 1:
        if len(notations) > 1:
            _LOGGER.error(
                "Station reference %s matches more than one station (%s); "
                "remove and re-add the station to pick the right one",
                station_reference, ", ".join(notations),
            )
        return None
    return notations[0]


async def get_station(session: aiohttp.ClientSession, station_id: str):
    """Get a single station by ID with robust error handling.

    New entries store the station's notation, which can always be looked up
    directly. Older entries store its stationReference, which can't when it
    differs from the notation (e.g. "055807_TG 320"), so those are resolved
    to the notation once and remembered.
    """
    try:
        station_id = _NOTATIONS.get(station_id, station_id)
        station = await _fetch_station(session, station_id)
        if station is None:
            notation = await _find_notation(session, station_id)
            if notation and notation != station_id:
                _NOTATIONS[station_id] = notation
                station = await _fetch_station(session, notation)
        if station is None:
            _LOGGER.error(
                "Could not find station %s (the API may be unavailable; "
                "enable debug logging for details)", station_id,
            )
        return station

    except Exception as err:
        _LOGGER.error("Exception fetching station %s: %s", station_id, err)
        return None
