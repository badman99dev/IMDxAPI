"""Query parameter models for request validation."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TitleSortBy(str, Enum):
    """Supported sort keys for the /titles endpoint."""

    SORT_BY_POPULARITY = "SORT_BY_POPULARITY"
    SORT_BY_RELEASE_DATE = "SORT_BY_RELEASE_DATE"
    SORT_BY_USER_RATING = "SORT_BY_USER_RATING"
    SORT_BY_USER_RATING_COUNT = "SORT_BY_USER_RATING_COUNT"
    SORT_BY_YEAR = "SORT_BY_YEAR"


class SortOrder(str, Enum):
    """Optional sort direction."""

    ASC = "ASC"
    DESC = "DESC"


class TitlesQueryParams(BaseModel):
    """Query parameters for GET /titles."""

    types: Optional[List[str]] = None
    genres: Optional[List[str]] = None
    countryCodes: Optional[List[str]] = None
    languageCodes: Optional[List[str]] = None
    nameIds: Optional[List[str]] = None
    interestIds: Optional[List[str]] = None
    startYear: Optional[int] = None
    endYear: Optional[int] = None
    minVoteCount: Optional[int] = None
    maxVoteCount: Optional[int] = None
    minAggregateRating: Optional[float] = None
    maxAggregateRating: Optional[float] = None
    sortBy: Optional[TitleSortBy] = TitleSortBy.SORT_BY_POPULARITY
    sortOrder: Optional[SortOrder] = SortOrder.DESC
    pageToken: Optional[str] = None
    limit: Optional[int] = Field(
        None, ge=1, le=50, description="Max 50 results per page."
    )
