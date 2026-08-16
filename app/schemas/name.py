"""Pydantic models matching the Tiffara imdbapiName schema exactly."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import (
    imdbapiImage,
    imdbapiInterest,
    imdbapiPrecisionDate,
    imdbapiRating,
)


class imdbapiNameMeterRanking(BaseModel):
    """IMDb popularity meter ranking for a person."""

    currentRank: Optional[int] = None
    changeDirection: Optional[str] = Field(
        None, description="'UP', 'DOWN' or 'NO_CHANGE'."
    )
    difference: Optional[int] = Field(
        None, description="Rank difference since last measurement."
    )


class imdbapiName(BaseModel):
    """A person in the IMDb database (actor, director, etc.)."""

    id: Optional[str] = Field(None, description="IMDb name ID (e.g. nm0634240).")
    displayName: Optional[str] = Field(None, description="Person's full name.")
    alternativeNames: Optional[List[str]] = Field(
        None, description="Stage names, nicknames, variations."
    )
    primaryImage: Optional[imdbapiImage] = Field(
        None, description="Profile photo."
    )
    primaryProfessions: Optional[List[str]] = Field(
        None, description="e.g. Actor, Director, Producer."
    )
    biography: Optional[str] = Field(None, description="Career biography.")
    heightCm: Optional[int] = Field(None, description="Height in centimetres.")
    birthName: Optional[str] = Field(None, description="Birth name.")
    birthDate: Optional[imdbapiPrecisionDate] = Field(None, description="Birth date.")
    birthLocation: Optional[str] = Field(None, description="Birth location.")
    deathDate: Optional[imdbapiPrecisionDate] = Field(None, description="Death date.")
    deathLocation: Optional[str] = Field(None, description="Death location.")
    deathReason: Optional[str] = Field(None, description="Cause of death.")
    meterRanking: Optional[imdbapiNameMeterRanking] = Field(
        None, description="Popularity meter ranking."
    )


class imdbapiBatchGetNamesResponse(BaseModel):
    """Response for batch-getting multiple names."""

    names: List[imdbapiName] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Phase-3: Name sub-endpoints + charts + interests
# --------------------------------------------------------------------------- #
class imdbapiListNameFilmographyResponse(BaseModel):
    """Response for listing a name's filmography credits."""

    credits: List["imdbapiNameCredit"] = Field(default_factory=list)
    totalCount: Optional[int] = None
    nextPageToken: Optional[str] = None


class imdbapiNameCreditTitle(BaseModel):
    """Lightweight title embedded inside a filmography credit."""

    id: Optional[str] = Field(None, description="IMDb title ID (e.g. tt1375666).")
    type: Optional[str] = Field(None, description='Title type, e.g. "movie".')
    primaryTitle: Optional[str] = Field(None, description="Primary title.")
    primaryImage: Optional[imdbapiImage] = Field(None, description="Poster/work image.")
    startYear: Optional[int] = Field(None, description="Earliest year.")
    endYear: Optional[int] = Field(None, description="Latest year (series).")
    runtimeSeconds: Optional[int] = Field(None, description="Runtime in seconds.")
    rating: Optional[imdbapiRating] = Field(None, description="Rating + votes.")
    plot: Optional[str] = Field(None, description="Brief storyline summary.")


class imdbapiNameCredit(BaseModel):
    """A credit of a person in the filmography."""

    title: Optional[imdbapiNameCreditTitle] = Field(
        None, description="The title of the credit."
    )
    category: Optional[str] = Field(None, description="Category of the credit.")
    characters: Optional[List[str]] = Field(
        None, description="Characters played by the person."
    )
    episodeCount: Optional[int] = Field(
        None, description="Episodes the person appeared in."
    )


class imdbapiListNameImagesResponse(BaseModel):
    """Response for listing a name's images."""

    images: List[imdbapiImage] = Field(default_factory=list)
    totalCount: Optional[int] = None
    nextPageToken: Optional[str] = None


class imdbapiNameRelationship(BaseModel):
    """A relationship between two people."""

    name: Optional[imdbapiName] = Field(None, description="The related person.")
    relationType: Optional[str] = Field(None, description="e.g. Sibling, Parent.")
    attributes: Optional[List[str]] = Field(
        None, description="Additional relationship attributes."
    )


class imdbapiListNameRelationshipsResponse(BaseModel):
    """Response for listing a name's relationships."""

    relationships: List[imdbapiNameRelationship] = Field(default_factory=list)


class imdbapiNameTrivia(BaseModel):
    """A trivia entry about a person."""

    id: Optional[str] = None
    text: Optional[str] = Field(None, description="Trivia text.")
    interestCount: Optional[int] = Field(
        None, description="Users who found the entry interesting."
    )
    voteCount: Optional[int] = Field(
        None, description="Total votes on the entry."
    )


class imdbapiListNameTriviaResponse(BaseModel):
    """Response for listing a name's trivia entries."""

    triviaEntries: List[imdbapiNameTrivia] = Field(default_factory=list)
    totalCount: Optional[int] = None
    nextPageToken: Optional[str] = None


class imdbapiListStarMetersResponse(BaseModel):
    """Response for the STAR_METER chart (top names)."""

    names: List[imdbapiName] = Field(default_factory=list)
    nextPageToken: Optional[str] = None


class imdbapiInterestCategory(BaseModel):
    """A category of interests (e.g. Franchise, Action)."""

    category: Optional[str] = Field(None, description="Category label.")
    interests: List[imdbapiInterest] = Field(default_factory=list)


class imdbapiListInterestCategoriesResponse(BaseModel):
    """Response for listing interest categories."""

    categories: List[imdbapiInterestCategory] = Field(default_factory=list)


class imdbapiGetInterestResponse(BaseModel):
    """Response for a single interest by ID."""

    id: Optional[str] = None
    name: Optional[str] = None
    primaryImage: Optional[imdbapiImage] = None
    description: Optional[str] = None
    isSubgenre: Optional[bool] = None
    similarInterests: Optional[List[imdbapiInterest]] = Field(default_factory=list)
