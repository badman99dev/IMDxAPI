"""Application configuration for IMDxAPI."""
import os


class Settings:
    """Runtime settings loaded from environment with sane defaults."""

    # IMDb GraphQL endpoint (reverse-engineered internal API)
    IMDB_GRAPHQL_URL = os.getenv(
        "IMDB_GRAPHQL_URL", "https://api.graphql.imdb.com/"
    )

    # Header spoofing to look like a real browser session to IMDb
    USER_AGENT = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )

    # Region / language localisation for IMDb responses
    COUNTRY = os.getenv("IMDB_COUNTRY", "US")
    LANGUAGE = os.getenv("IMDB_LANGUAGE", "en-US")

    # TTL (seconds) for in-process response caching to respect IMDb rate limits
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

    # CDN edge-caching headers. Default OFF — the Cloudflare Worker proxy
    # (cf_worker/) handles edge caching. Set CDN_CACHE=true to enable these
    # headers when deploying standalone (without the Worker).
    CDN_CACHE = os.getenv("CDN_CACHE", "false").lower() in ("true", "1", "yes", "on")

    # Retry behaviour on transient failures / rate limits
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT = float(os.getenv("TIMEOUT", "20"))

    # Pagination bounds (Tiffara API caps)
    MAX_SEARCH_LIMIT = int(os.getenv("MAX_SEARCH_LIMIT", "50"))
    MAX_BATCH_TITLES = int(os.getenv("MAX_BATCH_TITLES", "5"))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "50"))


settings = Settings()
