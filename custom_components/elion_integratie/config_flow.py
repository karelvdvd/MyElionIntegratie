"""Config flow for the Elion integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ElionApi, ElionApiError, ElionAuthError
from .const import (
    CLIENT_ID,
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_REDIRECT_URI,
    CONF_REFRESH_TOKEN,
    CONF_SITE_ID,
    CONF_TOKEN_URL,
    DOMAIN,
    REDIRECT_URI,
    TOKEN_URL,
)

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
            access_token = str(user_input.get(CONF_ACCESS_TOKEN, "")).strip() or None
            refresh_token = str(user_input[CONF_REFRESH_TOKEN]).strip()

            await self.async_set_unique_id(site_id)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = ElionApi(
                session=session,
                site_id=site_id,
                access_token=access_token,
                refresh_token=refresh_token,
                client_id=CLIENT_ID,
                token_url=TOKEN_URL,
                redirect_uri=REDIRECT_URI,
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
                        CONF_ACCESS_TOKEN: api.access_token or access_token or "",
                        CONF_REFRESH_TOKEN: api.refresh_token or refresh_token,
                        CONF_CLIENT_ID: CLIENT_ID,
                        CONF_TOKEN_URL: TOKEN_URL,
                        CONF_REDIRECT_URI: REDIRECT_URI,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SITE_ID): str,
                vol.Required(CONF_REFRESH_TOKEN): str,
                vol.Optional(CONF_ACCESS_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: dict,
    ) -> config_entries.ConfigFlowResult:
        """Handle reauthentication when the refresh token stops working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Ask the user for a fresh refresh token."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            refresh_token = str(user_input[CONF_REFRESH_TOKEN]).strip()
            access_token = str(user_input.get(CONF_ACCESS_TOKEN, "")).strip() or None

            session = async_get_clientsession(self.hass)
            api = ElionApi(
                session=session,
                site_id=reauth_entry.data[CONF_SITE_ID],
                access_token=access_token,
                refresh_token=refresh_token,
                client_id=CLIENT_ID,
                token_url=TOKEN_URL,
                redirect_uri=REDIRECT_URI,
            )

            try:
                await api.async_get_live()
            except ElionAuthError:
                errors["base"] = "invalid_auth"
            except ElionApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error while validating Elion reauth")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_ACCESS_TOKEN: api.access_token or access_token or "",
                        CONF_REFRESH_TOKEN: api.refresh_token or refresh_token,
                        CONF_CLIENT_ID: CLIENT_ID,
                        CONF_TOKEN_URL: TOKEN_URL,
                        CONF_REDIRECT_URI: REDIRECT_URI,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_REFRESH_TOKEN): str,
                    vol.Optional(CONF_ACCESS_TOKEN): str,
                }
            ),
            errors=errors,
        )
