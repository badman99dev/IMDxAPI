"""FastAPI application for IMDxAPI."""

from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from .config import settings
from .schemas.params import SortOrder, TitleSortBy
from .schemas.common import rpcStatus
from .schemas.title import (
    imdbapiBatchGetTitlesResponse,
    imdbapiListTitlesResponse,
    imdbapiSearchTitlesResponse,
    imdbapiTitle,
)
from .schemas.sub import (
    imdbapiBoxOffice,
    imdbapiListTitleAKAsResponse,
    imdbapiListTitleAwardNominationsResponse,
    imdbapiListTitleCertificatesResponse,
    imdbapiListTitleCompanyCreditsResponse,
    imdbapiListTitleCreditsResponse,
    imdbapiListTitleEpisodesResponse,
    imdbapiListTitleImagesResponse,
    imdbapiListTitleParentsGuideResponse,
    imdbapiListTitleReleaseDatesResponse,
    imdbapiListTitleSeasonsResponse,
    imdbapiListTitleVideosResponse,
)
from .schemas.name import imdbapiName
from .services.imdb_client import (
    ImdbClient,
    ImdbError,
    ImdbNotFoundError,
    ImdbRateLimitError,
)
from .services import title_service, name_service, title_sub_service

app = FastAPI(
    title="IMDxAPI",
    description="IMDx API for accessing movie and TV show data",
    version="2.7.12",
    contact={"name": "Telegram Group", "url": "https://t.me/imdbapi"},
)


async def get_client() -> ImdbClient:
    """Request-scoped IMDb GraphQL client."""
    client = ImdbClient()
    try:
        yield client
    finally:
        await client.close()


@app.exception_handler(ImdbNotFoundError)
async def not_found_handler(request: Request, exc: ImdbNotFoundError):
    return JSONResponse(
        status_code=404,
        content=rpcStatus(code=404, message=str(exc)).model_dump(),
    )


@app.exception_handler(ImdbRateLimitError)
async def rate_limit_handler(request: Request, exc: ImdbRateLimitError):
    return JSONResponse(
        status_code=429,
        content=rpcStatus(code=429, message="Rate limited by upstream provider").model_dump(),
    )


@app.exception_handler(ImdbError)
async def imdb_error_handler(request: Request, exc: ImdbError):
    return JSONResponse(
        status_code=502,
        content=rpcStatus(code=502, message=f"Upstream IMDb error: {exc}").model_dump(),
    )


@app.get("/", include_in_schema=False)
async def root():
    return {"name": "IMDxAPI", "version": "2.7.12", "docs": "/docs"}


# --------------------------------------------------------------------------- #
# Title endpoints
# --------------------------------------------------------------------------- #
@app.get(
    "/titles",
    response_model=imdbapiListTitlesResponse,
    response_model_exclude_none=True,
    summary="List titles",
    description="Retrieve a list of titles with optional filters.",
    tags=["Title"],
)
async def list_titles(
    types: Optional[List[str]] = Query(None),
    genres: Optional[List[str]] = Query(None),
    countryCodes: Optional[List[str]] = Query(None),
    languageCodes: Optional[List[str]] = Query(None),
    nameIds: Optional[List[str]] = Query(None),
    interestIds: Optional[List[str]] = Query(None),
    startYear: Optional[int] = Query(None),
    endYear: Optional[int] = Query(None),
    minVoteCount: Optional[int] = Query(None),
    maxVoteCount: Optional[int] = Query(None),
    minAggregateRating: Optional[float] = Query(None),
    maxAggregateRating: Optional[float] = Query(None),
    sortBy: Optional[TitleSortBy] = Query(TitleSortBy.SORT_BY_POPULARITY),
    sortOrder: Optional[SortOrder] = Query(SortOrder.DESC),
    pageToken: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=50),
    client: ImdbClient = Depends(get_client),
):
    return await title_service.list_titles(
        client,
        types=types,
        genres=genres,
        country_codes=countryCodes,
        language_codes=languageCodes,
        name_ids=nameIds,
        interest_ids=interestIds,
        start_year=startYear,
        end_year=endYear,
        min_vote_count=minVoteCount,
        max_vote_count=maxVoteCount,
        min_aggregate_rating=minAggregateRating,
        max_aggregate_rating=maxAggregateRating,
        sort_by=sortBy,
        sort_order=sortOrder,
        page_token=pageToken,
        limit=limit,
    )


