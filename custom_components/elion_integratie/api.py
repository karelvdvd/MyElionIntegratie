"""API client for the Elion integration."""

from __future__ import annotations

import logging
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
        url = f"{API_BASE_URL}/sites/{self._site_id}/live"

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