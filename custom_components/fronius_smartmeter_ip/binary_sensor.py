"""Binary sensor platform for Fronius Smartmeter IP."""
import logging
from typing import Tuple # Sicherstellen, dass Tuple für Type Hints importiert wird, falls nicht schon globaler

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass, # Wird hier nicht direkt verwendet, aber guter Import für die Plattform
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL # Für DeviceInfo benötigt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

# Importiere die Basis-Entitätsklasse und den Datenkoordinator.
# Diese werden jetzt in __init__.py erstellt und in hass.data gespeichert.
# Die Klassendefinitionen können in sensor.py bleiben, da sie dort auch für Sensoren verwendet werden.
from .sensor import FroniusSmartmeterDataCoordinator, FroniusSmartmeterEntity
from .const import (
    DOMAIN,
    SENSOR_NAME_PREFIX,
    STATUS_BIT_DEFINITIONS,
    KEY_STATUS_RAW,
)

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = tuple(
    BinarySensorEntityDescription(
        key=f"status_bit_{bit}",
        name=f"{desc}",
        device_class=None, # Korrigiert von BinarySensorDeviceClass.OK
        # entity_category=EntityCategory.DIAGNOSTIC, # Optional
    ) for bit, desc in STATUS_BIT_DEFINITIONS.items()
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fronius Smartmeter IP binary sensors from a config entry."""
    # Hole den Measurements-Koordinator aus hass.data, wo er von __init__.py gespeichert wurde
    domain_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    measurements_coordinator = domain_data.get('measurements_coordinator')

    if not measurements_coordinator:
        _LOGGER.error("Measurements coordinator not found for binary sensor setup. Ensure it's set up in __init__.py.")
        return

    # Erstelle DeviceInfo (konsistent mit sensor.py)
    # CONF_URL sollte in entry.data verfügbar sein
    base_url = entry.data[CONF_URL].rstrip('/')
    device_name_suffix = base_url.split('//')[-1].split(':')[0]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"{SENSOR_NAME_PREFIX} ({device_name_suffix})",
        manufacturer="Fronius (Custom)",
        model="Smartmeter IP API",
        configuration_url=base_url,
    )

    entities_to_add = []
    for description in BINARY_SENSOR_DESCRIPTIONS:
        # Extrahiere den Bit-Index aus dem Schlüssel der Beschreibung
        try:
            bit_index = int(description.key.split('_')[-1])
        except (ValueError, IndexError) as e:
            _LOGGER.error("Could not parse bit_index from binary_sensor key %s: %s", description.key, e)
            continue

        entities_to_add.append(
            FroniusSmartmeterStatusBinarySensor(
                measurements_coordinator, description, device_info, entry.entry_id, bit_index
            )
        )
    async_add_entities(entities_to_add)


class FroniusSmartmeterStatusBinarySensor(FroniusSmartmeterEntity, BinarySensorEntity):
    """Representation of a Fronius Smartmeter IP Status Binary Sensor."""
    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: FroniusSmartmeterDataCoordinator, # Typ kommt von .sensor
        description: BinarySensorEntityDescription,
        device_info: DeviceInfo,
        entry_id: str,
        status_bit_index: int,
    ):
        super().__init__(coordinator, description, device_info, entry_id) # Ruft Basisklasse auf
        self._status_bit_index = status_bit_index
        # Der Name wird automatisch durch _attr_has_entity_name = True in der Basisklasse und die description.name gesetzt

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on (status bit is set)."""
        if self.coordinator.data and isinstance(self.coordinator.data, dict):
            status_value = self.coordinator.data.get(KEY_STATUS_RAW) # KEY_STATUS_RAW aus .const
            if isinstance(status_value, int):
                # Bit ist gesetzt bedeutet "OK" (is_on = True)
                return bool(status_value & (1 << self._status_bit_index))
        return None