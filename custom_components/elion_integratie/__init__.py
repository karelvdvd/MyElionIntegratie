"""The Elion integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .api import ElionApi, ElionApiError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_REDIRECT_URI,
    CONF_REFRESH_TOKEN,
    CONF_SITE_ID,
    CONF_TOKEN_URL,
    DOMAIN,
    PLATFORMS,
    TOKEN_REFRESH_INTERVAL,
)
from .coordinator import ElionLiveCoordinator, ElionMeteringCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Elion from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)

    def _async_save_tokens(
        access_token: str,
        refresh_token: str | None,
    ) -> None:
        """Save refreshed tokens back to the config entry."""
        new_data = dict(entry.data)
        new_data[CONF_ACCESS_TOKEN] = access_token

        if refresh_token:
            new_data[CONF_REFRESH_TOKEN] = refresh_token

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
        )

    api = ElionApi(
        session=session,
        site_id=entry.data[CONF_SITE_ID],
        access_token=entry.data.get(CONF_ACCESS_TOKEN) or None,
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN) or None,
        client_id=entry.data.get(CONF_CLIENT_ID) or None,
        token_url=entry.data.get(CONF_TOKEN_URL) or None,
        redirect_uri=entry.data.get(CONF_REDIRECT_URI) or None,
        token_update_callback=_async_save_tokens,
    )

    live_coordinator = ElionLiveCoordinator(
        hass=hass,
        api=api,
    )

    metering_coordinator = ElionMeteringCoordinator(
        hass=hass,
        api=api,
    )

    await live_coordinator.async_config_entry_first_refresh()
    await metering_coordinator.async_config_entry_first_refresh()

    async def _async_proactive_token_refresh(_now) -> None:
        """Refresh token proactively before Elion invalidates it."""
        try:
            await api.async_refresh_access_token()
        except ElionApiError as err:
            _LOGGER.warning("Elion proactive token refresh failed: %s", err)
        else:
            _LOGGER.info("Elion proactive token refresh succeeded")

    entry.async_on_unload(
        async_track_time_interval(
            hass,
            _async_proactive_token_refresh,
            timedelta(seconds=TOKEN_REFRESH_INTERVAL),
        )
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "live": live_coordinator,
        "metering": metering_coordinator,
        "api": api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok