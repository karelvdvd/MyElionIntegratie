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

# Salesforce Experience Cloud OAuth2 (PKCE, public client) achter het Elion
# dashboard. Deze waarden staan publiek in de frontend-config (/__ENV.js) van
# dashboard.elion.be en zijn hetzelfde voor elke Elion-gebruiker, dus hoeven
# niet per installatie ingevuld te worden.
TOKEN_URL = "https://klant.elindus.be/services/oauth2/token"
CLIENT_ID = (
    "3MVG98_Psg5cppybYBR_rfLR4ao9_1wSWXNAec5JG7SHIfr8BpJTCuEIATA2oQ8O4Kpn_tSnKBhwZLdmUl5EU"
)
REDIRECT_URI = "https://dashboard.elion.be"

LIVE_SCAN_INTERVAL = 5
METERING_SCAN_INTERVAL = 60

# Refresh ruim vóór de access token vervalt.
# Salesforce/Elindus lijkt te falen als we wachten tot "Invalid token".
TOKEN_REFRESH_INTERVAL = 55 * 60

METERING_INTERVAL_HOURS = 0.25
LOCAL_TIMEZONE = "Europe/Brussels"

PLATFORMS = [Platform.SENSOR]