"""Config flow for the Elion integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN


class ElionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elion."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""

        if user_input is not None:
            await self.async_set_unique_id(user_input["username"])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Elion",
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required("username"): str,
                vol.Required("password"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors={},
        )