"""Common Pydantic models shared across Title and Name schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class imdbapiPrecisionDate(BaseModel):
    """A specific date (year/month/day used for birth, death, release)."""

    year: Optional[int] = Field(None, description="The year component.")
    month: Optional[int] = Field(None, description="The month component (1-12).")
    day: Optional[int] = Field(None, description="The day component (1-31).")


class imdbapiImage(BaseModel):
    """An image associated with a person or title."""

    url: Optional[str] = Field(None, description="The image URL.")
    width: Optional[int] = Field(None, description="Width in pixels.")
    height: Optional[int] = Field(None, description="Height in pixels.")
    type: Optional[str] = Field(
        None, description='Image type, e.g. "poster", "still_frame".'
    )


class imdbapiRating(BaseModel):
    """Aggregate rating and vote count for a title."""

    aggregateRating: Optional[float] = Field(
        None, description="Average rating, typically 1-10."
    )
    voteCount: Optional[int] = Field(None, description="Total votes cast.")


class imdbapiCountry(BaseModel):
    """A country with an ISO alpha-2 code and display name."""

    code: Optional[str] = Field(
        None, description='ISO 3166-1 alpha-2 country code, e.g. "US".'
    )
    name: Optional[str] = Field(None, description="Country name in English.")


class imdbapiLanguage(BaseModel):
    """A language with an ISO 639-3 code and display name."""

    code: Optional[str] = Field(
        None, description='ISO 639-3 language code, e.g. "eng".'
    )
    name: Optional[str] = Field(None, description="Language name in English.")


class imdbapiInterest(BaseModel):
    """An interest/category associated with a title."""

    id: Optional[str] = None
    name: Optional[str] = None
    primaryImage: Optional["imdbapiImage"] = None
    description: Optional[str] = None
    isSubgenre: Optional[bool] = Field(
        None, description="True when the interest is a subgenre of another."
    )
    similarInterests: Optional[List["imdbapiInterest"]] = None


class imdbapiMetacritic(BaseModel):
    """Metacritic score and review information for a title."""

    url: Optional[str] = None
    score: Optional[int] = Field(
        None, description="Metacritic metascore, typically 0-100."
    )
    reviewCount: Optional[int] = None


class imdbapiMoney(BaseModel):
    """A monetary amount with a currency."""

    amount: Optional[float] = None
    currency: Optional[str] = None


class rpcStatus(BaseModel):
    """Standard error response body."""

    code: Optional[int] = Field(None, description="Error status code.")
    message: Optional[str] = Field(None, description="Error message.")
    details: Optional[List[dict]] = Field(
        None, description="Additional error details."
    )


imdbapiInterest.model_rebuild()
