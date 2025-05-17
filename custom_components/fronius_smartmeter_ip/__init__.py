"""The Fronius Smartmeter IP integration."""
import logging
from typing import Tuple # Für Typ-Annotation

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_URL, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
# httpx.HTTPBasicAuth wird hier nicht mehr direkt benötigt, da das auth-Tupel verwendet wird

from .const import (
    DOMAIN,
    API_PATH_MEASUREMENTS, API_PATH_CONFIG, API_QUERY_PARAMS,
    DEFAULT_MEASUREMENTS_INTERVAL_SECONDS, DEFAULT_CONFIG_INTERVAL_SECONDS
)
# Die FroniusSmartmeterDataCoordinator Klasse wird aus sensor.py importiert
from .sensor import FroniusSmartmeterDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fronius Smartmeter IP from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Initialisiere das Dictionary für diese entry_id, falls es noch nicht existiert
    hass.data[DOMAIN][entry.entry_id] = {}

    config = entry.data
    base_url = config[CONF_URL].rstrip('/')
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    auth_tuple: Tuple[str, str] | None = (username, password) if username and password else None

    # Erstelle und speichere die Koordinatoren
    measurements_coordinator = FroniusSmartmeterDataCoordinator(
        hass, "Fronius Measurements", f"{base_url}{API_PATH_MEASUREMENTS}",
        auth_tuple, API_QUERY_PARAMS, DEFAULT_MEASUREMENTS_INTERVAL_SECONDS, is_measurements=True
    )
    config_coordinator = FroniusSmartmeterDataCoordinator(
        hass, "Fronius Configuration", f"{base_url}{API_PATH_CONFIG}",
        auth_tuple, API_QUERY_PARAMS, DEFAULT_CONFIG_INTERVAL_SECONDS
    )

    # Lade initiale Daten für die Koordinatoren
    await measurements_coordinator.async_config_entry_first_refresh()
    await config_coordinator.async_config_entry_first_refresh()

    # Speichere die Koordinatoren in hass.data, damit Plattformen darauf zugreifen können
    hass.data[DOMAIN][entry.entry_id]['measurements_coordinator'] = measurements_coordinator
    hass.data[DOMAIN][entry.entry_id]['config_coordinator'] = config_coordinator
    # Die Konfiguration selbst ist über entry.data zugänglich

    # Lade die Plattformen (sensor, binary_sensor)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Entferne die Daten dieser entry_id aus hass.data
        hass.data[DOMAIN].pop(entry.entry_id, None) # Füge , None hinzu, um KeyError zu vermeiden, falls nicht vorhanden
    return unload_ok