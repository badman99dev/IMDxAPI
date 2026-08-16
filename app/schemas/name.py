"""Pydantic models matching the Tiffara imdbapiName schema exactly."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import (
    imdbapiImage,
    imdbapiInterest,
    imdbapiName,
    imdbapiNameMeterRanking,
    imdbapiPrecisionDate,
    imdbapiRating,
)
from .title import imdbapiTitle

# Re-exported for backward-compatible imports.
__all__ = ["imdbapiName", "imdbapiNameMeterRanking"]


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


class imdbapiNameCredit(BaseModel):
    """A credit of a person in the filmography (title + category)."""

    title: Optional[imdbapiTitle] = Field(
        None, description="The title of the credit."
    )
    category: Optional[str] = Field(None, description="Category of the credit.")


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
