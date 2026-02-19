"""Config flow for Fronius Smartmeter IP."""
import logging
from typing import Any

import httpx
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL, CONF_PASSWORD

from .auth import FroniusJWTAuth
from .const import (
    DOMAIN,
    API_PATH_MEASUREMENTS,
    API_QUERY_PARAMS,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_URL): str,
    vol.Required(CONF_PASSWORD): str,
})

async def validate_input(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    base_url = data[CONF_URL].rstrip('/')
    password = data.get(CONF_PASSWORD)
    api_url = f"{base_url}{API_PATH_MEASUREMENTS}"

    try:
        # Authentifizierung über JWT
        jwt_auth = FroniusJWTAuth(base_url, password)
        token = await jwt_auth.get_token()

        cookies = {}
        if token:
            cookies["jwt"] = token

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                api_url,
                cookies=cookies,
                params=API_QUERY_PARAMS
            )
            response.raise_for_status()
            response.json()

        await jwt_auth.close()

    except httpx.HTTPStatusError as http_err:
        _LOGGER.error("HTTP error during validation (%s): %s", api_url, http_err)
        if http_err.response.status_code == 401:
            raise vol.Invalid("invalid_auth") from http_err
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
            await self.async_set_unique_id(user_input[CONF_URL])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except vol.Invalid as err_type:
                errors["base"] = str(err_type)
            except Exception:
                _LOGGER.exception("Unexpected exception in config flow")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
