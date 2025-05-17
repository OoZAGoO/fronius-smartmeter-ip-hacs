"""Sensor platform for Fronius Smartmeter IP."""
import logging
import math
from datetime import timedelta
from typing import Any, cast, Tuple

import httpx

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
# BinarySensor-spezifische Imports werden hier nicht mehr benötigt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity, # Wird von FroniusSmartmeterEntity verwendet
    DataUpdateCoordinator, # Wird von FroniusSmartmeterDataCoordinator verwendet
    UpdateFailed,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    DEFAULT_MEASUREMENTS_INTERVAL_SECONDS,
    DEFAULT_CONFIG_INTERVAL_SECONDS,
    API_PATH_MEASUREMENTS,
    API_PATH_CONFIG,
    API_QUERY_PARAMS,
    SENSOR_NAME_PREFIX,

    # Einheiten (wie in const.py definiert, egal ob HA-Konstante oder String)
    UNIT_WATT,
    UNIT_VOLT_AMPERE,
    UNIT_VOLT_AMPERE_REACTIVE,
    UNIT_WATT_HOUR,
    UNIT_VOLT_AMPERE_REACTIVE_HOUR,
    UNIT_VOLT_AMPERE_HOUR,
    UNIT_VOLT,
    UNIT_AMPERE,
    UNIT_HERTZ,
    UNIT_CELSIUS,
    UNIT_DEGREE,
    UNIT_PERCENTAGE,
    UNIT_SECONDS,

    # Schlüssel für API-Daten und berechnete Werte
    KEY_FREQUENCY,
    KEY_TEMPERATURE,
    KEY_VOLTAGE_A,
    KEY_VOLTAGE_B,
    KEY_VOLTAGE_C,
    KEY_VOLTAGE_L1_L2,
    KEY_VOLTAGE_L2_L3,
    KEY_VOLTAGE_L3_L1,
    KEY_VOLTAGE_AVG_LN,
    KEY_VOLTAGE_AVG_LL,
    KEY_VOLTAGE_PHASE_ANGLE_A,
    KEY_VOLTAGE_PHASE_ANGLE_B,
    KEY_VOLTAGE_PHASE_ANGLE_C,
    KEY_CURRENT_A,
    KEY_CURRENT_B,
    KEY_CURRENT_C,
    KEY_CURRENT_N,
    KEY_CURRENT_N0,
    KEY_IMAX_CALCULATED,
    KEY_CURRENT_PHASE_ANGLE_A,
    KEY_CURRENT_PHASE_ANGLE_B,
    KEY_CURRENT_PHASE_ANGLE_C,
    KEY_ACTIVE_POWER_A,
    KEY_ACTIVE_POWER_B,
    KEY_ACTIVE_POWER_C,
    KEY_ACTIVE_POWER_TOTAL,
    KEY_REACTIVE_POWER_A,
    KEY_REACTIVE_POWER_B,
    KEY_REACTIVE_POWER_C,
    KEY_REACTIVE_POWER_TOTAL,
    KEY_APPARENT_POWER_A,
    KEY_APPARENT_POWER_B,
    KEY_APPARENT_POWER_C,
    KEY_APPARENT_POWER_TOTAL,
    KEY_POWER_FACTOR_A,
    KEY_POWER_FACTOR_B,
    KEY_POWER_FACTOR_C,
    KEY_POWER_FACTOR_TOTAL,
    KEY_THD_VOLTAGE_A,
    KEY_THD_VOLTAGE_B,
    KEY_THD_VOLTAGE_C,
    KEY_THD_CURRENT_A,
    KEY_THD_CURRENT_B,
    KEY_THD_CURRENT_C,
    KEY_OPERATING_TIME_MILLISECONDS, # Wird vom Coordinator intern verwendet
    KEY_OPERATING_TIME_SECONDS,    # Wird in SensorDescription verwendet
    KEY_SAMPLES,
    KEY_STATUS_RAW, # Wird auch von binary_sensor verwendet, aber gut, ihn hier zu haben für den Raw-Sensor

    # Grund- und Oberschwingungs-Wirkleistung
    KEY_ACTIVE_POWER_FUNDAMENTAL_A,
    KEY_ACTIVE_POWER_FUNDAMENTAL_B,
    KEY_ACTIVE_POWER_FUNDAMENTAL_C,
    KEY_ACTIVE_POWER_FUNDAMENTAL_TOTAL,
    KEY_ACTIVE_POWER_HARMONIC_A,
    KEY_ACTIVE_POWER_HARMONIC_B,
    KEY_ACTIVE_POWER_HARMONIC_C,
    KEY_ACTIVE_POWER_HARMONIC_TOTAL,

    # Energie Schlüssel (alle, die in SENSOR_DESCRIPTIONS und DETAILED_ENERGY_SENSOR_DESCRIPTIONS verwendet werden)
    KEY_ENERGY_EXPORT_ACTIVE_A,
    KEY_ENERGY_EXPORT_ACTIVE_B,
    KEY_ENERGY_EXPORT_ACTIVE_C,
    KEY_ENERGY_EXPORT_ACTIVE_TOTAL,
    KEY_ENERGY_EXPORT_REACTIVE_A,
    KEY_ENERGY_EXPORT_REACTIVE_B,
    KEY_ENERGY_EXPORT_REACTIVE_C,
    KEY_ENERGY_EXPORT_REACTIVE_TOTAL,
    KEY_ENERGY_IMPORT_ACTIVE_A,
    KEY_ENERGY_IMPORT_ACTIVE_B,
    KEY_ENERGY_IMPORT_ACTIVE_C,
    KEY_ENERGY_IMPORT_ACTIVE_TOTAL,
    KEY_ENERGY_IMPORT_REACTIVE_A,
    KEY_ENERGY_IMPORT_REACTIVE_B,
    KEY_ENERGY_IMPORT_REACTIVE_C,
    KEY_ENERGY_IMPORT_REACTIVE_TOTAL,
    KEY_ENERGY_APPARENT_A,
    KEY_ENERGY_APPARENT_B,
    KEY_ENERGY_APPARENT_C,
    KEY_ENERGY_APPARENT_TOTAL,
    KEY_ENERGY_EXPORT_APPARENT_A,
    KEY_ENERGY_EXPORT_APPARENT_B,
    KEY_ENERGY_EXPORT_APPARENT_C,
    KEY_ENERGY_EXPORT_APPARENT_TOTAL,
    KEY_ENERGY_IMPORT_APPARENT_A,
    KEY_ENERGY_IMPORT_APPARENT_B,
    KEY_ENERGY_IMPORT_APPARENT_C,
    KEY_ENERGY_IMPORT_APPARENT_TOTAL,
    KEY_ENERGY_EXPORT_ACTIVE_FUNDAMENTAL_A, # Phasenweise Fundamental/Harmonic Energie
    KEY_ENERGY_EXPORT_ACTIVE_FUNDAMENTAL_B,
    KEY_ENERGY_EXPORT_ACTIVE_FUNDAMENTAL_C,
    KEY_ENERGY_EXPORT_ACTIVE_FUNDAMENTAL_TOTAL,
    KEY_ENERGY_EXPORT_ACTIVE_HARMONIC_A,
    KEY_ENERGY_EXPORT_ACTIVE_HARMONIC_B,
    KEY_ENERGY_EXPORT_ACTIVE_HARMONIC_C,
    KEY_ENERGY_EXPORT_ACTIVE_HARMONIC_TOTAL,
    KEY_ENERGY_IMPORT_ACTIVE_FUNDAMENTAL_A,
    KEY_ENERGY_IMPORT_ACTIVE_FUNDAMENTAL_B,
    KEY_ENERGY_IMPORT_ACTIVE_FUNDAMENTAL_C,
    KEY_ENERGY_IMPORT_ACTIVE_FUNDAMENTAL_TOTAL,
    KEY_ENERGY_IMPORT_ACTIVE_HARMONIC_A,
    KEY_ENERGY_IMPORT_ACTIVE_HARMONIC_B,
    KEY_ENERGY_IMPORT_ACTIVE_HARMONIC_C,
    KEY_ENERGY_IMPORT_ACTIVE_HARMONIC_TOTAL,
    # Falls noch weitere spezifische Energie-Keys (ERT1 etc.) verwendet werden, hier auch importieren
)

