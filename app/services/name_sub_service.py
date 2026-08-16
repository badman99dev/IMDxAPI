"""Service functions for Tiffara name sub-endpoints (Phase-3)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..schemas.common import imdbapiImage, imdbapiInterest, imdbapiRating
from ..schemas.name import (
    imdbapiGetInterestResponse,
    imdbapiListInterestCategoriesResponse,
    imdbapiListNameFilmographyResponse,
    imdbapiListNameImagesResponse,
    imdbapiListNameRelationshipsResponse,
    imdbapiListNameTriviaResponse,
    imdbapiListStarMetersResponse,
    imdbapiName,
    imdbapiNameCredit,
    imdbapiNameCreditTitle,
    imdbapiNameMeterRanking,
    imdbapiNameRelationship,
    imdbapiNameTrivia,
    imdbapiInterestCategory,
)
from . imdb_client import ImdbClient
from . import queries

MAX_PAGE = 50


def _page_info(data: Dict) -> Optional[str]:
    pi = data.get("pageInfo") or {}
    if pi.get("hasNextPage"):
        return pi.get("endCursor")
    return None


def _to_image(data: Dict) -> Optional[imdbapiImage]:
    if not data:
        return None
    return imdbapiImage(
        url=data.get("url"),
        width=data.get("width"),
        height=data.get("height"),
        type=data.get("type"),
    )


def _to_meter(data: Dict) -> Optional[imdbapiNameMeterRanking]:
    if not data or data.get("currentRank") is None:
        return None
    rank_change = data.get("rankChange") or {}
    return imdbapiNameMeterRanking(
        currentRank=data.get("currentRank"),
        changeDirection=rank_change.get("changeDirection"),
        difference=rank_change.get("difference"),
    )


def _to_light_name(data: Dict) -> Optional[imdbapiName]:
    if not data:
        return None
    return imdbapiName(
        id=data.get("id"),
        displayName=(data.get("nameText") or {}).get("text"),
        primaryImage=_to_image(data.get("primaryImage")),
        meterRanking=_to_meter(data.get("meterRanking")),
    )


def _to_credit_title(data: Dict) -> Optional[imdbapiNameCreditTitle]:
    if not data:
        return None
    release_year = data.get("releaseYear")
    rating = data.get("ratingsSummary") or {}
    runtime = data.get("runtime") or {}
    return imdbapiNameCreditTitle(
        id=data.get("id"),
        type=(data.get("titleType") or {}).get("id"),
        primaryTitle=(data.get("titleText") or {}).get("text"),
        primaryImage=_to_image(data.get("primaryImage")),
        startYear=release_year.get("year") if release_year else None,
        endYear=(data.get("endYear") or {}).get("year"),
        runtimeSeconds=runtime.get("seconds"),
        rating=imdbapiRating(
            aggregateRating=rating.get("aggregateRating"),
            voteCount=rating.get("voteCount"),
        )
        if rating
        else None,
        plot=(data.get("plot") or {}).get("plotText", {}).get("plainText")
        if data.get("plot")
        else None,
    )


def _to_credit(data: Dict) -> Optional[imdbapiNameCredit]:
    if not data:
        return None
    episode_count = None
    ep = data.get("episodeCredits") or {}
    total = ep.get("total")
    if total is not None:
        episode_count = total
    return imdbapiNameCredit(
        title=_to_credit_title(data.get("title")),
        category=(data.get("category") or {}).get("id"),
        characters=[c.get("name") for c in (data.get("characters") or []) if c.get("name")]
        or None,
        episodeCount=episode_count,
    )


def _to_interest(data: Dict) -> Optional[imdbapiInterest]:
    if not data:
        return None
    desc = data.get("description") or {}
    desc_text = desc.get("value", {}).get("plainText") if isinstance(desc, dict) and desc else None
    similar = data.get("similarInterests") or {}
    return imdbapiInterest(
        id=data.get("id"),
        name=(data.get("primaryText") or {}).get("text"),
        primaryImage=_to_image(data.get("primaryImage")),
        description=desc_text,
        isSubgenre=(data.get("type") == "SUBGENRE"),
        similarInterests=[
            si for si in (
                _to_interest((e.get("node") or {})) for e in (similar.get("edges") or [])
            ) if si
        ]
        or None,
    )


async def list_name_filmography(
    client: ImdbClient,
    name_id: str,
    *,
    categories: Optional[List[str]] = None,
    page_token: Optional[str] = None,
    limit: int = 50,
) -> imdbapiListNameFilmographyResponse:
    """List a name's credits (actor, director, etc.) with filter + pagination."""
    limit = min(limit, MAX_PAGE)
    data = await client.graphql(
        queries.NAME_CREDITS_QUERY,
        {
            "id": name_id,
            "first": limit,
            "after": page_token,
            "categories": categories or None,
        },
        "NameCredits",
    )
    credits_data = ((data.get("name") or {}).get("credits")) or {}
    credits = [
        c for c in (_to_credit((e.get("node") or {})) for e in (credits_data.get("edges") or []))
        if c
    ]
    return imdbapiListNameFilmographyResponse(
        credits=credits,
        totalCount=credits_data.get("total"),
        nextPageToken=_page_info(credits_data),
    )


