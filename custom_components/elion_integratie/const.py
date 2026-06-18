"""Constants for the Elion integration."""

from homeassistant.const import Platform

DOMAIN = "elion_integratie"

NAME = "Elion Integratie"
MANUFACTURER = "Elion"

CONF_SITE_ID = "site_id"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_CLIENT_ID = "client_id"
CONF_TOKEN_URL = "token_url"
CONF_REDIRECT_URI = "redirect_uri"

API_BASE_URL = "https://dashboard.elion.be/api"

LIVE_SCAN_INTERVAL = 5
METERING_SCAN_INTERVAL = 60

METERING_INTERVAL_HOURS = 0.25
LOCAL_TIMEZONE = "Europe/Brussels"

PLATFORMS = [Platform.SENSOR]