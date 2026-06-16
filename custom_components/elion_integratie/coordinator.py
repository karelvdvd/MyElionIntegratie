"""DataUpdateCoordinator for the Elion integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ElionApi, ElionApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ElionDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Elion data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: ElionApi,
    ) -> None:
        """Initialize coordinator."""
        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Elion."""
        try:
            return await self.api.async_get_live()
        except ElionApiError as err:
            raise UpdateFailed(str(err)) from err