async def list_name_images(
    client: ImdbClient,
    name_id: str,
    *,
    types: Optional[List[str]] = None,
    page_token: Optional[str] = None,
    limit: int = 50,
) -> imdbapiListNameImagesResponse:
    """List a name's images, optionally filtered by image type."""
    limit = min(limit, MAX_PAGE)
    data = await client.graphql(
        queries.NAME_IMAGES_QUERY,
        {
            "id": name_id,
            "first": limit,
            "after": page_token,
            "types": types or None,
        },
        "NameImages",
    )
    images_data = ((data.get("name") or {}).get("images")) or {}
    images = [
        i for i in (_to_image((e.get("node") or {})) for e in (images_data.get("edges") or []))
        if i
    ]
    return imdbapiListNameImagesResponse(
        images=images,
        totalCount=images_data.get("total"),
        nextPageToken=_page_info(images_data),
    )


async def get_name_relationships(
    client: ImdbClient,
    name_id: str,
    *,
    limit: int = 50,
) -> imdbapiListNameRelationshipsResponse:
    """List a person's relationships (family, spouses, etc.)."""
    limit = min(limit, MAX_PAGE)
    data = await client.graphql(
        queries.NAME_RELATIONS_QUERY,
        {"id": name_id, "first": limit},
        "NameRelations",
    )
    relations_data = ((data.get("name") or {}).get("relations")) or {}
    relationships = []
    for edge in relations_data.get("edges") or []:
        node = edge.get("node") or {}
        rel_name = node.get("relationName") or {}
        inner = rel_name.get("name") or {}
        display = (
            rel_name.get("nameText")
            or (inner.get("nameText") or {}).get("text")
            or inner.get("id")
        )
        relationships.append(
            imdbapiNameRelationship(
                name=imdbapiName(
                    id=inner.get("id"),
                    displayName=display,
                    primaryImage=_to_image(inner.get("primaryImage")),
                )
                if (inner.get("id") or display)
                else None,
                relationType=(node.get("relationshipType") or {}).get("text"),
                attributes=None,
            )
        )
    return imdbapiListNameRelationshipsResponse(relationships=relationships)


