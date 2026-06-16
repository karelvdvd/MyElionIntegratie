"""Sensor platform for the Elion integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import ElionDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class ElionSensorEntityDescription(SensorEntityDescription):
    """Class describing Elion sensor entities."""

    value_key: str


SENSOR_DESCRIPTIONS: tuple[ElionSensorEntityDescription, ...] = (
    ElionSensorEntityDescription(
        key="battery_soc",
        value_key="soc",
        translation_key="battery_soc",
        name="Battery SoC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="battery_power",
        value_key="flex",
        translation_key="battery_power",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="grid_power",
        value_key="grid",
        translation_key="grid_power",
        name="Grid Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="consumption_power",
        value_key="consumption",
        translation_key="consumption_power",
        name="Consumption Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="production_power",
        value_key="production",
        translation_key="production_power",
        name="Production Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elion sensors from a config entry."""
    coordinator: ElionDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        ElionSensor(
            coordinator=coordinator,
            entry=entry,
            description=description,
        )
        for description in SENSOR_DESCRIPTIONS
    )


class ElionSensor(CoordinatorEntity[ElionDataUpdateCoordinator], SensorEntity):
    """Elion sensor."""

    entity_description: ElionSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ElionDataUpdateCoordinator,
        entry: ConfigEntry,
        description: ElionSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        site_id = entry.data.get("site_id", "unknown")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Elion site {site_id}",
            manufacturer=MANUFACTURER,
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        value = self.coordinator.data.get(self.entity_description.value_key)

        if value is None:
            return None

        try:
            return round(float(value), 3)
        except (TypeError, ValueError):
            return value