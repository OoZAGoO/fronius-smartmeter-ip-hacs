"""JWT Authentication Handler for Fronius Smart Meter IP."""
import logging
import httpx
from typing import Optional
from datetime import datetime, timedelta

from Crypto.Hash import keccak

_LOGGER = logging.getLogger(__name__)


def derive_hash(password: str, salt_hex: str) -> str:
    """Derive Keccak-512 hash from password and salt."""
    data = (password + salt_hex).encode("utf-8")
    k = keccak.new(digest_bits=512)
    k.update(data)
    return k.hexdigest()


class FroniusJWTAuth:
    """Handle JWT authentication for Fronius Smart Meter IP."""

    def __init__(self, base_url: str, password: str):
        """Initialize the JWT auth handler."""
        self.base_url = base_url.rstrip('/')
        self.password = password
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._client = httpx.AsyncClient(timeout=10)

    async def get_token(self) -> Optional[str]:
        """Get valid JWT token, refresh if needed."""
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token

        return await self._refresh_token()

    async def _refresh_token(self) -> Optional[str]:
        """Request new JWT token from the API."""
        try:
            # Step 1: Get salt from settings
            settings_url = f"{self.base_url}/wizard/public/api/settings"
            settings_response = await self._client.get(settings_url)
            settings_response.raise_for_status()
            settings_data = settings_response.json()
            salt = settings_data.get("salt")
            if not salt:
                _LOGGER.error("No salt found in settings response")
                return None

            # Step 2: Compute Keccak-512 hash
            password_hash = derive_hash(self.password, salt)

            # Step 3: Login with salt,hash to get JWT cookie
            login_url = f"{self.base_url}/wizard/public/api/login"
            payload = {"password": f"{salt},{password_hash}"}
            response = await self._client.post(login_url, json=payload)
            response.raise_for_status()

            # Extract JWT from Set-Cookie header
            jwt_token = response.cookies.get("jwt")
            if not jwt_token:
                _LOGGER.error("No jwt cookie in login response")
                return None

            self._token = jwt_token
            # Refresh after 50 minutes (JWT typically expires after 1 hour)
            self._token_expiry = datetime.now() + timedelta(minutes=50)

            _LOGGER.debug("Successfully obtained JWT token")
            return self._token

        except Exception as err:
            _LOGGER.error("Failed to obtain JWT token: %s", err)
            self._token = None
            self._token_expiry = None
            return None

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
