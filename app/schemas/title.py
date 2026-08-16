"""Pydantic models matching the Tiffara imdbapiTitle schema exactly."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import (
    imdbapiCountry,
    imdbapiImage,
    imdbapiInterest,
    imdbapiLanguage,
    imdbapiMetacritic,
    imdbapiRating,
)
from .name import imdbapiName


class imdbapiTitle(BaseModel):
    """A movie, TV series, TV episode, or other title."""

    id: Optional[str] = Field(None, description="IMDb title ID (e.g. tt1375666).")
    type: Optional[str] = Field(
        None, description='Title type, e.g. "movie", "tvSeries".'
    )
    isAdult: Optional[bool] = Field(None, description="Indicates adult content.")
    primaryTitle: Optional[str] = Field(
        None, description="Primary (most recognised) title."
    )
    originalTitle: Optional[str] = Field(
        None, description="Title as originally released."
    )
    primaryImage: Optional[imdbapiImage] = Field(
        None, description="Primary poster/work image."
    )
    startYear: Optional[int] = Field(None, description="Earliest year.")
    endYear: Optional[int] = Field(None, description="Latest year (series).")
    runtimeSeconds: Optional[int] = Field(None, description="Runtime in seconds.")
    genres: Optional[List[str]] = Field(None, description="List of genres.")
    rating: Optional[imdbapiRating] = Field(None, description="Rating + votes.")
    metacritic: Optional[imdbapiMetacritic] = Field(None, description="Metacritic.")
    plot: Optional[str] = Field(None, description="Brief storyline summary.")
    directors: Optional[List[imdbapiName]] = Field(None, description="Directors.")
    writers: Optional[List[imdbapiName]] = Field(None, description="Writers.")
    stars: Optional[List[imdbapiName]] = Field(None, description="Star actors.")
    originCountries: Optional[List[imdbapiCountry]] = Field(
        None, description="Production countries."
    )
    spokenLanguages: Optional[List[imdbapiLanguage]] = Field(
        None, description="Spoken languages."
    )
    interests: Optional[List[imdbapiInterest]] = Field(
        None, description="Interests associated with the title."
    )


class imdbapiListTitlesResponse(BaseModel):
    """Response for listing/filtering titles."""

    titles: List[imdbapiTitle] = Field(default_factory=list)
    totalCount: Optional[int] = Field(None, description="Total matching titles.")
    nextPageToken: Optional[str] = Field(
        None, description="Token for the next page of results."
    )


class imdbapiBatchGetTitlesResponse(BaseModel):
    """Response for batch-getting multiple titles."""

    titles: List[imdbapiTitle] = Field(default_factory=list)


class imdbapiSearchTitlesResponse(BaseModel):
    """Response for the search endpoint."""

    titles: List[imdbapiTitle] = Field(default_factory=list)
