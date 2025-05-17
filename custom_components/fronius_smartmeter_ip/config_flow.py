"""Config flow for Fronius Smartmeter IP."""
import logging
from typing import Any

import httpx
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL, CONF_USERNAME, CONF_PASSWORD

from .const import (
    DOMAIN,
    API_PATH_MEASUREMENTS,
    API_QUERY_PARAMS,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_URL): str,
    vol.Required(CONF_USERNAME): str, # Behalte diese bei, auch wenn sie leer sein können
    vol.Required(CONF_PASSWORD): str, # Behalte diese bei
})

async def validate_input(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    base_url = data[CONF_URL].rstrip('/')
    username = data.get(CONF_USERNAME) # Verwende .get() falls die Felder optional sein könnten
    password = data.get(CONF_PASSWORD)
    api_url = f"{base_url}{API_PATH_MEASUREMENTS}"

    # Auth Tupel erstellen, falls Benutzername und Passwort vorhanden sind
    auth_tuple = (username, password) if username and password else None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                api_url,
                auth=auth_tuple, # <--- GEÄNDERT: Tupel verwenden
                params=API_QUERY_PARAMS
            )
            response.raise_for_status()
            response.json()
    except httpx.HTTPStatusError as http_err:
        _LOGGER.error("HTTP error during validation (%s): %s", api_url, http_err)
        if http_err.response.status_code == 401:
            # Überprüfe, ob auth_tuple überhaupt gesetzt war, bevor du invalid_auth meldest
            if auth_tuple:
                raise vol.Invalid("invalid_auth") from http_err
            else: # Kein Auth versucht, aber 401 bekommen -> Server erwartet Auth
                raise vol.Invalid("auth_required_but_not_provided") from http_err
        raise vol.Invalid("cannot_connect_http") from http_err
    except httpx.RequestError as req_err:
        _LOGGER.error("Request error during validation (%s): %s", api_url, req_err)
        raise vol.Invalid("cannot_connect_request") from req_err
    except (ValueError, TypeError) as json_err:
        _LOGGER.error("JSON parsing error during validation (%s): %s", api_url, json_err)
        raise vol.Invalid("invalid_response") from json_err
    except Exception as e:
        _LOGGER.error("Unexpected error during validation (%s): %s", api_url, e)
        raise vol.Invalid("unknown") from e

    return {"title": data[CONF_URL].split('//')[-1] or "Fronius Smartmeter IP"}


class FroniusSmartmeterIPConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            # Wenn Benutzername/Passwort leer sind, behandle sie als None für validate_input
            # (obwohl .get() in validate_input das bereits abfängt)
            processed_input = user_input.copy()
            if not processed_input.get(CONF_USERNAME): # Explizit None wenn leer
                 processed_input[CONF_USERNAME] = None
            if not processed_input.get(CONF_PASSWORD):
                 processed_input[CONF_PASSWORD] = None


            await self.async_set_unique_id(user_input[CONF_URL])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(processed_input) # Verwende processed_input
                # Speichere die originalen user_input (können leere Strings sein),
                # da HA leere Strings in der Konfiguration speichert, nicht None, wenn das Schema es so definiert.
                return self.async_create_entry(title=info["title"], data=user_input)
            except vol.Invalid as err_type:
                errors["base"] = str(err_type)
            except Exception:
                _LOGGER.exception("Unexpected exception in config flow")
                errors["base"] = "unknown"
        
        # Definiere das Schema hier neu, um leere Eingaben zu erlauben, falls htaccess optional ist
        # Wenn htaccess IMMER benötigt wird, dann lasse die Felder Required.
        # Für optionale Felder:
        # data_schema = vol.Schema({
        #     vol.Required(CONF_URL): str,
        #     vol.Optional(CONF_USERNAME, default=""): str,
        #     vol.Optional(CONF_PASSWORD, default=""): str,
        # })
        # Für jetzt belassen wir es bei Required, da htaccess Auth das ursprüngliche Problem war.
        # Der Benutzer muss dann ggf. Dummy-Werte eingeben, wenn keine Auth benötigt wird,
        # oder das Schema müsste auf Optional geändert werden.
        # Da die API htaccess-geschützt ist, bleiben wir bei Required.

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )