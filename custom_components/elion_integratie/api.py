"""API client for the Elion integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_BASE_URL, LOCAL_TIMEZONE, METERING_INTERVAL_HOURS

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
        access_token: str | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        token_url: str | None = None,
        redirect_uri: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._site_id = site_id
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._client_id = client_id
        self._token_url = token_url
        self._redirect_uri = redirect_uri

    async def async_get_live(self) -> dict[str, Any]:
        """Get live site data."""
        return await self._async_get(f"/sites/{self._site_id}/live")

    async def async_get_metering(self) -> dict[str, Any]:
        """Get metering data for the current local day."""
        local_tz = ZoneInfo(LOCAL_TIMEZONE)

        now = datetime.now(local_tz)
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

    async def async_refresh_access_token(self) -> str:
        """Refresh the Salesforce/Elindus access token."""
        if not self._token_url or not self._client_id or not self._refresh_token:
            raise ElionAuthError("Missing refresh token configuration")

        payload = {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "refresh_token": self._refresh_token,
        }

        if self._redirect_uri:
            payload["redirect_uri"] = self._redirect_uri

        try:
            async with self._session.post(
                self._token_url,
                data=payload,
                timeout=30,
            ) as response:
                text = await response.text()

                if response.status in (400, 401, 403):
                    _LOGGER.warning("Elion token refresh failed: %s", text)
                    raise ElionAuthError("Could not refresh Elion access token")

                response.raise_for_status()

                try:
                    data = await response.json()
                except Exception as err:  # noqa: BLE001
                    raise ElionAuthError("Invalid token refresh response") from err

        except ElionAuthError:
            raise
        except ClientResponseError as err:
            raise ElionApiError(f"Elion token endpoint returned HTTP {err.status}") from err
        except ClientError as err:
            raise ElionApiError("Cannot connect to Elion token endpoint") from err

        access_token = data.get("access_token")
        if not access_token:
            raise ElionAuthError("Token refresh response did not contain access_token")

        self._access_token = str(access_token)
        _LOGGER.debug("Elion access token refreshed")

        return self._access_token

    async def _async_get(self, path: str) -> dict[str, Any]:
        """Execute GET request with one automatic token refresh."""
        if not self._access_token:
            await self.async_refresh_access_token()

        try:
            return await self._async_get_once(path)
        except ElionAuthError:
            if not self._refresh_token:
                raise

            _LOGGER.info("Elion access token invalid or expired, refreshing")
            await self.async_refresh_access_token()
            return await self._async_get_once(path)

    async def _async_get_once(self, path: str) -> dict[str, Any]:
        """Execute one GET request."""
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
        """Calculate daily kWh totals exactly like the Elion dashboard."""
        totals: dict[str, float] = {
            "consumption_today": 0.0,
            "production_today": 0.0,
            "curtailed_production_today": 0.0,
            "flex_charge_today": 0.0,
            "flex_discharge_today": 0.0,
            "grid_offtake_today": 0.0,
            "grid_inject_today": 0.0,
        }

        for reading in readings:
            if not isinstance(reading, dict):
                continue

            consumption = cls._safe_float(reading.get("consumption"))
            production = cls._safe_float(reading.get("uncurtailedProduction"))
            curtailed_production = cls._safe_float(reading.get("curtailedProduction"))
            flex_charge = cls._safe_float(reading.get("flexCharge"))
            flex_discharge = cls._safe_float(reading.get("flexDischarge"))
            grid_offtake = cls._safe_float(reading.get("gridOfftake"))
            grid_inject = cls._safe_float(reading.get("gridInject"))

            if consumption is not None:
                totals["consumption_today"] += (
                    consumption * METERING_INTERVAL_HOURS / 1000
                )

            if production is not None:
                totals["production_today"] += (
                    production * METERING_INTERVAL_HOURS / 1000
                )

            if curtailed_production is not None:
                totals["curtailed_production_today"] += (
                    curtailed_production * METERING_INTERVAL_HOURS / 1000
                )

            if flex_charge is not None:
                totals["flex_charge_today"] += (
                    flex_charge * METERING_INTERVAL_HOURS / 1000
                )

            if flex_discharge is not None:
                totals["flex_discharge_today"] += (
                    flex_discharge * METERING_INTERVAL_HOURS / 1000
                )

            if grid_offtake is not None:
                totals["grid_offtake_today"] += (
                    grid_offtake * METERING_INTERVAL_HOURS / 1000
                )

            if grid_inject is not None:
                totals["grid_inject_today"] += (
                    grid_inject * METERING_INTERVAL_HOURS / 1000
                )

        totals["grid_inject_today_negative"] = -totals["grid_inject_today"]

        return totals