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
    """A country with an ID and display text."""

    id: Optional[str] = None
    text: Optional[str] = None


class imdbapiLanguage(BaseModel):
    """A language with an ID and display text."""

    id: Optional[str] = None
    text: Optional[str] = None


class imdbapiInterest(BaseModel):
    """An interest/category associated with a title."""

    id: Optional[str] = None
    name: Optional[str] = None


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
