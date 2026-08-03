"""DataUpdateCoordinator for the Elion integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ElionApi, ElionApiError, ElionAuthError
from .const import DOMAIN, LIVE_SCAN_INTERVAL, METERING_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ElionLiveCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Elion live data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: ElionApi,
    ) -> None:
        """Initialize coordinator."""
        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_live",
            update_interval=timedelta(seconds=LIVE_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch live data from Elion."""
        try:
            return await self.api.async_get_live()
        except ElionAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ElionApiError as err:
            raise UpdateFailed(str(err)) from err


class ElionMeteringCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Elion metering data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: ElionApi,
    ) -> None:
        """Initialize coordinator."""
        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_metering",
            update_interval=timedelta(seconds=METERING_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch metering data from Elion."""
        try:
            return await self.api.async_get_metering()
        except ElionAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ElionApiError as err:
            raise UpdateFailed(str(err)) from err