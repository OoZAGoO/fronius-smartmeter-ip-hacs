"""The Fronius Smartmeter IP integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_URL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .auth import FroniusJWTAuth
from .const import (
    DOMAIN,
    API_PATH_MEASUREMENTS, API_PATH_CONFIG, API_QUERY_PARAMS,
    DEFAULT_MEASUREMENTS_INTERVAL_SECONDS, DEFAULT_CONFIG_INTERVAL_SECONDS
)
from .sensor import FroniusSmartmeterDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fronius Smartmeter IP from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    config = entry.data
    base_url = config[CONF_URL].rstrip('/')
    password = config.get(CONF_PASSWORD)

    # JWT Auth Handler erstellen
    jwt_auth = None
    if password:
        jwt_auth = FroniusJWTAuth(base_url, password)

    # Erstelle und speichere die Koordinatoren
    measurements_coordinator = FroniusSmartmeterDataCoordinator(
        hass, "Fronius Measurements", f"{base_url}{API_PATH_MEASUREMENTS}",
        jwt_auth, API_QUERY_PARAMS, DEFAULT_MEASUREMENTS_INTERVAL_SECONDS, is_measurements=True
    )
    config_coordinator = FroniusSmartmeterDataCoordinator(
        hass, "Fronius Configuration", f"{base_url}{API_PATH_CONFIG}",
        jwt_auth, API_QUERY_PARAMS, DEFAULT_CONFIG_INTERVAL_SECONDS
    )

    # Lade initiale Daten für die Koordinatoren
    await measurements_coordinator.async_config_entry_first_refresh()
    await config_coordinator.async_config_entry_first_refresh()

    # Speichere die Koordinatoren in hass.data, damit Plattformen darauf zugreifen können
    hass.data[DOMAIN][entry.entry_id]['measurements_coordinator'] = measurements_coordinator
    hass.data[DOMAIN][entry.entry_id]['config_coordinator'] = config_coordinator

    # Lade die Plattformen (sensor, binary_sensor)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
