"""Thin async client for IMDb's internal (reverse-engineered) GraphQL API.

All GraphQL queries here were verified to work against
`https://api.graphql.imdb.com/` (sources: imdb-unofficial-api and
imdbGraphQLPHP). The endpoint needs browser-like headers, not an API key.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

from ..config import settings

GRAPHQL_URL = settings.IMDB_GRAPHQL_URL


class ImdbError(Exception):
    """Base error raised by the IMDb client."""


class ImdbNotFoundError(ImdbError):
    """Raised when a requested resource does not exist."""


class ImdbRateLimitError(ImdbError):
    """Raised when IMDb rate-limits the request (HTTP 429)."""


class ImdbGraphQLError(ImdbError):
    """Raised when the GraphQL endpoint returns errors."""


def _headers(country: str = settings.COUNTRY, language: str = settings.LANGUAGE) -> Dict[str, str]:
    """Build browser-like request headers for the IMDb GraphQL endpoint."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": settings.USER_AGENT,
        "Origin": "https://www.imdb.com",
        "Referer": "https://www.imdb.com/",
        "X-Imdb-User-Country": country,
        "X-Imdb-User-Language": language,
        "x-imdb-client-name": "imdb-web-next-localized",
    }


class ImdbClient:
    """Async HTTP client with retry + TTL caching for IMDb GraphQL."""

    def __init__(
        self,
        country: str = settings.COUNTRY,
        language: str = settings.LANGUAGE,
        cache_ttl: int = settings.CACHE_TTL,
        max_retries: int = settings.MAX_RETRIES,
        timeout: float = settings.TIMEOUT,
    ) -> None:
        self._client = httpx.AsyncClient(
            headers=_headers(country, language),
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )
        self._cache_ttl = cache_ttl
        self._max_retries = max_retries
        self._cache: Dict[str, tuple[float, Any]] = {}

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "ImdbClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def graphql(
        self, query: str, variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a GraphQL request and return the `data` payload."""
        variables = variables or {}
        cache_key = f"{operation_name}|{query}|{variables}"
        if self._cache_ttl and cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                return data

        payload: Dict[str, Any] = {"query": query, "variables": variables}
        if operation_name:
            payload["operationName"] = operation_name

        for attempt in range(self._max_retries):
            resp = await self._client.post(GRAPHQL_URL, json=payload)
            if resp.status_code == 429:
                if attempt < self._max_retries - 1:
                    await self._sleep(2 ** attempt)
                    continue
                raise ImdbRateLimitError("Rate limited by IMDb API")
            if resp.status_code == 404:
                raise ImdbNotFoundError("Resource not found")
            resp.raise_for_status()
            data = resp.json()

            if "errors" in data:
                is_retriable = any(
                    e.get("extensions", {}).get("code")
                    in ("INTERNAL_ERROR", "TIMEOUT", "GRAPHQL_PARSE_FAILED")
                    for e in data["errors"]
                )
                if is_retriable and attempt < self._max_retries - 1:
                    await self._sleep(2 ** attempt)
                    continue
                raise ImdbGraphQLError(str(data["errors"]))

            result = data.get("data", {})
            if self._cache_ttl:
                self._cache[cache_key] = (time.time(), result)
            return result

        raise ImdbError("Max retries exceeded")

    @staticmethod
    async def _sleep(seconds: float) -> None:
        import asyncio

        await asyncio.sleep(seconds)
