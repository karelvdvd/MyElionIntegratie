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
    def _safe_float(value: Any) -> float | None:
        """Convert a value to float safely."""
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _calculate_day_totals(cls, readings: list[Any]) -> dict[str, float]:
        """Calculate daily kWh totals from 15-minute metering values."""
        totals: dict[str, float] = {
            "consumption_today": 0.0,
            "production_today": 0.0,
            "flex_charge_today": 0.0,
            "flex_discharge_today": 0.0,
            "grid_offtake_today": 0.0,
            "grid_inject_today": 0.0,
        }

        for reading in readings:
            if not isinstance(reading, dict):
                continue

            consumption = cls._safe_float(reading.get("consumption"))
            production = cls._safe_float(reading.get("production"))
            grid_offtake = cls._safe_float(reading.get("gridOfftake"))
            grid_inject = cls._safe_float(reading.get("gridInject"))
            flex_charge = cls._safe_float(reading.get("flexCharge"))
            flex_discharge = cls._safe_float(reading.get("flexDischarge"))

            if consumption is not None:
                totals["consumption_today"] += (
                    consumption * METERING_INTERVAL_HOURS / 1000
                )

            if production is not None:
                totals["production_today"] += (
                    production * METERING_INTERVAL_HOURS / 1000
                )

            if grid_offtake is not None:
                totals["grid_offtake_today"] += (
                    grid_offtake * METERING_INTERVAL_HOURS / 1000
                )

            if grid_inject is not None:
                totals["grid_inject_today"] += (
                    grid_inject * METERING_INTERVAL_HOURS / 1000
                )

            # Elion dashboard uses:
            # battery_action = flexCharge - flexDischarge
            #
            # Positive = battery charging
            # Negative = battery discharging
            if flex_charge is not None and flex_discharge is not None:
                battery_action = flex_charge - flex_discharge

                if battery_action > 0:
                    totals["flex_charge_today"] += (
                        battery_action * METERING_INTERVAL_HOURS / 1000
                    )
                elif battery_action < 0:
                    totals["flex_discharge_today"] += (
                        abs(battery_action) * METERING_INTERVAL_HOURS / 1000
                    )

        totals["grid_inject_today_negative"] = -totals["grid_inject_today"]

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