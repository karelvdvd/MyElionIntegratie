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
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
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
    data_key: str | None = None
    scale: float = 1.0


SENSOR_DESCRIPTIONS: tuple[ElionSensorEntityDescription, ...] = (
    # Live
    ElionSensorEntityDescription(
        key="live_battery_soc",
        value_key="soc",
        coordinator_key="live",
        name="Live Battery SoC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="live_battery_power",
        value_key="flex",
        coordinator_key="live",
        name="Live Battery Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="live_grid_power",
        value_key="grid",
        coordinator_key="live",
        name="Live Grid Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="live_consumption_power",
        value_key="consumption",
        coordinator_key="live",
        name="Live Consumption Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="live_production_power",
        value_key="production",
        coordinator_key="live",
        name="Live Production Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),

    # Latest metering
    ElionSensorEntityDescription(
        key="latest_flex_charge",
        value_key="flexCharge",
        coordinator_key="metering",
        data_key="latest",
        name="Latest Flex Charge",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
    ),
    ElionSensorEntityDescription(
        key="latest_flex_discharge",
        value_key="flexDischarge",
        coordinator_key="metering",
        data_key="latest",
        name="Latest Flex Discharge",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
    ),
    ElionSensorEntityDescription(
        key="latest_grid_offtake",
        value_key="gridOfftake",
        coordinator_key="metering",
        data_key="latest",
        name="Latest Grid Offtake",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
    ),
    ElionSensorEntityDescription(
        key="latest_grid_inject",
        value_key="gridInject",
        coordinator_key="metering",
        data_key="latest",
        name="Latest Grid Inject",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
    ),

    # Today totals
    ElionSensorEntityDescription(
        key="today_consumption",
        value_key="consumption_today",
        coordinator_key="metering",
        data_key="totals",
        name="Today Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="today_production",
        value_key="production_today",
        coordinator_key="metering",
        data_key="totals",
        name="Today Production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="today_battery_charge",
        value_key="flex_charge_today",
        coordinator_key="metering",
        data_key="totals",
        name="Today Battery Charge",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="today_battery_discharge",
        value_key="flex_discharge_today",
        coordinator_key="metering",
        data_key="totals",
        name="Today Battery Discharge",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="today_grid_offtake",
        value_key="grid_offtake_today",
        coordinator_key="metering",
        data_key="totals",
        name="Today Grid Offtake",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="today_grid_inject",
        value_key="grid_inject_today_negative",
        coordinator_key="metering",
        data_key="totals",
        name="Today Grid Inject",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),

    # Financial
    ElionSensorEntityDescription(
        key="financial_epex_price",
        value_key="epex",
        coordinator_key="metering",
        data_key="latest",
        name="Financial EPEX Price",
        native_unit_of_measurement="€/MWh",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="financial_imbalance_price",
        value_key="imbPrice",
        coordinator_key="metering",
        data_key="latest",
        name="Financial Imbalance Price",
        native_unit_of_measurement="€/MWh",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ElionSensorEntityDescription(
        key="financial_cost_no_elion",
        value_key="costNoElion",
        coordinator_key="metering",
        data_key="latest",
        name="Financial Cost No Elion",
        native_unit_of_measurement="€",
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="financial_cost_elion",
        value_key="costElion",
        coordinator_key="metering",
        data_key="latest",
        name="Financial Cost Elion",
        native_unit_of_measurement="€",
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="financial_profit_elion",
        value_key="profitElion",
        coordinator_key="metering",
        data_key="latest",
        name="Financial Profit Elion",
        native_unit_of_measurement="€",
        state_class=SensorStateClass.TOTAL,
    ),
    ElionSensorEntityDescription(
        key="today_curtailed_production",
        value_key="curtailed_production_today",
        coordinator_key="metering",
        data_key="totals",
        name="Today Curtailed Production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
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

    async_add_entities(
        ElionSensor(
            coordinator=coordinators[description.coordinator_key],
            entry=entry,
            description=description,
        )
        for description in SENSOR_DESCRIPTIONS
    )


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
        data = self.coordinator.data

        if self.entity_description.data_key:
            data = data.get(self.entity_description.data_key, {})

        if not isinstance(data, dict):
            return None

        value = data.get(self.entity_description.value_key)

        if value is None:
            return None

        try:
            return round(float(value) * self.entity_description.scale, 3)
        except (TypeError, ValueError):
            return value