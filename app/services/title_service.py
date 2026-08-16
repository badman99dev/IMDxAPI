"""Title service: maps IMDb GraphQL responses to Tiffara title models."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..schemas.common import (
    imdbapiCountry,
    imdbapiImage,
    imdbapiInterest,
    imdbapiLanguage,
    imdbapiMetacritic,
    imdbapiPrecisionDate,
    imdbapiRating,
)
from ..schemas.name import imdbapiName
from ..schemas.params import SortOrder, TitleSortBy
from ..schemas.title import (
    imdbapiBatchGetTitlesResponse,
    imdbapiListTitlesResponse,
    imdbapiSearchTitlesResponse,
    imdbapiTitle,
)
from ..config import settings
from . imdb_client import ImdbClient
from . import queries


# --- Sort mapping: Tiffara sortBy -> GraphQL sort field ----#
SORT_FIELD_MAP = {
    TitleSortBy.SORT_BY_POPULARITY: "POPULARITY",
    TitleSortBy.SORT_BY_RELEASE_DATE: "RELEASE_DATE",
    TitleSortBy.SORT_BY_USER_RATING: "USER_RATING",
    TitleSortBy.SORT_BY_USER_RATING_COUNT: "NUM_VOTES",
    TitleSortBy.SORT_BY_YEAR: "RELEASE_DATE",
}


def _to_image(data: Optional[Dict]) -> Optional[imdbapiImage]:
    if not data:
        return None
    return imdbapiImage(
        url=data.get("url"),
        width=data.get("width"),
        height=data.get("height"),
        type=data.get("type"),
    )


def _to_name(data: Optional[Dict]) -> Optional[imdbapiName]:
    """Build a minimal imdbapiName from a principal credit entry."""
    if not data:
        return None
    return imdbapiName(id=data.get("id"), displayName=(data.get("nameText") or {}).get("text"))


def _to_title(data: Optional[Dict]) -> Optional[imdbapiTitle]:
    """Map raw IMDb title GraphQL node to a Tiffara imdbapiTitle."""
    if not data:
        return None

    rating = data.get("ratingsSummary") or {}
    rating_obj = None
    if rating.get("aggregateRating") is not None or rating.get("voteCount") is not None:
        rating_obj = imdbapiRating(
            aggregateRating=rating.get("aggregateRating"),
            voteCount=rating.get("voteCount"),
        )

    metacritic = data.get("metacritic") or {}
    metacritic_obj = None
    ms = metacritic.get("metascore") or {}
    if metacritic.get("url") or ms.get("score") is not None:
        metacritic_obj = imdbapiMetacritic(
            url=metacritic.get("url"),
            score=ms.get("score"),
            reviewCount=ms.get("reviewCount"),
        )

    genres = []
    for g in (data.get("titleGenres") or {}).get("genres", []):
        genre = (g or {}).get("genre") or {}
        if genre.get("text"):
            genres.append(genre["text"])

    directors: List[imdbapiName] = []
    writers: List[imdbapiName] = []
    for pc in data.get("principalCredits") or []:
        for cred in (pc or {}).get("credits", []):
            name = _to_name(cred.get("name"))
            if not name:
                continue
            cat = ((cred.get("category") or {}).get("text") or "").lower()
            if cat == "director":
                directors.append(name)
            elif cat == "writer":
                writers.append(name)

    countries = [
        imdbapiCountry(id=c.get("id"), text=c.get("text"))
        for c in (data.get("countriesOfOrigin") or {}).get("countries", [])
        if c.get("text")
    ]
    languages = [
        imdbapiLanguage(id=l.get("id"), text=l.get("text"))
        for l in (data.get("spokenLanguages") or {}).get("spokenLanguages", [])
        if l.get("text")
    ]

    # Plot from different sources in different queries
    plot = None
    if data.get("plot") and (data["plot"].get("plotText") or {}).get("plainText"):
        plot = data["plot"]["plotText"]["plainText"]

    return imdbapiTitle(
        id=data.get("id"),
        type=(data.get("titleType") or {}).get("text"),
        isAdult=data.get("isAdult"),
        primaryTitle=(data.get("titleText") or {}).get("text"),
        originalTitle=(data.get("originalTitleText") or {}).get("text"),
        primaryImage=_to_image(data.get("primaryImage")),
        startYear=(data.get("releaseYear") or {}).get("year"),
        endYear=(data.get("releaseYear") or {}).get("endYear"),
        runtimeSeconds=((data.get("runtime") or {}).get("seconds")),
        genres=genres or None,
        rating=rating_obj,
        metacritic=metacritic_obj,
        plot=plot,
        directors=directors or None,
        writers=writers or None,
        stars=None,
        originCountries=countries or None,
        spokenLanguages=languages or None,
        interests=None,
    )


def _apply_sort_and_constraints(
    query: str, sort_by: TitleSortBy, sort_order: SortOrder, constraints: str
) -> str:
    """Inject sort and constraints placeholders into the advanced query."""
    sort_str = ""
    if sort_by:
        sort_order_str = "ASC" if sort_order == SortOrder.ASC else "DESC"
        enum_val = SORT_FIELD_MAP.get(sort_by, "POPULARITY")
        sort_str = f" sort: {{sortBy: {enum_val} sortOrder: {sort_order_str}}}"
    transformed = query.replace("{SORT}", sort_str)
    if constraints:
        transformed = transformed.replace("{CONSTRAINTS}", f", constraints: {{ {constraints} }}")
    else:
        transformed = transformed.replace("{CONSTRAINTS}", "")
    return transformed


def _build_constraints(
    genres=None, types=None, name_ids=None, start_year=None, end_year=None,
    min_rating=None, max_rating=None, min_votes=None, max_votes=None,
) -> str:
    """Build advanced search constraints from Tiffara filter params."""
    parts = []

    if types:
        joined = '","'.join(types)
        parts.append(f'titleTypeConstraint: {{ anyTitleTypeIds: ["{joined}"] }}')

    if genres:
        joined = '","'.join(genres)
        parts.append(f'genreConstraint: {{ allGenreIds: ["{joined}"] }}')

    if name_ids:
        ids = []
        for nid in name_ids:
            ids.append(nid if nid.startswith("nm") else f"nm{nid}")
        joined = '","'.join(ids)
        parts.append(f'creditedNameConstraint: {{ anyNameIds: ["{joined}"] }}')

    date_parts = []
    if start_year:
        date_parts.append(f'start: "{start_year}-01-01"')
    if end_year:
        date_parts.append(f'end: "{end_year}-12-31"')
    if date_parts:
        parts.append(f"releaseDateConstraint: {{ releaseDateRange: {{ {', '.join(date_parts)} }} }}")

    rating_parts = []
    if min_rating is not None:
        rating_parts.append(f"min: {min_rating}")
    if max_rating is not None:
        rating_parts.append(f"max: {max_rating}")
    if rating_parts:
        parts.append(f"userRatingsConstraint: {{ aggregateRatingRange: {{ {', '.join(rating_parts)} }} }}")

    votes_parts = []
    if min_votes is not None:
        votes_parts.append(f"min: {min_votes}")
    if max_votes is not None:
        votes_parts.append(f"max: {max_votes}")
    if votes_parts:
        parts.append(f"userRatingsConstraint: {{ numVotesRange: {{ {', '.join(votes_parts)} }} }}")

    parts.append("explicitContentConstraint: { explicitContentFilter: INCLUDE_ADULT }")
    return " ".join(filter(None, parts))


async def get_title(client: ImdbClient, title_id: str) -> Optional[imdbapiTitle]:
    """Fetch a single title by ID with a combined call, plus metacritic."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(queries.GET_TITLE_QUERY, {"id": tid}, "GetTitle")
    title_data = data.get("title")
    if not title_data or not (title_data.get("titleText") or {}).get("text"):
        return None

    # Fetch metacritic separately
    mc_data = await client.graphql(queries.GET_METACRITIC_QUERY, {"id": tid}, "Metacritic")
    title_data["metacritic"] = (mc_data.get("title") or {}).get("metacritic")

    return _to_title(title_data)