_LOGGER = logging.getLogger(__name__)

# --- Sensor Entity Descriptions (aktualisiert mit Screenshot-Infos) ---
SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    # Spannungen L-N
    SensorEntityDescription(key=KEY_VOLTAGE_A, name="Voltage L1", native_unit_of_measurement=UNIT_VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_VOLTAGE_B, name="Voltage L2", native_unit_of_measurement=UNIT_VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_VOLTAGE_C, name="Voltage L3", native_unit_of_measurement=UNIT_VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    # Spannungen L-L
    SensorEntityDescription(key=KEY_VOLTAGE_L1_L2, name="Voltage L1-L2", native_unit_of_measurement=UNIT_VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_VOLTAGE_L2_L3, name="Voltage L2-L3", native_unit_of_measurement=UNIT_VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_VOLTAGE_L3_L1, name="Voltage L3-L1", native_unit_of_measurement=UNIT_VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_VOLTAGE_AVG_LN, name="Voltage Average L-N", native_unit_of_measurement=UNIT_VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_VOLTAGE_AVG_LL, name="Voltage Average L-L", native_unit_of_measurement=UNIT_VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),

    # Spannungs-Phasenwinkel
    SensorEntityDescription(key=KEY_VOLTAGE_PHASE_ANGLE_A, name="Voltage Phase Angle L1", native_unit_of_measurement=UNIT_DEGREE, icon="mdi:angle-acute", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    SensorEntityDescription(key=KEY_VOLTAGE_PHASE_ANGLE_B, name="Voltage Phase Angle L2", native_unit_of_measurement=UNIT_DEGREE, icon="mdi:angle-acute", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    SensorEntityDescription(key=KEY_VOLTAGE_PHASE_ANGLE_C, name="Voltage Phase Angle L3", native_unit_of_measurement=UNIT_DEGREE, icon="mdi:angle-acute", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),

    # Ströme
    SensorEntityDescription(key=KEY_CURRENT_A, name="Current L1", native_unit_of_measurement=UNIT_AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_CURRENT_B, name="Current L2", native_unit_of_measurement=UNIT_AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_CURRENT_C, name="Current L3", native_unit_of_measurement=UNIT_AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_CURRENT_N, name="Current N", native_unit_of_measurement=UNIT_AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_CURRENT_N0, name="Current N0", native_unit_of_measurement=UNIT_AMPERE, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_IMAX_CALCULATED, name="Calculated Max Phase Current", native_unit_of_measurement=UNIT_AMPERE, icon="mdi:current-ac", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),

    # Strom-Phasenwinkel
    SensorEntityDescription(key=KEY_CURRENT_PHASE_ANGLE_A, name="Current Phase Angle L1", native_unit_of_measurement=UNIT_DEGREE, icon="mdi:angle-right", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    SensorEntityDescription(key=KEY_CURRENT_PHASE_ANGLE_B, name="Current Phase Angle L2", native_unit_of_measurement=UNIT_DEGREE, icon="mdi:angle-right", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),
    SensorEntityDescription(key=KEY_CURRENT_PHASE_ANGLE_C, name="Current Phase Angle L3", native_unit_of_measurement=UNIT_DEGREE, icon="mdi:angle-right", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1),

    # Wirkleistung
    SensorEntityDescription(key=KEY_ACTIVE_POWER_A, name="Active Power L1", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_B, name="Active Power L2", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_C, name="Active Power L3", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_TOTAL, name="Active Power Total", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),

    # Blindleistung
    SensorEntityDescription(key=KEY_REACTIVE_POWER_A, name="Reactive Power L1", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE, device_class=SensorDeviceClass.REACTIVE_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_REACTIVE_POWER_B, name="Reactive Power L2", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE, device_class=SensorDeviceClass.REACTIVE_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_REACTIVE_POWER_C, name="Reactive Power L3", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE, device_class=SensorDeviceClass.REACTIVE_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_REACTIVE_POWER_TOTAL, name="Reactive Power Total", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE, device_class=SensorDeviceClass.REACTIVE_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),

    # Scheinleistung
    SensorEntityDescription(key=KEY_APPARENT_POWER_A, name="Apparent Power L1", native_unit_of_measurement=UNIT_VOLT_AMPERE, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_APPARENT_POWER_B, name="Apparent Power L2", native_unit_of_measurement=UNIT_VOLT_AMPERE, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_APPARENT_POWER_C, name="Apparent Power L3", native_unit_of_measurement=UNIT_VOLT_AMPERE, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_APPARENT_POWER_TOTAL, name="Apparent Power Total", native_unit_of_measurement=UNIT_VOLT_AMPERE, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),

    # Leistungsfaktor (als Verhältnis -1 bis 1)
    SensorEntityDescription(key=KEY_POWER_FACTOR_A, name="Power Factor L1", icon="mdi:cosine-wave", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3), # Keine Einheit, da Verhältnis
    SensorEntityDescription(key=KEY_POWER_FACTOR_B, name="Power Factor L2", icon="mdi:cosine-wave", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_POWER_FACTOR_C, name="Power Factor L3", icon="mdi:cosine-wave", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_POWER_FACTOR_TOTAL, name="Power Factor Total", icon="mdi:cosine-wave", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3),

    # THD Spannung & Strom
    SensorEntityDescription(key=KEY_THD_VOLTAGE_A, name="THD Voltage L1", native_unit_of_measurement=UNIT_PERCENTAGE, icon="mdi:chart-bell-curve", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    SensorEntityDescription(key=KEY_THD_VOLTAGE_B, name="THD Voltage L2", native_unit_of_measurement=UNIT_PERCENTAGE, icon="mdi:chart-bell-curve", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    SensorEntityDescription(key=KEY_THD_VOLTAGE_C, name="THD Voltage L3", native_unit_of_measurement=UNIT_PERCENTAGE, icon="mdi:chart-bell-curve", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    SensorEntityDescription(key=KEY_THD_CURRENT_A, name="THD Current L1", native_unit_of_measurement=UNIT_PERCENTAGE, icon="mdi:chart-waveform", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    SensorEntityDescription(key=KEY_THD_CURRENT_B, name="THD Current L2", native_unit_of_measurement=UNIT_PERCENTAGE, icon="mdi:chart-waveform", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    SensorEntityDescription(key=KEY_THD_CURRENT_C, name="THD Current L3", native_unit_of_measurement=UNIT_PERCENTAGE, icon="mdi:chart-waveform", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),

    # Allgemein
    SensorEntityDescription(key=KEY_FREQUENCY, name="Frequency", native_unit_of_measurement=UNIT_HERTZ, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    SensorEntityDescription(key=KEY_TEMPERATURE, name="Device Temperature", native_unit_of_measurement=UNIT_CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0),
    SensorEntityDescription(key=KEY_SAMPLES, name="Samples", icon="mdi:counter", state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_STATUS_RAW, name="Raw Status Code", icon="mdi:information-outline", entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_OPERATING_TIME_SECONDS, name="Operating Time", native_unit_of_measurement=UNIT_SECONDS, device_class=SensorDeviceClass.DURATION, icon="mdi:timer-sand", suggested_display_precision=0),

    # Fundamental- und Harmonische Wirkleistung (standardmäßig deaktiviert)
    SensorEntityDescription(key=KEY_ACTIVE_POWER_FUNDAMENTAL_A, name="Active Power Fundamental L1", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_FUNDAMENTAL_B, name="Active Power Fundamental L2", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_FUNDAMENTAL_C, name="Active Power Fundamental L3", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_FUNDAMENTAL_TOTAL, name="Active Power Fundamental Total", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_HARMONIC_A, name="Active Power Harmonic L1", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_HARMONIC_B, name="Active Power Harmonic L2", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_HARMONIC_C, name="Active Power Harmonic L3", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ACTIVE_POWER_HARMONIC_TOTAL, name="Active Power Harmonic Total", native_unit_of_measurement=UNIT_WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, entity_registry_enabled_default=False),

    # Energie Sensoren (Beispiele, erweitere nach Bedarf mit den Schlüsseln aus const.py)
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_TOTAL, name="Reverse Active Energy Total", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_TOTAL, name="Forward Active Energy Total", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_REACTIVE_TOTAL, name="Reverse Reactive Energy Total", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_REACTIVE_TOTAL, name="Forward Reactive Energy Total", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_APPARENT_TOTAL, name="Apparent Energy Total", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_APPARENT_TOTAL, name="Forward Apparent Energy Total", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_APPARENT_TOTAL, name="Reverse Apparent Energy Total", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3), # Kein device_class=ENERGY

    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_FUNDAMENTAL_TOTAL, name="Forward Active Fundamental Energy Total", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_HARMONIC_TOTAL, name="Forward Active Harmonic Energy Total", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_FUNDAMENTAL_TOTAL, name="Reverse Active Fundamental Energy Total", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3, entity_registry_enabled_default=False),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_HARMONIC_TOTAL, name="Reverse Active Harmonic Energy Total", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=3, entity_registry_enabled_default=False),
)

# Erstelle eine umfassendere Liste von Energie-Sensoren, die standardmäßig deaktiviert sind.
# Dies verhindert eine Überflutung der Entitätenliste, erlaubt aber dem Benutzer, sie bei Bedarf zu aktivieren.
# Alle Phasen-spezifischen Energiewerte werden hier hinzugefügt.
DETAILED_ENERGY_SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    # KORRIGIERTE Energie Sensoren (device_class nur für Wirkenergie)
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_A, name="Forward Active Energy L1", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_B, name="Forward Active Energy L2", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_C, name="Forward Active Energy L3", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_A, name="Reverse Active Energy L1", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_B, name="Reverse Active Energy L2", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_C, name="Reverse Active Energy L3", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_REACTIVE_A, name="Forward Reactive Energy L1", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_REACTIVE_B, name="Forward Reactive Energy L2", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_REACTIVE_C, name="Forward Reactive Energy L3", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_REACTIVE_A, name="Reverse Reactive Energy L1", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_REACTIVE_B, name="Reverse Reactive Energy L2", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_REACTIVE_C, name="Reverse Reactive Energy L3", native_unit_of_measurement=UNIT_VOLT_AMPERE_REACTIVE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_APPARENT_A, name="Apparent Energy L1", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_APPARENT_B, name="Apparent Energy L2", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_APPARENT_C, name="Apparent Energy L3", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_APPARENT_A, name="Forward Apparent Energy L1", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_APPARENT_B, name="Forward Apparent Energy L2", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_APPARENT_C, name="Forward Apparent Energy L3", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_APPARENT_A, name="Reverse Apparent Energy L1", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_APPARENT_B, name="Reverse Apparent Energy L2", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_APPARENT_C, name="Reverse Apparent Energy L3", native_unit_of_measurement=UNIT_VOLT_AMPERE_HOUR, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3), # Kein device_class=ENERGY
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_FUNDAMENTAL_A, name="Forward Active Fundamental Energy L1", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_FUNDAMENTAL_B, name="Forward Active Fundamental Energy L2", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_FUNDAMENTAL_C, name="Forward Active Fundamental Energy L3", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_HARMONIC_A, name="Forward Active Harmonic Energy L1", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_HARMONIC_B, name="Forward Active Harmonic Energy L2", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_EXPORT_ACTIVE_HARMONIC_C, name="Forward Active Harmonic Energy L3", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_FUNDAMENTAL_A, name="Reverse Active Fundamental Energy L1", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_FUNDAMENTAL_B, name="Reverse Active Fundamental Energy L2", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_FUNDAMENTAL_C, name="Reverse Active Fundamental Energy L3", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_HARMONIC_A, name="Reverse Active Harmonic Energy L1", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_HARMONIC_B, name="Reverse Active Harmonic Energy L2", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
    SensorEntityDescription(key=KEY_ENERGY_IMPORT_ACTIVE_HARMONIC_C, name="Reverse Active Harmonic Energy L3", native_unit_of_measurement=UNIT_WATT_HOUR, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, entity_registry_enabled_default=False, suggested_display_precision=3),
)
# --- Ende der Sensorbeschreibungen ---

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fronius Smartmeter IP sensors from a config entry."""
    config = entry.data
    base_url = config[CONF_URL].rstrip('/')
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    auth_tuple: Tuple[str, str] | None = (username, password) if username and password else None

    device_name_suffix = base_url.split('//')[-1].split(':')[0]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"{SENSOR_NAME_PREFIX} ({device_name_suffix})",
        manufacturer="Fronius (Custom)",
        model="Smartmeter IP API",
        configuration_url=base_url,
    )

    measurements_coordinator = FroniusSmartmeterDataCoordinator(
        hass, "Fronius Measurements", f"{base_url}{API_PATH_MEASUREMENTS}",
        auth_tuple, API_QUERY_PARAMS, DEFAULT_MEASUREMENTS_INTERVAL_SECONDS, is_measurements=True
    )
    config_coordinator = FroniusSmartmeterDataCoordinator(
        hass, "Fronius Configuration", f"{base_url}{API_PATH_CONFIG}",
        auth_tuple, API_QUERY_PARAMS, DEFAULT_CONFIG_INTERVAL_SECONDS
    )

    await measurements_coordinator.async_config_entry_first_refresh()
    await config_coordinator.async_config_entry_first_refresh()

    entities_to_add: list[SensorEntity] = []

    # Füge zuerst die primären Sensoren hinzu
    for description in SENSOR_DESCRIPTIONS:
        entities_to_add.append(FroniusSmartmeterSensor(measurements_coordinator, description, device_info, entry.entry_id))
    
    # Füge dann die detaillierten Energie-Sensoren hinzu (meist standardmäßig deaktiviert)
    for description in DETAILED_ENERGY_SENSOR_DESCRIPTIONS:
        entities_to_add.append(FroniusSmartmeterSensor(measurements_coordinator, description, device_info, entry.entry_id))

    cfg_sensor_desc = SensorEntityDescription(key="configuration_data", name="Configuration Data", icon="mdi:cog-outline")
    entities_to_add.append(FroniusSmartmeterConfigSensor(config_coordinator, cfg_sensor_desc, device_info, entry.entry_id))

    async_add_entities(entities_to_add)


class FroniusSmartmeterDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self, hass: HomeAssistant, name: str, url: str,
        auth: Tuple[str, str] | None,
        params: dict | None, interval_seconds: int, is_measurements: bool = False
    ):
        self.api_url = url
        self.auth_tuple = auth
        self.params = params
        self.is_measurements = is_measurements
        self._client = httpx.AsyncClient(timeout=10)
        super().__init__(hass, _LOGGER, name=name, update_interval=timedelta(seconds=interval_seconds))

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            response = await self._client.get(self.api_url, auth=self.auth_tuple, params=self.params)
            response.raise_for_status()
            data = cast(dict[str, Any], response.json())
            _LOGGER.debug("Data from %s: %s", self.api_url, str(data)[:800] + "..." if len(str(data)) > 800 else data) # Log more data

            if self.is_measurements and isinstance(data, dict):
                ia = float(data.get(KEY_CURRENT_A, 0) or 0)
                ib = float(data.get(KEY_CURRENT_B, 0) or 0)
                ic = float(data.get(KEY_CURRENT_C, 0) or 0)
                data[KEY_IMAX_CALCULATED] = math.ceil(max(ia, ib, ic, 0.1))
                time_ms = data.get(KEY_OPERATING_TIME_MILLISECONDS) # Verwende korrigierten Schlüssel
                if isinstance(time_ms, (int, float)):
                    data[KEY_OPERATING_TIME_SECONDS] = time_ms / 1000.0 # Verwende korrigierten Schlüssel
                else:
                    data[KEY_OPERATING_TIME_SECONDS] = None
            return data
        except httpx.HTTPStatusError as err:
            _LOGGER.error("HTTP error for %s (%s): %s", self.name, self.api_url, err) # Log coordinator name
            raise UpdateFailed(f"Error communicating with API ({self.name} - {self.api_url}): {err}") from err
        except (httpx.RequestError, httpx.TimeoutException) as err:
            _LOGGER.error("Request error for %s (%s): %s", self.name, self.api_url, err)
            raise UpdateFailed(f"Error communicating with API ({self.name} - {self.api_url}): {err}") from err
        except (ValueError, TypeError) as err:
            _LOGGER.error("JSON parsing error for %s (%s): %s", self.name, self.api_url, err)
            raise UpdateFailed(f"Invalid JSON response from API ({self.name} - {self.api_url}): {err}") from err


class FroniusSmartmeterEntity(CoordinatorEntity[FroniusSmartmeterDataCoordinator]):
    _attr_has_entity_name = True
    def __init__(
        self,
        coordinator: FroniusSmartmeterDataCoordinator,
        description: SensorEntityDescription,
        device_info: DeviceInfo,
        entry_id: str,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key.lower()}" # Lowercase key for ID


class FroniusSmartmeterSensor(FroniusSmartmeterEntity, SensorEntity):
    entity_description: SensorEntityDescription

    @property
    def native_value(self) -> Any:
        if self.coordinator.data and isinstance(self.coordinator.data, dict):
            value = self.coordinator.data.get(self.entity_description.key)
            if value is None: return None

            # Spezifische Formatierung/Rundung für bestimmte Typen
            # Die suggested_display_precision wird von HA für die Anzeige verwendet.
            # Hier geht es um die Konvertierung des Rohwerts.
            try:
                if isinstance(value, (int, float)):
                    # Für Leistungsfaktoren, die als Verhältnis bleiben
                    if self.entity_description.key in [KEY_POWER_FACTOR_A, KEY_POWER_FACTOR_B, KEY_POWER_FACTOR_C, KEY_POWER_FACTOR_TOTAL]:
                        return round(float(value), 3) # Behalte als Verhältnis bei

                    # Für die meisten anderen numerischen Werte, die direkt verwendet werden können
                    # Die Rundung für die Anzeige erfolgt durch suggested_display_precision.
                    return float(value)
                
                # Wenn der Wert ein String ist, aber numerisch sein sollte (unwahrscheinlich bei diesem API-JSON)
                if isinstance(value, str):
                    try:
                        return float(value)
                    except ValueError:
                        pass # Fällt durch zum return value
            except (ValueError, TypeError) as e:
                _LOGGER.warning("Could not convert value '%s' for sensor %s to float: %s", value, self.entity_id, e)
                return None # Oder value, wenn String okay ist

            return value # Gib den Wert zurück, wenn er nicht numerisch ist oder keine spezielle Behandlung benötigt
        return None


class FroniusSmartmeterConfigSensor(FroniusSmartmeterEntity, SensorEntity):
    entity_description: SensorEntityDescription
    def __init__(
        self,
        coordinator: FroniusSmartmeterDataCoordinator,
        description: SensorEntityDescription,
        device_info: DeviceInfo,
        entry_id: str,
    ):
        super().__init__(coordinator, description, device_info, entry_id)
        self._attr_extra_state_attributes: dict[str, Any] = {}

    @property
    def native_value(self) -> str | None:
        if self.coordinator.last_update_success :
            return self.coordinator.last_update_success
        return "Unavailable" # Oder None

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.coordinator.data and isinstance(self.coordinator.data, dict):
            self._attr_extra_state_attributes = {
                k: v for k, v in self.coordinator.data.items()
                if isinstance(v, (str, int, float, bool)) or v is None
            }
        else:
            self._attr_extra_state_attributes = {}
        super()._handle_coordinator_update()