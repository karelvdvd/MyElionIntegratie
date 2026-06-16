"""The Elion integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ElionApi
from .const import CONF_ACCESS_TOKEN, CONF_SITE_ID, DOMAIN, PLATFORMS
from .coordinator import ElionLiveCoordinator, ElionMeteringCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Elion from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)

    api = ElionApi(
        session=session,
        site_id=entry.data[CONF_SITE_ID],
        access_token=entry.data[CONF_ACCESS_TOKEN],
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

    hass.data[DOMAIN][entry.entry_id] = {
        "live": live_coordinator,
        "metering": metering_coordinator,
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