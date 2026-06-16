"""API client for the Elion integration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_BASE_URL, METERING_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class ElionApiError(Exception):
    """Base Elion API error."""


class ElionAuthError(ElionApiError):
    """Elion authentication error."""


class ElionApi:
    """Elion dashboard API client."""

    def __init__(
        self,
        session: ClientSession,
        site_id: str,
        access_token: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._site_id = site_id
        self._access_token = access_token

    async def async_get_live(self) -> dict[str, Any]:
        """Get live site data."""
        return await self._async_get(f"/sites/{self._site_id}/live")

    async def async_get_metering(self) -> dict[str, Any]:
        """Get metering data for today."""
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        fromts = int(start_of_day.timestamp())
        tots = int(now.timestamp())

        data = await self._async_get(
            f"/sites/{self._site_id}/metering?fromts={fromts}&tots={tots}"
        )

        readings = data.get("readings", [])
        if not isinstance(readings, list):
            raise ElionApiError("Unexpected Elion metering response")

        latest = self._get_latest_valid_reading(readings)
        totals = self._calculate_day_totals(readings)

        return {
            "readings": readings,
            "latest": latest,
            "totals": totals,
        }

    @staticmethod
    def _get_latest_valid_reading(readings: list[Any]) -> dict[str, Any]:
        """Return latest reading with real data."""
        for reading in reversed(readings):
            if isinstance(reading, dict) and reading.get("soc") is not None:
                return reading

        return {}

    @staticmethod
    def _calculate_day_totals(readings: list[Any]) -> dict[str, float]:
        """Calculate daily kWh totals from 15-minute metering values."""
        fields = {
            "consumption_today": "consumption",
            "production_today": "production",
            "flex_charge_today": "flexCharge",
            "flex_discharge_today": "flexDischarge",
            "grid_offtake_today": "gridOfftake",
            "grid_inject_today": "gridInject",
        }

        totals: dict[str, float] = {}

        for total_key, source_key in fields.items():
            total = 0.0

            for reading in readings:
                if not isinstance(reading, dict):
                    continue

                value = reading.get(source_key)
                if value is None:
                    continue

                try:
                    total += float(value) * METERING_INTERVAL_HOURS / 1000
                except (TypeError, ValueError):
                    continue

            totals[total_key] = total

        totals["grid_inject_today_negative"] = -totals.get("grid_inject_today", 0.0)

        return totals

    async def _async_get(self, path: str) -> dict[str, Any]:
        """Execute GET request."""
        url = f"{API_BASE_URL}{path}"

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json, text/plain, */*",
        }

        try:
            async with self._session.get(
                url,
                headers=headers,
                timeout=30,
            ) as response:
                if response.status in (401, 403):
                    text = await response.text()
                    _LOGGER.warning("Elion authentication failed: %s", text)
                    raise ElionAuthError("Invalid or expired Elion access token")

                response.raise_for_status()
                data = await response.json()

        except ElionAuthError:
            raise
        except ClientResponseError as err:
            raise ElionApiError(f"Elion API returned HTTP {err.status}") from err
        except ClientError as err:
            raise ElionApiError("Cannot connect to Elion API") from err

        if not isinstance(data, dict):
            raise ElionApiError("Unexpected Elion API response")

        return data