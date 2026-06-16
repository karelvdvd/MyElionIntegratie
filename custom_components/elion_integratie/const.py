"""Constants for the Elion integration."""

from homeassistant.const import Platform

DOMAIN = "elion_integratie"

NAME = "Elion Integratie"
MANUFACTURER = "Elion"

CONF_SITE_ID = "site_id"
CONF_ACCESS_TOKEN = "access_token"

API_BASE_URL = "https://dashboard.elion.be/api"

DEFAULT_SCAN_INTERVAL = 60

PLATFORMS = [Platform.SENSOR]