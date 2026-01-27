"""The Environment Agency Flood Gauges Fixed integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# This tells Home Assistant to look for sensor.py
PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EAFM2 from a config entry."""
    _LOGGER.debug("Setting up eafm2 entry: %s", entry.title)
    
    # This line is the 'bridge' that tells HA to now go and run sensor.py
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry when the user deletes the integration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)