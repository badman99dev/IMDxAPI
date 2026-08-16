"""Title service: maps IMDb GraphQL responses to Tiffara title models."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from ..config import settings
from ..schemas.common import (
    imdbapiCountry,
    imdbapiImage,
    imdbapiInterest,
    imdbapiLanguage,
    imdbapiMetacritic,
    imdbapiRating,
)
from ..schemas.name import imdbapiName
from ..schemas.params import SortOrder, TitleSortBy
from ..schemas.title import (
    imdbapiBatchGetTitlesResponse,
    imdbapiListTitlesResponse,
    imdbapiSearchTitlesResponse,
    imdbapiTitle,
    imdbapiTitleSummary,
)
from . imdb_client import ImdbClient
from . import queries

# --- IMDb titleType.text -> Tiffara title type mapping ----
TYPE_MAP = {
    "Movie": "movie",
    "TV Series": "tvSeries",
    "TV Mini Series": "tvMiniSeries",
    "TV Movie": "tvMovie",
    "TV Special": "tvSpecial",
    "TV Episode": "tvEpisode",
    "Short": "short",
    "Video": "video",
    "Video Game": "videoGame",
    "Podcast Series": "podcastSeries",
    "Podcast Episode": "podcastEpisode",
    "Music Video": "musicVideo",
    "Music": "music",
    "Documentary": "documentary",
    "Radio Series": "radioSeries",
    "Radio Episode": "radioEpisode",
    "TV Short": "tvShort",
    "Theatre": "theatre",
}

# IMDb two-letter code -> ISO 639-3 (Tiffara language codes)
LANG_MAP = {
    "en": "eng", "ja": "jpn", "fr": "fra", "de": "deu", "es": "spa",
    "it": "ita", "pt": "por", "ru": "rus", "zh": "zho", "hi": "hin",
    "ko": "kor", "ar": "ara", "nl": "nld", "sv": "swe", "da": "dan",
    "no": "nor", "fi": "fin", "pl": "pol", "tr": "tur", "el": "ell",
    "he": "heb", "th": "tha", "vi": "vie", "id": "ind", "ms": "msa",
    "uk": "ukr", "cs": "ces", "hu": "hun", "ro": "ron", "bg": "bul",
    "bn": "ben", "ta": "tam", "te": "tel", "pa": "pan", "ur": "urd",
    "fa": "fas", "sw": "swa",
}

# --- Sort mapping: Tiffara sortBy -> GraphQL sort enum ----#
SORT_FIELD_MAP = {
    TitleSortBy.SORT_BY_POPULARITY: "POPULARITY",
    TitleSortBy.SORT_BY_RELEASE_DATE: "RELEASE_DATE",
    TitleSortBy.SORT_BY_USER_RATING: "USER_RATING",
    TitleSortBy.SORT_BY_USER_RATING_COUNT: "USER_RATING_COUNT",
    TitleSortBy.SORT_BY_YEAR: "YEAR",
}

# --- Tiffara types enum -> GraphQL titleType ids ---
# Accepts uppercase enum (MOVIE, TV_SERIES...), camelCase (tvSeries...) and
# any casing that maps to a known GraphQL title type id.
TYPES_FILTER_MAP = {
    "MOVIE": "movie",
    "TV_SERIES": "tvSeries",
    "TV_MINI_SERIES": "tvMiniSeries",
    "TV_SPECIAL": "tvSpecial",
    "TV_MOVIE": "tvMovie",
    "SHORT": "short",
    "VIDEO": "video",
    "VIDEO_GAME": "videoGame",
    "movie": "movie",
    "tvSeries": "tvSeries",
    "tvMiniSeries": "tvMiniSeries",
    "tvSpecial": "tvSpecial",
    "tvMovie": "tvMovie",
    "short": "short",
    "video": "video",
    "videoGame": "videoGame",
}

# Default type filter Tiffara always injects when `types` is absent.
DEFAULT_TITLE_TYPES = ["movie", "tvSeries", "tvMiniSeries", "tvMovie", "tvSpecial", "short"]


def _map_type_filter(raw: str) -> Optional[str]:
    """Map a Tiffara types value to its GraphQL titleType id (case-insensitive)."""
    key = raw.strip()
    if key in TYPES_FILTER_MAP:
        return TYPES_FILTER_MAP[key]
    # best-effort camelCase/spaced forms (e.g. "TV Mini Series")
    normalized = key.replace(" ", "_").replace("-", "_").upper()
    return TYPES_FILTER_MAP.get(normalized) or TYPES_FILTER_MAP.get(key.lower())


def _map_type(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return TYPE_MAP.get(raw, raw.lower())


def _to_image(data: Optional[Dict]) -> Optional[imdbapiImage]:
    if not data:
        return None
    return imdbapiImage(url=data.get("url"), width=data.get("width"), height=data.get("height"))


def _to_name(data: Optional[Dict], minimal: bool = True) -> Optional[imdbapiName]:
    """Build an imdbapiName from a principal credit entry."""
    if not data:
        return None
    if minimal:
        return imdbapiName(id=data.get("id"), displayName=(data.get("nameText") or {}).get("text"))
    name = imdbapiName(id=data.get("id"), displayName=(data.get("nameText") or {}).get("text"))
    if data.get("primaryImage"):
        name.primaryImage = _to_image(data["primaryImage"])
    akas = []
    for edge in (data.get("akas") or {}).get("edges", []):
        text = (edge.get("node") or {}).get("text")
        if text:
            akas.append(text)
    if akas:
        name.alternativeNames = akas
    professions = []
    for p in data.get("primaryProfessions") or []:
        cat = p.get("category") or {}
        text = cat.get("id") or (cat.get("text") or "").lower()
        if text:
            professions.append(text)
    professions.sort()
    if professions:
        name.primaryProfessions = professions
    return name


async def _enrich_names(client: ImdbClient, names: List[Dict]) -> Dict[str, Dict]:
    """Fetch full name details for a list of {id, nameText} dicts."""
    ids = [n["id"] for n in names]
    if not ids:
        return {}
    query = queries.batch_names_query(ids)
    variables = {f"id{i}": ids[i] for i in range(len(ids))}
    data = await client.graphql(query, variables, "BatchNames")
    result = {}
    for i in range(len(ids)):
        node = data.get(f"n{i}")
        if node:
            result[ids[i]] = node
    return result


def _to_title(data: Optional[Dict]) -> Optional[imdbapiTitle]:
    """Map raw IMDb title GraphQL node to a Tiffara imdbapiTitle."""
    if not data:
        return None

    rating = data.get("ratingsSummary") or {}
    rating_obj = None
    if rating.get("aggregateRating") is not None:
        rating_obj = imdbapiRating(
            aggregateRating=rating.get("aggregateRating"),
            voteCount=rating.get("voteCount"),
        )

    metacritic = data.get("metacritic") or {}
    metacritic_obj = None
    ms = metacritic.get("metascore") or {}
    if ms.get("score") is not None or ms.get("reviewCount") is not None:
        metacritic_obj = imdbapiMetacritic(
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
    stars: List[imdbapiName] = []
    for pc in data.get("principalCredits") or []:
        for cred in (pc or {}).get("credits", []):
            name = _to_name(cred.get("name"), minimal=not bool((cred.get("name") or {}).get("primaryProfessions")))
            if not name:
                continue
            cat = ((cred.get("category") or {}).get("text") or "").lower()
            if cat == "director":
                directors.append(name)
            elif cat == "writer":
                writers.append(name)
            elif cat == "actor":
                stars.append(name)
    # Tiffara returns stars as the principal 'actors' with full info.
    # If GraphQL gives no actor category, fall back to other principal credits.
    if not stars:
        for pc in data.get("principalCredits") or []:
            for cred in (pc or {}).get("credits", []):
                name = _to_name(cred.get("name"), minimal=not bool((cred.get("name") or {}).get("primaryProfessions")))
                if not name:
                    continue
                cat = ((cred.get("category") or {}).get("text") or "").lower()
                if cat not in ("director", "writer", "actor"):
                    stars.append(name)

    countries = []
    for c in (data.get("countriesOfOrigin") or {}).get("countries", []):
        text = c.get("text")
        code = c.get("id")
        if text or code:
            countries.append(imdbapiCountry(code=code, name=text))
    # Tiffara lists US first when present
    countries.sort(key=lambda c: 0 if c.code == "US" else 1)

    languages = []
    for l in (data.get("spokenLanguages") or {}).get("spokenLanguages", []):
        lid = l.get("id") or ""
        text = l.get("text")
        code = LANG_MAP.get(lid, lid)
        if text or code:
            languages.append(imdbapiLanguage(code=code, name=text))

    interests = None
    interests_list = []
    for e in ((data.get("interests") or {}).get("edges") or []):
        node = e.get("node") or {}
        interest = imdbapiInterest(
            id=node.get("id"),
            name=(node.get("primaryText") or {}).get("text"),
            isSubgenre=(node.get("type") == "SUBGENRE"),
        )
        interests_list.append(interest)
    if interests_list:
        interests = interests_list

    plot = None
    if data.get("plot") and (data["plot"].get("plotText") or {}).get("plainText"):
        plot = data["plot"]["plotText"]["plainText"]

    return imdbapiTitle(
        id=data.get("id"),
        type=_map_type((data.get("titleType") or {}).get("text")),
        isAdult=data.get("isAdult") or None,
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
        stars=stars or None,
        originCountries=countries or None,
        spokenLanguages=languages or None,
        interests=interests,
    )


def _to_title_summary(data: Optional[Dict]) -> Optional[imdbapiTitleSummary]:
    """Map a raw IMDb title node to the minimal Tiffara list-item shape (10 keys).

    Matches Tiffara's /titles response: id, type, primaryTitle, originalTitle,
    primaryImage, startYear, runtimeSeconds, genres, rating, plot.
    """
    if not data:
        return None

    rating = data.get("ratingsSummary") or {}
    rating_obj = None
    if rating.get("aggregateRating") is not None:
        rating_obj = imdbapiRating(
            aggregateRating=rating.get("aggregateRating"),
            voteCount=rating.get("voteCount"),
        )

    genres = None
    genre_list = []
    for g in (data.get("titleGenres") or {}).get("genres", []):
        genre = (g or {}).get("genre") or {}
        if genre.get("text"):
            genre_list.append(genre["text"])
    if genre_list:
        genres = genre_list

    plot = None
    if data.get("plot") and (data["plot"].get("plotText") or {}).get("plainText"):
        plot = data["plot"]["plotText"]["plainText"]

    return imdbapiTitleSummary(
        id=data.get("id"),
        type=_map_type((data.get("titleType") or {}).get("text")),
        primaryTitle=(data.get("titleText") or {}).get("text"),
        originalTitle=(data.get("originalTitleText") or {}).get("text"),
        primaryImage=_to_image(data.get("primaryImage")),
        startYear=(data.get("releaseYear") or {}).get("year"),
        runtimeSeconds=((data.get("runtime") or {}).get("seconds")),
        genres=genres,
        rating=rating_obj,
        plot=plot,
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
    genres=None, types=None, name_ids=None, country_codes=None,
    language_codes=None, interest_ids=None, start_year=None, end_year=None,
    min_rating=None, max_rating=None, min_votes=None, max_votes=None,
) -> str:
    """Build advanced search constraints from Tiffara filter params.

    Mirrors Tiffara's GraphQL mapping (verified against api.graphql.imdb.com):
      - types           -> titleTypeConstraint.anyTitleTypeIds
      - genres          -> genreConstraint.allGenreIds        (AND, exact case)
      - country_codes   -> originCountryConstraint.allCountries (AND)
      - language_codes  -> languageConstraint.allLanguages      (AND)
      - interest_ids    -> interestConstraint.allInterestIds    (AND)
      - name_ids        -> creditedNameConstraint.anyNameIds
      - start/end_year  -> releaseDateConstraint.releaseDateRange
      - min/max_rating  -> userRatingsConstraint.aggregateRatingRange
      - min/max_votes   -> userRatingsConstraint.ratingsCountRange
    """
    parts = []

    if types:
        graphql_types = [_map_type_filter(t) for t in types]
        graphql_types = [t for t in graphql_types if t]
    else:
        graphql_types = list(DEFAULT_TITLE_TYPES)
    if graphql_types:
        joined = '","'.join(graphql_types)
        parts.append(f'titleTypeConstraint: {{ anyTitleTypeIds: ["{joined}"] }}')

    if genres:
        joined = '","'.join(genres)
        parts.append(f'genreConstraint: {{ allGenreIds: ["{joined}"] }}')

    if country_codes:
        joined = '","'.join(country_codes)
        parts.append(f'originCountryConstraint: {{ allCountries: ["{joined}"] }}')

    if language_codes:
        joined = '","'.join(language_codes)
        parts.append(f'languageConstraint: {{ allLanguages: ["{joined}"] }}')

    if interest_ids:
        joined = '","'.join(interest_ids)
        parts.append(f'interestConstraint: {{ allInterestIds: ["{joined}"] }}')

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
        parts.append(f"userRatingsConstraint: {{ ratingsCountRange: {{ {', '.join(votes_parts)} }} }}")

    return " ".join(filter(None, parts))


async def get_title(client: ImdbClient, title_id: str) -> Optional[imdbapiTitle]:
    """Fetch a single title by ID with a combined call, plus metacritic & name enrichment."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(queries.GET_TITLE_QUERY, {"id": tid}, "GetTitle")
    title_data = data.get("title")
    if not title_data or not (title_data.get("titleText") or {}).get("text"):
        return None

    # Fetch metacritic separately
    mc_data = await client.graphql(queries.GET_METACRITIC_QUERY, {"id": tid}, "Metacritic")
    title_data["metacritic"] = (mc_data.get("title") or {}).get("metacritic")

    # Collect principal name IDs for enrichment
    people = []
    for pc in title_data.get("principalCredits") or []:
        for cred in (pc or {}).get("credits", []):
            nm = cred.get("name") or {}
            if nm.get("id"):
                people.append(nm)
    if people:
        enriched = await _enrich_names(client, people)
        for i, pc in enumerate(title_data.get("principalCredits") or []):
            for cred in (pc or {}).get("credits", []):
                nm = cred.get("name") or {}
                if nm.get("id") in enriched:
                    cred["name"] = enriched[nm["id"]]

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
        country_codes=country_codes,
        language_codes=language_codes,
        interest_ids=interest_ids,
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
        sort_order or SortOrder.ASC,
        constraints,
    )
    count_query = _apply_sort_and_constraints(
        queries.ADVANCED_COUNT_QUERY,
        sort_by or TitleSortBy.SORT_BY_POPULARITY,
        sort_order or SortOrder.ASC,
        constraints,
    )
    if not page_token:
        # IMDb's mock `total` differs when `after` is present (even null).
        # Tiffara computes the count on the first page WITHOUT an `after` arg.
        # Remove both the arg and its unused variable declaration.
        count_query = count_query.replace(", after: $after", ",")
        count_query = count_query.replace("$first: Int!, $after: String", "$first: Int!")
    variables: Dict[str, Any] = {"first": min(limit, settings.MAX_PAGE_SIZE)}
    if page_token:
        variables["after"] = page_token

    # Total count comes from a dedicated count query with first:1 (mirrors Tiffara).
    # NOTE: do NOT pass `after` on the first page (even None) — it changes the
    # mock `total` reported by the GraphQL endpoint.
    count_variables: Dict[str, Any] = {"first": 1}
    if page_token:
        count_variables["after"] = page_token
    (count_data, data) = await asyncio.gather(
        client.graphql(count_query, count_variables, "AdvancedSearchCount"),
        client.graphql(query, variables, "AdvancedSearch"),
    )
    adv = data.get("advancedTitleSearch") or {}
    edges = adv.get("edges") or []
    titles = [_to_title_summary((e.get("node") or {}).get("title")) for e in edges]
    titles = [t for t in titles if t]

    next_token = None
    page_info = adv.get("pageInfo") or {}
    if page_info.get("hasNextPage"):
        next_token = page_info.get("endCursor")

    total = ((count_data.get("advancedTitleSearch") or {}).get("total")
             or (adv.get("total") if adv.get("total") else None))
    return imdbapiListTitlesResponse(
        titles=titles,
        totalCount=total,
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