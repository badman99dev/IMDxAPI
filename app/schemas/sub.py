"""Pydantic models for the Tiffara title sub-endpoints (Phase-2)."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import (
    imdbapiCountry,
    imdbapiImage,
    imdbapiLanguage,
    imdbapiMoney,
    imdbapiPrecisionDate,
    imdbapiRating,
)
from .name import imdbapiName
from .title import imdbapiTitle, imdbapiListTitlesResponse


# --------------------------------------------------------------------------- #
# Credits
# --------------------------------------------------------------------------- #
class imdbapiCredit(BaseModel):
    """A credit of a person in a title."""

    title: Optional[imdbapiTitle] = Field(None, description="The title of the credit.")
    name: Optional[imdbapiName] = Field(None, description="The credited person.")
    category: Optional[str] = Field(None, description="Category of the credit.")
    characters: Optional[List[str]] = Field(
        None, description="Characters played by the person."
    )
    episodeCount: Optional[int] = Field(
        None, description="Episodes the person appeared in."
    )


class imdbapiListTitleCreditsResponse(BaseModel):
    """Response for listing credits associated with a title."""

    credits: List[imdbapiCredit] = Field(default_factory=list)
    totalCount: Optional[int] = None
    nextPageToken: Optional[str] = None


# --------------------------------------------------------------------------- #
# Release dates
# --------------------------------------------------------------------------- #
class imdbapiReleaseDate(BaseModel):
    """Release date of a title in a specific country."""

    country: Optional[imdbapiCountry] = Field(None, description="Release country.")
    releaseDate: Optional[imdbapiPrecisionDate] = Field(None, description="Release date.")
    attributes: Optional[List[str]] = Field(
        None, description="e.g. Theatrical, DVD, Blu-ray."
    )


class imdbapiListTitleReleaseDatesResponse(BaseModel):
    """Response for listing release dates associated with a title."""

    releaseDates: List[imdbapiReleaseDate] = Field(default_factory=list)
    nextPageToken: Optional[str] = None


# --------------------------------------------------------------------------- #
# AKAs (also known as)
# --------------------------------------------------------------------------- #
class imdbapiAKA(BaseModel):
    """An alternative title of a movie or TV show."""

    text: Optional[str] = Field(None, description="Display text of the AKA.")
    country: Optional[imdbapiCountry] = Field(None, description="Country of the AKA.")
    language: Optional[imdbapiLanguage] = Field(None, description="Language of the AKA.")
    attributes: Optional[List[str]] = Field(
        None, description='e.g. original title, working title.'
    )


class imdbapiListTitleAKAsResponse(BaseModel):
    """Response for listing AKAs associated with a title."""

    akas: List[imdbapiAKA] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Seasons / episodes
# --------------------------------------------------------------------------- #
class imdbapiSeason(BaseModel):
    """A season of a TV series."""

    season: Optional[str] = Field(None, description="Season identifier.")
    episodeCount: Optional[int] = Field(None, description="Episodes in the season.")


class imdbapiListTitleSeasonsResponse(BaseModel):
    """Response for listing seasons associated with a title."""

    seasons: List[imdbapiSeason] = Field(default_factory=list)


class imdbapiEpisode(BaseModel):
    """A single episode of a TV series."""

    id: Optional[str] = Field(None, description="IMDb episode ID.")
    title: Optional[str] = Field(None, description="Episode title.")
    primaryImage: Optional[imdbapiImage] = Field(None, description="Episode image.")
    season: Optional[str] = Field(None, description="Season the episode belongs to.")
    episodeNumber: Optional[int] = Field(None, description="Episode number in season.")
    runtimeSeconds: Optional[int] = Field(None, description="Runtime in seconds.")
    plot: Optional[str] = Field(None, description="Episode plot summary.")
    rating: Optional[imdbapiRating] = Field(None, description="Rating of the episode.")
    releaseDate: Optional[imdbapiPrecisionDate] = Field(
        None, description="Original air date."
    )


class imdbapiListTitleEpisodesResponse(BaseModel):
    """Response for listing episodes associated with a title."""

    episodes: List[imdbapiEpisode] = Field(default_factory=list)
    totalCount: Optional[int] = Field(None, description="Total aired episodes.")
    nextPageToken: Optional[str] = None


# --------------------------------------------------------------------------- #
# Images
# --------------------------------------------------------------------------- #
class imdbapiListTitleImagesResponse(BaseModel):
    """Response for listing images associated with a title."""

    images: List[imdbapiImage] = Field(default_factory=list)
    totalCount: Optional[int] = None
    nextPageToken: Optional[str] = None


# --------------------------------------------------------------------------- #
# Videos
# --------------------------------------------------------------------------- #
class imdbapiVideo(BaseModel):
    """A video associated with a title."""

    id: Optional[str] = Field(None, description="IMDb video ID.")
    type: Optional[str] = Field(None, description="Video type.")
    name: Optional[str] = Field(None, description="Video name.")
    primaryImage: Optional[imdbapiImage] = Field(None, description="Video thumbnail.")
    description: Optional[str] = Field(None, description="Video description.")
    width: Optional[int] = Field(None, description="Width in pixels.")
    height: Optional[int] = Field(None, description="Height in pixels.")
    runtimeSeconds: Optional[int] = Field(None, description="Runtime in seconds.")


class imdbapiListTitleVideosResponse(BaseModel):
    """Response for listing videos associated with a title."""

    videos: List[imdbapiVideo] = Field(default_factory=list)
    totalCount: Optional[int] = None
    nextPageToken: Optional[str] = None


# --------------------------------------------------------------------------- #
# Awards
# --------------------------------------------------------------------------- #
class imdbapiEvent(BaseModel):
    """An award event, e.g. Academy Awards."""

    id: Optional[str] = None
    name: Optional[str] = None


class imdbapiAwardNomination(BaseModel):
    """A nomination for an award."""

    titles: Optional[List[imdbapiTitle]] = Field(None, description="Nominated titles.")
    nominees: Optional[List[imdbapiName]] = Field(None, description="Nominated people.")
    event: Optional[imdbapiEvent] = Field(None, description="Award event.")
    year: Optional[int] = Field(None, description="Year of the award.")
    text: Optional[str] = Field(None, description="Text description of the nomination.")
    category: Optional[str] = Field(None, description="Award category.")
    isWinner: Optional[bool] = Field(None, description="Whether it won.")
    winnerRank: Optional[int] = Field(None, description="Rank of the winner.")


class imdbapiAwardNominationStats(BaseModel):
    """Aggregate award statistics for a title."""

    nominationCount: Optional[int] = None
    winCount: Optional[int] = None


class imdbapiListTitleAwardNominationsResponse(BaseModel):
    """Response for listing award nominations associated with a title."""

    stats: Optional[imdbapiAwardNominationStats] = None
    awardNominations: List[imdbapiAwardNomination] = Field(default_factory=list)
    nextPageToken: Optional[str] = None


# --------------------------------------------------------------------------- #
# Parents guide
# --------------------------------------------------------------------------- #
class imdbapiParentsGuideSeverity(BaseModel):
    """A severity vote breakdown for a parents guide category."""

    severityLevel: Optional[str] = None
    voteCount: Optional[int] = None


class imdbapiParentsGuideReview(BaseModel):
    """A parents guide review entry."""

    text: Optional[str] = None
    isSpoiler: Optional[bool] = None


class imdbapiParentsGuide(BaseModel):
    """Parents guide info for a category of a title."""

    category: Optional[str] = None
    severityBreakdowns: List[imdbapiParentsGuideSeverity] = Field(default_factory=list)
    reviews: List[imdbapiParentsGuideReview] = Field(default_factory=list)


class imdbapiListTitleParentsGuideResponse(BaseModel):
    """Response for listing parents guide for a title."""

    parentsGuide: List[imdbapiParentsGuide] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Certificates
# --------------------------------------------------------------------------- #
class imdbapiCertificate(BaseModel):
    """A content rating certificate."""

    rating: Optional[str] = Field(None, description='e.g. "PG-13", "R".')
    country: Optional[imdbapiCountry] = Field(None, description="Issuing country.")
    attributes: Optional[List[str]] = Field(None, description="Additional attributes.")


class imdbapiListTitleCertificatesResponse(BaseModel):
    """Response for listing certificates associated with a title."""

    certificates: List[imdbapiCertificate] = Field(default_factory=list)
    totalCount: Optional[int] = None


# --------------------------------------------------------------------------- #
# Company credits
# --------------------------------------------------------------------------- #
class imdbapiCompany(BaseModel):
    """A production/distribution company."""

    id: Optional[str] = Field(None, description="Company ID.")
    name: Optional[str] = Field(None, description="Company name.")


class imdbapiYearsInvolved(BaseModel):
    """Years a company was involved in a project."""

    startYear: Optional[int] = None
    endYear: Optional[int] = None


class imdbapiCompanyCredit(BaseModel):
    """A company credit associated with a title."""

    company: Optional[imdbapiCompany] = Field(None, description="The company.")
    category: Optional[str] = Field(None, description="Category of the credit.")
    countries: Optional[List[imdbapiCountry]] = Field(
        None, description="Countries the company operates in."
    )
    yearsInvolved: Optional[imdbapiYearsInvolved] = Field(None, description="Years.")
    attributes: Optional[List[str]] = Field(None, description="Additional attributes.")


class imdbapiListTitleCompanyCreditsResponse(BaseModel):
    """Response for listing company credits associated with a title."""

    companyCredits: List[imdbapiCompanyCredit] = Field(default_factory=list)
    totalCount: Optional[int] = None
    nextPageToken: Optional[str] = None


# --------------------------------------------------------------------------- #
# Box office
# --------------------------------------------------------------------------- #
class imdbapiOpeningWeekendGross(BaseModel):
    """Opening weekend box office gross."""

    gross: Optional[imdbapiMoney] = None
    weekendEndDate: Optional[imdbapiPrecisionDate] = None


class imdbapiBoxOffice(BaseModel):
    """Box office information for a title."""

    domesticGross: Optional[imdbapiMoney] = Field(
        None, description="Domestic box office gross."
    )
    worldwideGross: Optional[imdbapiMoney] = Field(
        None, description="Worldwide box office gross."
    )
    openingWeekendGross: Optional[imdbapiOpeningWeekendGross] = Field(
        None, description="Opening weekend gross."
    )
    productionBudget: Optional[imdbapiMoney] = Field(
        None, description="Production budget."
    )