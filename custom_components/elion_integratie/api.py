"""API client for the Elion integration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_BASE_URL

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
        """Get metering data from start of current UTC day until now."""
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

        for reading in reversed(readings):
            if isinstance(reading, dict) and reading.get("soc") is not None:
                return reading

        return {}

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