@app.get(
    "/titles/{titleId}",
    response_model=imdbapiTitle,
    response_model_exclude_none=True,
    summary="Get title by ID",
    description="Retrieve a title's details using its IMDb ID.",
    tags=["Title"],
    responses={404: {"model": rpcStatus}},
)
async def get_title(titleId: str, client: ImdbClient = Depends(get_client)):
    result = await title_service.get_title(client, titleId)
    if not result:
        raise ImdbNotFoundError(f"Title {titleId} not found")
    return result


@app.get(
    "/titles/{titleId}/credits",
    response_model=imdbapiListTitleCreditsResponse,
    response_model_exclude_none=True,
    summary="List credits for a title",
    description="Retrieve the credits associated with a specific title.",
    tags=["Title"],
)
async def list_title_credits(
    titleId: str,
    categories: Optional[List[str]] = Query(None),
    pageSize: int = Query(20, ge=1, le=50),
    pageToken: Optional[str] = Query(None),
    client: ImdbClient = Depends(get_client),
):
    return await title_sub_service.list_title_credits(
        client, titleId, categories=categories, limit=pageSize, page_token=pageToken
    )


@app.get(
    "/titles/{titleId}/releaseDates",
    response_model=imdbapiListTitleReleaseDatesResponse,
    response_model_exclude_none=True,
    summary="List release dates for a title",
    description="Retrieve the release dates associated with a specific title.",
    tags=["Title"],
)
async def list_title_release_dates(
    titleId: str,
    pageSize: int = Query(20, ge=1, le=50),
    pageToken: Optional[str] = Query(None),
    client: ImdbClient = Depends(get_client),
):
    return await title_sub_service.list_title_release_dates(
        client, titleId, limit=pageSize, page_token=pageToken
    )


@app.get(
    "/titles/{titleId}/akas",
    response_model=imdbapiListTitleAKAsResponse,
    response_model_exclude_none=True,
    summary="List AKAs for a title",
    description="Retrieve the alternative titles (AKAs) associated with a specific title.",
    tags=["Title"],
)
async def list_title_akas(titleId: str, client: ImdbClient = Depends(get_client)):
    return await title_sub_service.list_title_akas(client, titleId)


@app.get(
    "/titles/{titleId}/seasons",
    response_model=imdbapiListTitleSeasonsResponse,
    response_model_exclude_none=True,
    summary="List seasons for a title",
    description="Retrieve the seasons associated with a specific title.",
    tags=["Title"],
)
async def list_title_seasons(titleId: str, client: ImdbClient = Depends(get_client)):
    return await title_sub_service.list_title_seasons(client, titleId)


@app.get(
    "/titles/{titleId}/episodes",
    response_model=imdbapiListTitleEpisodesResponse,
    response_model_exclude_none=True,
    summary="List episodes for a title",
    description="Retrieve the episodes associated with a specific title.",
    tags=["Title"],
)
async def list_title_episodes(
    titleId: str,
    season: Optional[str] = Query(None),
    pageSize: int = Query(20, ge=1, le=50),
    pageToken: Optional[str] = Query(None),
    client: ImdbClient = Depends(get_client),
):
    return await title_sub_service.list_title_episodes(
        client, titleId, season=season, limit=pageSize, page_token=pageToken
    )


@app.get(
    "/titles/{titleId}/images",
    response_model=imdbapiListTitleImagesResponse,
    response_model_exclude_none=True,
    summary="List images for a title",
    description="Retrieve the images associated with a specific title.",
    tags=["Title"],
)
async def list_title_images(
    titleId: str,
    types: Optional[List[str]] = Query(None),
    pageSize: int = Query(20, ge=1, le=50),
    pageToken: Optional[str] = Query(None),
    client: ImdbClient = Depends(get_client),
):
    return await title_sub_service.list_title_images(
        client, titleId, types=types, limit=pageSize, page_token=pageToken
    )


@app.get(
    "/titles/{titleId}/videos",
    response_model=imdbapiListTitleVideosResponse,
    response_model_exclude_none=True,
    summary="List videos for a title",
    description="Retrieve the videos associated with a specific title.",
    tags=["Title"],
)
async def list_title_videos(
    titleId: str,
    pageSize: int = Query(20, ge=1, le=50),
    pageToken: Optional[str] = Query(None),
    client: ImdbClient = Depends(get_client),
):
    return await title_sub_service.list_title_videos(
        client, titleId, limit=pageSize, page_token=pageToken
    )