async def list_name_trivia(
    client: ImdbClient,
    name_id: str,
    *,
    page_token: Optional[str] = None,
    limit: int = 50,
) -> imdbapiListNameTriviaResponse:
    """List a person's trivia entries."""
    limit = min(limit, MAX_PAGE)
    data = await client.graphql(
        queries.NAME_TRIVIA_QUERY,
        {"id": name_id, "first": limit, "after": page_token},
        "NameTrivia",
    )
    trivia_data = ((data.get("name") or {}).get("trivia")) or {}
    entries = []
    for edge in trivia_data.get("edges") or []:
        node = edge.get("node") or {}
        score = node.get("interestScore") or {}
        entries.append(
            imdbapiNameTrivia(
                id=node.get("id"),
                text=(node.get("text") or {}).get("plainText"),
                interestCount=score.get("usersInterested"),
                voteCount=score.get("usersVoted"),
            )
        )
    return imdbapiListNameTriviaResponse(
        triviaEntries=entries,
        totalCount=trivia_data.get("total"),
        nextPageToken=_page_info(trivia_data),
    )


async def get_starmeter_chart(
    client: ImdbClient,
    *,
    page_token: Optional[str] = None,
    limit: int = 50,
) -> imdbapiListStarMetersResponse:
    """Return the IMDb StarMeter top names chart."""
    limit = min(limit, MAX_PAGE)
    data = await client.graphql(
        queries.STARMETER_QUERY,
        {"first": limit, "after": page_token},
        "StarMeter",
    )
    chart_data = data.get("topMeterNames") or {}
    names = []
    for edge in chart_data.get("edges") or []:
        node = edge.get("node") or {}
        entry = _to_light_name(node)
        if entry:
            names.append(entry)
    return imdbapiListStarMetersResponse(
        names=names,
        nextPageToken=_page_info(chart_data),
    )


async def list_interest_categories(
    client: ImdbClient,
    *,
    limit: int = 100,
) -> imdbapiListInterestCategoriesResponse:
    """List all interest categories, each with its interests."""
    limit = min(limit, 100)
    data = await client.graphql(
        queries.INTEREST_CATEGORIES_QUERY,
        {"first": limit, "after": None},
        "InterestCategories",
    )
    cats_data = data.get("interestCategories") or {}
    categories = []
    for edge in cats_data.get("edges") or []:
        node = edge.get("node") or {}
        interests = [
            i for i in (
                _to_interest((e.get("node") or {}))
                for e in ((node.get("interests") or {}).get("edges") or [])
            ) if i
        ]
        categories.append(
            imdbapiInterestCategory(
                category=node.get("text"),
                interests=interests,
            )
        )
    return imdbapiListInterestCategoriesResponse(categories=categories)


async def get_interest(
    client: ImdbClient,
    interest_id: str,
) -> Optional[imdbapiGetInterestResponse]:
    """Return a single interest by ID."""
    data = await client.graphql(
        queries.INTEREST_QUERY,
        {"id": interest_id},
        "Interest",
    )
    node = data.get("interest")
    if not node:
        return None
    interest = _to_interest(node)
    if not interest:
        return None
    return imdbapiGetInterestResponse(
        id=interest.id,
        name=interest.name,
        primaryImage=interest.primaryImage,
        description=interest.description,
        isSubgenre=interest.isSubgenre,
        similarInterests=interest.similarInterests,
    )


async def batch_get_names(
    client: ImdbClient,
    name_ids: List[str],
) -> List[imdbapiName]:
    """Fetch up to 5 names in a single query."""
    from ..config import settings

    ids = [n if n.startswith("nm") else f"nm{n}" for n in name_ids][: settings.MAX_BATCH_TITLES]
    data = await client.graphql(
        queries.BATCH_NAMES_QUERY,
        {"ids": ids},
        "BatchNames",
    )
    names = []
    for node in data.get("names") or []:
        display_name = (node.get("nameText") or {}).get("text")
        if not node.get("id"):
            continue
        entry = imdbapiName(
            id=node.get("id"),
            displayName=display_name,
            primaryImage=_to_image(node.get("primaryImage")),
            meterRanking=_to_meter(node.get("meterRanking")),
        )
        professions = []
        for p in node.get("primaryProfessions") or []:
            text = (p.get("category") or {}).get("text")
            if text:
                professions.append(text.lower())
        professions.sort()
        if professions:
            entry.primaryProfessions = professions
        names.append(entry)
    return names