async def batch_get_titles(client: ImdbClient, title_ids: List[str]) -> imdbapiBatchGetTitlesResponse:
    """Fetch up to 5 titles in a single query."""
    ids = [t if t.startswith("tt") else f"tt{t}" for t in title_ids][: settings.MAX_BATCH_TITLES]
    query = queries.batch_titles_query(len(ids))
    variables = {f"id{i}": ids[i] for i in range(len(ids))}
    data = await client.graphql(query, variables, "BatchGet")
    titles = [_to_title(data.get(f"t{i}")) for i in range(len(ids))]
    return imdbapiBatchGetTitlesResponse(titles=[t for t in titles if t])


async def list_titles(
    client: ImdbClient,
    *,
    types=None, genres=None, country_codes=None, language_codes=None,
    name_ids=None, interest_ids=None, start_year=None, end_year=None,
    min_vote_count=None, max_vote_count=None, min_aggregate_rating=None,
    max_aggregate_rating=None, sort_by: Optional[TitleSortBy] = None,
    sort_order: Optional[SortOrder] = None, page_token: Optional[str] = None,
    limit: int = 50,
) -> imdbapiListTitlesResponse:
    """List/filter/sort titles with cursor pagination."""
    constraints = _build_constraints(
        genres=genres,
        types=types,
        name_ids=name_ids,
        start_year=start_year,
        end_year=end_year,
        min_rating=min_aggregate_rating,
        max_rating=max_aggregate_rating,
        min_votes=min_vote_count,
        max_votes=max_vote_count,
    )
    query = _apply_sort_and_constraints(
        queries.ADVANCED_SEARCH_QUERY,
        sort_by or TitleSortBy.SORT_BY_POPULARITY,
        sort_order or SortOrder.DESC,
        constraints,
    )
    variables: Dict[str, Any] = {"first": min(limit, settings.MAX_PAGE_SIZE)}
    if page_token:
        variables["after"] = page_token

    data = await client.graphql(query, variables, "AdvancedSearch")
    adv = data.get("advancedTitleSearch") or {}
    edges = adv.get("edges") or []
    titles = [_to_title((e.get("node") or {}).get("title")) for e in edges]
    titles = [t for t in titles if t]

    next_token = None
    page_info = adv.get("pageInfo") or {}
    if page_info.get("hasNextPage"):
        next_token = page_info.get("endCursor")

    return imdbapiListTitlesResponse(
        titles=titles,
        totalCount=adv.get("total"),
        nextPageToken=next_token,
    )


async def search_titles(client: ImdbClient, query: str, limit: int = 20) -> imdbapiSearchTitlesResponse:
    """Search titles by free-text query via mainSearch."""
    limit = min(limit, settings.MAX_SEARCH_LIMIT)
    data = await client.graphql(
        queries.SEARCH_QUERY,
        {"searchTerm": query, "first": limit},
        "Search",
    )
    edges = (data.get("mainSearch") or {}).get("edges") or []
    titles = []
    for e in edges:
        entity = (e.get("node") or {}).get("entity") or {}
        if not entity.get("id"):
            continue
        titles.append(_to_title(entity))
    return imdbapiSearchTitlesResponse(titles=[t for t in titles if t])