@app.get(
    "/titles/{titleId}/awardNominations",
    response_model=imdbapiListTitleAwardNominationsResponse,
    response_model_exclude_none=True,
    summary="List award nominations for a title",
    description="Retrieve the award nominations associated with a specific title.",
    tags=["Title"],
)
async def list_title_award_nominations(
    titleId: str,
    pageSize: int = Query(20, ge=1, le=50),
    pageToken: Optional[str] = Query(None),
    client: ImdbClient = Depends(get_client),
):
    return await title_sub_service.list_title_award_nominations(
        client, titleId, limit=pageSize, page_token=pageToken
    )


@app.get(
    "/titles/{titleId}/parentsGuide",
    response_model=imdbapiListTitleParentsGuideResponse,
    response_model_exclude_none=True,
    summary="List parents guide for a title",
    description="Retrieve the parents guide associated with a specific title.",
    tags=["Title"],
)
async def list_title_parents_guide(
    titleId: str, client: ImdbClient = Depends(get_client)
):
    return await title_sub_service.list_title_parents_guide(client, titleId)


@app.get(
    "/titles/{titleId}/certificates",
    response_model=imdbapiListTitleCertificatesResponse,
    response_model_exclude_none=True,
    summary="List certificates for a title",
    description="Retrieve the certificates associated with a specific title.",
    tags=["Title"],
)
async def list_title_certificates(
    titleId: str, client: ImdbClient = Depends(get_client)
):
    return await title_sub_service.list_title_certificates(client, titleId)


@app.get(
    "/titles/{titleId}/companyCredits",
    response_model=imdbapiListTitleCompanyCreditsResponse,
    response_model_exclude_none=True,
    summary="List company credits for a title",
    description="Retrieve the company credits associated with a specific title.",
    tags=["Title"],
)
async def list_title_company_credits(
    titleId: str,
    categories: Optional[List[str]] = Query(None),
    pageSize: int = Query(20, ge=1, le=50),
    pageToken: Optional[str] = Query(None),
    client: ImdbClient = Depends(get_client),
):
    return await title_sub_service.list_title_company_credits(
        client, titleId, categories=categories, limit=pageSize, page_token=pageToken
    )


@app.get(
    "/titles/{titleId}/boxOffice",
    response_model=imdbapiBoxOffice,
    response_model_exclude_none=True,
    summary="Get box office information for a title",
    description="Retrieve the box office information associated with a specific title.",
    tags=["Title"],
)
async def get_title_box_office(
    titleId: str, client: ImdbClient = Depends(get_client)
):
    result = await title_sub_service.get_title_box_office(client, titleId)
    if not result:
        raise ImdbNotFoundError(f"Title {titleId} not found")
    return result


@app.get(
    "/titles:batchGet",
    response_model=imdbapiBatchGetTitlesResponse,
    response_model_exclude_none=True,
    summary="Batch get titles by IDs",
    description="Retrieve details of multiple titles using their IMDb IDs. Maximum 5 IDs.",
    tags=["Title"],
)
async def batch_get_titles(
    titleIds: Optional[List[str]] = Query(None, description="List of IMDb title IDs. Maximum 5 IDs."),
    client: ImdbClient = Depends(get_client),
):
    if not titleIds:
        return imdbapiBatchGetTitlesResponse(titles=[])
    return await title_service.batch_get_titles(client, titleIds)


# --------------------------------------------------------------------------- #
# Search endpoints
# --------------------------------------------------------------------------- #
@app.get(
    "/search/titles",
    response_model=imdbapiSearchTitlesResponse,
    response_model_exclude_none=True,
    summary="Search titles by query",
    description="Search for titles using a query string.",
    tags=["Title"],
)
async def search_titles(
    query: str = Query(..., description="The search query for titles."),
    limit: int = Query(20, ge=1, le=50, description="Maximum is 50."),
    client: ImdbClient = Depends(get_client),
):
    return await title_service.search_titles(client, query, limit)


# --------------------------------------------------------------------------- #
# Name endpoints
# --------------------------------------------------------------------------- #
@app.get(
    "/names/{nameId}",
    response_model=imdbapiName,
    response_model_exclude_none=True,
    summary="Get name by ID",
    description="Retrieve a name's details using its IMDb ID.",
    tags=["Name"],
    responses={404: {"model": rpcStatus}},
)
async def get_name(nameId: str, client: ImdbClient = Depends(get_client)):
    result = await name_service.get_name(client, nameId)
    if not result:
        raise ImdbNotFoundError(f"Name {nameId} not found")
    return result