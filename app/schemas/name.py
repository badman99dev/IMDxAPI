"""Pydantic models matching the Tiffara imdbapiName schema exactly."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import imdbapiImage, imdbapiPrecisionDate


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
