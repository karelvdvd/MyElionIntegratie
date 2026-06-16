"""Config flow for the Elion integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ElionApi, ElionApiError, ElionAuthError
from .const import CONF_ACCESS_TOKEN, CONF_SITE_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ElionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elion."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            site_id = str(user_input[CONF_SITE_ID]).strip()
            access_token = str(user_input[CONF_ACCESS_TOKEN]).strip()

            await self.async_set_unique_id(site_id)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = ElionApi(
                session=session,
                site_id=site_id,
                access_token=access_token,
            )

            try:
                await api.async_get_live()
            except ElionAuthError:
                errors["base"] = "invalid_auth"
            except ElionApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error while validating Elion config")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Elion site {site_id}",
                    data={
                        CONF_SITE_ID: site_id,
                        CONF_ACCESS_TOKEN: access_token,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SITE_ID, default="808"): str,
                vol.Required(CONF_ACCESS_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )