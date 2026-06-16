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
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, MANUFACTURER


@dataclass(frozen=True, kw_only=True)
class ElionSensorEntityDescription(SensorEntityDescription):
    """Class describing Elion sensor entities."""

    value_key: str
    coordinator_key: str


SENSOR_DESCRIPTIONS: tuple[ElionSensorEntityDescription, ...] = (
    ElionSensorEntityDescription(
        key="battery_soc",
        value_key="soc",
        coordinator_key="live",
        name="Battery SoC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="battery_power",
        value_key="flex",
        coordinator_key="live",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="grid_power",
        value_key="grid",
        coordinator_key="live",
        name="Grid Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="consumption_power",
        value_key="consumption",
        coordinator_key="live",
        name="Consumption Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="production_power",
        value_key="production",
        coordinator_key="live",
        name="Production Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="flex_charge",
        value_key="flexCharge",
        coordinator_key="metering",
        name="Flex Charge",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="flex_discharge",
        value_key="flexDischarge",
        coordinator_key="metering",
        name="Flex Discharge",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="grid_offtake",
        value_key="gridOfftake",
        coordinator_key="metering",
        name="Grid Offtake",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="grid_inject",
        value_key="gridInject",
        coordinator_key="metering",
        name="Grid Inject",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="epex_price",
        value_key="epex",
        coordinator_key="metering",
        name="EPEX Price",
        native_unit_of_measurement="€/MWh",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="imbalance_price",
        value_key="imbPrice",
        coordinator_key="metering",
        name="Imbalance Price",
        native_unit_of_measurement="€/MWh",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="cost_no_elion",
        value_key="costNoElion",
        coordinator_key="metering",
        name="Cost No Elion",
        native_unit_of_measurement="€",
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="cost_elion",
        value_key="costElion",
        coordinator_key="metering",
        name="Cost Elion",
        native_unit_of_measurement="€",
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="profit_elion",
        value_key="profitElion",
        coordinator_key="metering",
        name="Profit Elion",
        native_unit_of_measurement="€",
        state_class=SensorStateClass.TOTAL,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elion sensors from a config entry."""
    coordinators = hass.data[DOMAIN][entry.entry_id]

    entities = []

    for description in SENSOR_DESCRIPTIONS:
        entities.append(
            ElionSensor(
                coordinator=coordinators[description.coordinator_key],
                entry=entry,
                description=description,
            )
        )

    async_add_entities(entities)


class ElionSensor(CoordinatorEntity[DataUpdateCoordinator], SensorEntity):
    """Elion sensor."""

    entity_description: ElionSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
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