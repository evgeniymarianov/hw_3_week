import httpx
from fastapi import HTTPException, status

from samokat.infrastructure.api_connectors.base import BaseHTTPConnector
from samokat.infrastructure.api_connectors.schemas import (
    AddressSuggestionData,
    ResolvedAddressData,
)
from samokat.infrastructure.redis.manager import RedisManager


class AddressConnector(BaseHTTPConnector):
    def __init__(
        self,
        base_url: str,
        timeout: float,
        client_id: str,
        client_secret: str,
        redis_client: RedisManager,
        headers: dict[str, str] | None = None,
        token_refresh_path: str = "/auth/token/refresh",
    ) -> None:
        super().__init__(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            rate_limit_requests=15,
            rate_limit_interval=60,
        )
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_refresh_path = token_refresh_path
        self._access_token: str | None = None
        self._redis_client = redis_client

    async def suggest_addresses(
        self,
        query: str,
    ) -> list[AddressSuggestionData]:
        response = await self._request_with_token_refresh(
            "GET",
            "/suggest",
            retry=True,
            params={"query": query},
        )
        response.raise_for_status()
        data = response.json()

        return [
            AddressSuggestionData(
                id=item["id"],
                address_text=item["address_text"],
                lat=item["lat"],
                lon=item["lon"],
            )
            for item in data["suggestions"]
        ]

    async def get_address_full_info(
        self,
        address_id: str,
    ) -> ResolvedAddressData:
        response = await self._request_with_token_refresh(
            "GET",
            "/resolve",
            retry=True,
            params={"address_id": address_id},
        )
        response.raise_for_status()
        data = response.json()

        return ResolvedAddressData(
            address_text=data["address_text"],
            lat=data["lat"],
            lon=data["lon"],
        )

    async def _request_with_token_refresh(
        self,
        method: str,
        url: str,
        retry: bool,
        **kwargs,
    ) -> httpx.Response:
        access_token = self._access_token

        if not access_token:
            access_token = await self._redis_client.client.get("address-api:access-token")
            self._access_token = access_token

        if access_token is None:
            access_token = await self._refresh_token_with_lock()

        response = await self._request(
            method,
            url,
            retry,
            **self._with_auth_header(kwargs, access_token),
        )

        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=response.json()["detail"],
            )

        if response.status_code != 401:
            return response

        access_token = await self._refresh_token_with_lock(expired_token=access_token)
        return await self._request(
            method,
            url,
            retry,
            **self._with_auth_header(kwargs, access_token),
        )

    async def _refresh_token_with_lock(self, expired_token: str | None = None):
        async with self._redis_client.client.lock(
            name="locks:address-api-access-token",
            timeout=5,
            blocking_timeout=3,
        ):
            access_token = await self._redis_client.client.get("address-api:access-token")
            if access_token is not None and access_token != expired_token:
                self._access_token = access_token
                return access_token

            access_token = await self._refresh_token()
            self._access_token = access_token
            await self._redis_client.client.set(
                name="address-api:access-token",
                value=access_token,
                ex=29,
            )
            return access_token

    async def _refresh_token(self) -> str:
        response = await self._request(
            "POST",
            "/auth/token/refresh",
            json={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]

    def _with_auth_header(self, kwargs: dict, access_token: str) -> dict:
        if self._access_token is None:
            return kwargs

        headers = {
            **kwargs.get("headers", {}),
            "Authorization": f"Bearer {access_token}",
        }

        return {
            **kwargs,
            "headers": headers,
        }
