"""Service functions for Tiffara title sub-endpoints (Phase-2)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..schemas.common import (
    imdbapiCountry,
    imdbapiImage,
    imdbapiLanguage,
    imdbapiMoney,
    imdbapiPrecisionDate,
    imdbapiRating,
)
from ..schemas.name import imdbapiName
from ..schemas.sub import (
    imdbapiAKA,
    imdbapiAwardNomination,
    imdbapiAwardNominationStats,
    imdbapiBoxOffice,
    imdbapiCertificate,
    imdbapiCompany,
    imdbapiCompanyCredit,
    imdbapiCredit,
    imdbapiEpisode,
    imdbapiEvent,
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
    imdbapiOpeningWeekendGross,
    imdbapiParentsGuide,
    imdbapiParentsGuideReview,
    imdbapiParentsGuideSeverity,
    imdbapiReleaseDate,
    imdbapiSeason,
    imdbapiVideo,
    imdbapiYearsInvolved,
)
from ..schemas.title import imdbapiListTitlesResponse
from . imdb_client import ImdbClient
from . import queries
from .title_service import _to_title_summary

# IMDb parents-guide category id -> Tiffara enum
PARENTS_GUIDE_MAP = {
    "NUDITY": "SEXUAL_CONTENT",
    "SEX": "SEXUAL_CONTENT",
    "VIOLENCE": "VIOLENCE",
    "PROFANITY": "PROFANITY",
    "ALCOHOL": "ALCOHOL_DRUGS",
    "DRUGS": "ALCOHOL_DRUGS",
    "FRIGHTENING": "FRIGHTENING_INTENSE_SCENES",
}


def _page_info(data: Dict) -> Optional[str]:
    """Extract nextPageToken from a GraphQL connection's pageInfo."""
    pi = data.get("pageInfo") or {}
    if pi.get("hasNextPage"):
        return pi.get("endCursor")
    return None


def _to_date(date: Dict) -> Optional[imdbapiPrecisionDate]:
    if not date:
        return None
    return imdbapiPrecisionDate(
        year=date.get("year"), month=date.get("month"), day=date.get("day")
    )


async def list_title_credits(
    client: ImdbClient,
    title_id: str,
    categories: Optional[List[str]] = None,
    limit: int = 20,
    page_token: Optional[str] = None,
) -> imdbapiListTitleCreditsResponse:
    """List credits for a title with category filter + pagination."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    query = queries.credits_query(limit, page_token, categories)
    data = await client.graphql(query, {"id": tid}, "GetCredits")
    conn = (data.get("title") or {}).get("credits") or {}
    credits = []
    for edge in conn.get("edges") or []:
        node = edge.get("node") or {}
        name = None
        nm = node.get("name") or {}
        if nm.get("id"):
            name = imdbapiName(id=nm.get("id"), displayName=(nm.get("nameText") or {}).get("text"))
            img = nm.get("primaryImage")
            if img:
                name.primaryImage = imdbapiImage(
                    url=img.get("url"), width=img.get("width"), height=img.get("height")
                )
            akas = [(a.get("node") or {}).get("text") for a in (nm.get("akas") or {}).get("edges") or []]
            akas = [a for a in akas if a]
            if akas:
                name.alternativeNames = akas
            profs = [(p.get("category") or {}).get("id") or (p.get("category") or {}).get("text") for p in nm.get("primaryProfessions") or []]
            profs = sorted([p.lower() for p in profs if p])
            if profs:
                name.primaryProfessions = profs
        characters = None
        chars = node.get("characters") or []
        if chars:
            characters = [c.get("name") for c in chars if c.get("name")]
        credits.append(
            imdbapiCredit(
                name=name,
                category=(node.get("category") or {}).get("id"),
                characters=characters,
            )
        )
    return imdbapiListTitleCreditsResponse(
        credits=credits,
        totalCount=conn.get("total"),
        nextPageToken=_page_info(conn),
    )


async def list_title_release_dates(
    client: ImdbClient,
    title_id: str,
    limit: int = 20,
    page_token: Optional[str] = None,
) -> imdbapiListTitleReleaseDatesResponse:
    """List release dates for a title with pagination."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(
        queries.GET_RELEASE_DATES_QUERY,
        {"id": tid, "first": limit, "after": page_token},
        "GetReleaseDates",
    )
    conn = (data.get("title") or {}).get("releaseDates") or {}
    dates = []
    for edge in conn.get("edges") or []:
        node = edge.get("node") or {}
        c = node.get("country") or {}
        dates.append(
            imdbapiReleaseDate(
                country=imdbapiCountry(code=c.get("id"), name=c.get("text")),
                releaseDate=_to_date(node),
                attributes=[a.get("text") for a in node.get("attributes") or [] if a.get("text")] or None,
            )
        )
    return imdbapiListTitleReleaseDatesResponse(
        releaseDates=dates,
        nextPageToken=_page_info(conn),
    )


async def list_title_akas(
    client: ImdbClient, title_id: str
) -> imdbapiListTitleAKAsResponse:
    """List AKAs (also known as) for a title."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(queries.GET_AKAS_QUERY, {"id": tid}, "GetAkas")
    conn = (data.get("title") or {}).get("akas") or {}
    akas = []
    for edge in conn.get("edges") or []:
        node = edge.get("node") or {}
        c = node.get("country") or {}
        l = node.get("language") or {}
        akas.append(
            imdbapiAKA(
                text=node.get("text"),
                country=imdbapiCountry(code=c.get("id"), name=c.get("text")),
                language=imdbapiLanguage(code=l.get("id"), name=l.get("text")),
                attributes=[a.get("text") for a in node.get("attributes") or [] if a.get("text")] or None,
            )
        )
    return imdbapiListTitleAKAsResponse(akas=akas)


async def list_title_seasons(
    client: ImdbClient, title_id: str
) -> imdbapiListTitleSeasonsResponse:
    """List seasons for a title with per-season episode counts."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(queries.GET_SEASONS_QUERY, {"id": tid}, "GetSeasons")
    conn = (data.get("title") or {}).get("episodes") or {}
    seasons_data = (conn.get("displayableSeasons") or {})
    edges = seasons_data.get("edges") or []
    seasons = [e.get("node") or {} for e in edges]

    counts: Dict[str, int] = {}
    if seasons:
        season_list = [s.get("season") for s in seasons]
        # IMDb needs one subquery per season; sizeable series have <= 30 seasons.
        # Build a single query with one aliased subquery per season.
        query = queries.season_totals_query(season_list)
        totals = await client.graphql(query, {"id": tid}, "GetSeasonTotals")
        for i, s in enumerate(season_list):
            node = totals.get(f"s{i}") or {}
            total = ((node.get("episodes") or {}).get("episodes") or {}).get("total")
            if total:
                counts[str(s)] = total

    result = []
    for s in seasons:
        season_val = s.get("season")
        ep_count = counts.get(str(season_val))
        # IMDb posts unaired specials under season 0; fall back to text label.
        result.append(imdbapiSeason(season=season_val, episodeCount=ep_count))
    return imdbapiListTitleSeasonsResponse(seasons=result)


async def list_title_episodes(
    client: ImdbClient,
    title_id: str,
    season: Optional[str] = None,
    limit: int = 20,
    page_token: Optional[str] = None,
) -> imdbapiListTitleEpisodesResponse:
    """List episodes for a title with optional season filter + pagination."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    query = queries.episodes_query(limit, page_token, season)
    data = await client.graphql(query, {"id": tid}, "GetEpisodes")
    conn = (data.get("title") or {}).get("episodes") or {}
    ep_conn = conn.get("episodes") or {}
    episodes = []
    for edge in ep_conn.get("edges") or []:
        node = edge.get("node") or {}
        series = node.get("series") or {}
        den = series.get("displayableEpisodeNumber") or {}
        rating = node.get("ratingsSummary") or {}
        rating_obj = None
        if rating.get("aggregateRating") is not None:
            rating_obj = imdbapiRating(
                aggregateRating=rating.get("aggregateRating"), voteCount=rating.get("voteCount")
            )
        img = node.get("primaryImage")
        episodes.append(
            imdbapiEpisode(
                id=node.get("id"),
                title=(node.get("titleText") or {}).get("text"),
                primaryImage=imdbapiImage(url=img.get("url"), width=img.get("width"), height=img.get("height")) if img else None,
                season=((den.get("displayableSeason") or {}).get("season") or (den.get("displayableSeason") or {}).get("text")),
                episodeNumber=((den.get("episodeNumber") or {}).get("episodeNumber")),
                runtimeSeconds=(node.get("runtime") or {}).get("seconds"),
                plot=((node.get("plot") or {}).get("plotText") or {}).get("plainText"),
                rating=rating_obj,
                releaseDate=_to_date(node.get("releaseDate")),
            )
        )
    return imdbapiListTitleEpisodesResponse(
        episodes=episodes,
        totalCount=ep_conn.get("total"),
        nextPageToken=_page_info(ep_conn),
    )


async def list_title_images(
    client: ImdbClient,
    title_id: str,
    types: Optional[List[str]] = None,
    limit: int = 20,
    page_token: Optional[str] = None,
) -> imdbapiListTitleImagesResponse:
    """List images for a title with optional type filter + pagination."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    query = queries.images_query(limit, page_token, types)
    data = await client.graphql(query, {"id": tid}, "GetImages")
    conn = (data.get("title") or {}).get("images") or {}
    images = [
        imdbapiImage(
            url=(n := edge.get("node") or {}).get("url"),
            width=n.get("width"),
            height=n.get("height"),
            type=n.get("type"),
        )
        for edge in conn.get("edges") or []
    ]
    return imdbapiListTitleImagesResponse(
        images=images,
        totalCount=conn.get("total"),
        nextPageToken=_page_info(conn),
    )


async def list_title_videos(
    client: ImdbClient,
    title_id: str,
    limit: int = 20,
    page_token: Optional[str] = None,
) -> imdbapiListTitleVideosResponse:
    """List videos for a title."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(
        queries.GET_VIDEOS_QUERY,
        {"id": tid, "first": limit},
        "GetVideos",
    )
    conn = (data.get("title") or {}).get("primaryVideos") or {}
    videos = []
    for edge in conn.get("edges") or []:
        node = edge.get("node") or {}
        ct = node.get("contentType") or {}
        rt = node.get("runtime") or {}
        thumb = node.get("thumbnail") or {}
        dims = node.get("videoDimensions") or {}
        videos.append(
            imdbapiVideo(
                id=node.get("id"),
                type=(ct.get("id") or "").replace("amzn1.imdb.video.contenttype.", "") or None,
                name=(node.get("name") or {}).get("value"),
                description=(node.get("description") or {}).get("value"),
                primaryImage=imdbapiImage(
                    url=thumb.get("url"), width=thumb.get("width"), height=thumb.get("height")
                ) if thumb.get("url") else None,
                width=dims.get("width") or None,
                height=dims.get("height") or None,
                runtimeSeconds=rt.get("value"),
            )
        )
    return imdbapiListTitleVideosResponse(
        videos=videos,
        totalCount=len(videos),
        nextPageToken=None,
    )


async def list_title_award_nominations(
    client: ImdbClient,
    title_id: str,
    limit: int = 20,
    page_token: Optional[str] = None,
) -> imdbapiListTitleAwardNominationsResponse:
    """List award nominations for a title with pagination."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    query = queries.awards_query(limit, page_token)
    data = await client.graphql(query, {"id": tid}, "GetAwards")
    conn = (data.get("title") or {}).get("awardNominations") or {}
    awards = []
    for edge in conn.get("edges") or []:
        node = edge.get("node") or {}
        a = node.get("award") or {}
        event = a.get("event") or {}
        nominees = None
        awarded = node.get("awardedEntities") or {}
        raw_names = awarded.get("secondaryAwardNames") or awarded.get("awardNames") or []
        name_list = []
        for raw in raw_names:
            nm = raw.get("name") or {}
            if not nm.get("id"):
                continue
            person = imdbapiName(id=nm.get("id"), displayName=(nm.get("nameText") or {}).get("text"))
            img = nm.get("primaryImage")
            if img:
                person.primaryImage = imdbapiImage(
                    url=img.get("url"), width=img.get("width"), height=img.get("height")
                )
            name_list.append(person)
        if name_list:
            nominees = name_list
        awards.append(
            imdbapiAwardNomination(
                event=imdbapiEvent(id=event.get("id"), name=event.get("text")),
                year=(a.get("eventEdition") or {}).get("year"),
                text=a.get("text"),
                category=(a.get("category") or {}).get("text"),
                isWinner=node.get("isWinner"),
                winnerRank=node.get("winningRank"),
                nominees=nominees,
            )
        )
    stats = None
    try:
        sdata = await client.graphql(queries.AWARDS_STATS_QUERY, {"id": tid}, "GetAwardsStats")
        st = (sdata.get("title") or {})
        all_total = ((st.get("all") or {}).get("total")) or 0
        win_total = ((st.get("wins") or {}).get("total")) or 0
        if all_total or win_total:
            stats = imdbapiAwardNominationStats(
                nominationCount=max(all_total - win_total, 0), winCount=win_total
            )
    except Exception:
        stats = None
    return imdbapiListTitleAwardNominationsResponse(
        stats=stats,
        awardNominations=awards,
        nextPageToken=_page_info(conn),
    )


async def list_title_parents_guide(
    client: ImdbClient, title_id: str
) -> imdbapiListTitleParentsGuideResponse:
    """List parents guide categories for a title."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(queries.GET_PARENTS_GUIDE_QUERY, {"id": tid}, "GetParentsGuide")
    categories = ((data.get("title") or {}).get("parentsGuide") or {}).get("categories") or []
    guides = []
    for cat in categories:
        severity = cat.get("severity") or {}
        severity_breakdowns = []
        if severity.get("votedFor") is not None or severity.get("text"):
            severity_breakdowns.append(
                imdbapiParentsGuideSeverity(
                    severityLevel=severity.get("text") or "Unknown",
                    voteCount=severity.get("votedFor"),
                )
            )
        reviews = []
        for gi in ((cat.get("guideItems") or {}).get("edges") or []):
            gn = gi.get("node") or {}
            reviews.append(
                imdbapiParentsGuideReview(
                    text=((gn.get("text") or {}).get("plainText")),
                    isSpoiler=gn.get("isSpoiler"),
                )
            )
        cat_id = ((cat.get("category") or {}).get("id") or "").upper()
        guides.append(
            imdbapiParentsGuide(
                category=PARENTS_GUIDE_MAP.get(cat_id, cat_id or None),
                severityBreakdowns=severity_breakdowns,
                reviews=reviews,
            )
        )
    return imdbapiListTitleParentsGuideResponse(parentsGuide=guides)


async def list_title_certificates(
    client: ImdbClient, title_id: str
) -> imdbapiListTitleCertificatesResponse:
    """List content-rating certificates for a title."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(queries.GET_CERTIFICATES_QUERY, {"id": tid}, "GetCertificates")
    conn = (data.get("title") or {}).get("certificates") or {}
    certs = []
    for edge in conn.get("edges") or []:
        node = edge.get("node") or {}
        c = node.get("country") or {}
        certs.append(
            imdbapiCertificate(
                rating=node.get("rating"),
                country=imdbapiCountry(code=c.get("id"), name=c.get("text")),
                attributes=[a.get("text") for a in node.get("attributes") or [] if a.get("text")] or None,
            )
        )
    return imdbapiListTitleCertificatesResponse(
        certificates=certs, totalCount=conn.get("total")
    )


async def list_title_company_credits(
    client: ImdbClient,
    title_id: str,
    categories: Optional[List[str]] = None,
    limit: int = 20,
    page_token: Optional[str] = None,
) -> imdbapiListTitleCompanyCreditsResponse:
    """List company credits with optional category filter + pagination."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    query = queries.company_credits_query(limit, page_token, categories)
    data = await client.graphql(query, {"id": tid}, "GetCompanyCredits")
    conn = (data.get("title") or {}).get("companyCredits") or {}
    credits = []
    for edge in conn.get("edges") or []:
        node = edge.get("node") or {}
        co = node.get("company") or {}
        yi = node.get("yearsInvolved") or {}
        credits.append(
            imdbapiCompanyCredit(
                company=imdbapiCompany(
                    id=co.get("id"), name=(co.get("companyText") or {}).get("text")
                ),
                category=(node.get("category") or {}).get("text"),
                countries=[
                    imdbapiCountry(code=c.get("id"), name=c.get("text"))
                    for c in node.get("countries") or []
                    if c.get("id") or c.get("text")
                ]
                or None,
                yearsInvolved=imdbapiYearsInvolved(
                    startYear=yi.get("year"), endYear=yi.get("endYear")
                )
                if yi.get("year") or yi.get("endYear")
                else None,
                attributes=[a.get("text") for a in node.get("attributes") or [] if a.get("text")] or None,
            )
        )
    return imdbapiListTitleCompanyCreditsResponse(
        companyCredits=credits,
        totalCount=conn.get("total"),
        nextPageToken=_page_info(conn),
    )


async def get_title_box_office(
    client: ImdbClient, title_id: str
) -> Optional[imdbapiBoxOffice]:
    """Get box office information for a title."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(queries.GET_BOX_OFFICE_QUERY, {"id": tid}, "GetBoxOffice")
    t = data.get("title") or {}

    def _money(key: str) -> Optional[imdbapiMoney]:
        node = (t.get(key) or {}).get("total") if key != "productionBudget" else (t.get(key) or {}).get("budget")
        if not node:
            return None
        amount = node.get("amount")
        if amount is None:
            return None
        return imdbapiMoney(amount=str(amount), currency=node.get("currency"))

    budget = _money("productionBudget")
    domestic = _money("lifetimeGross")
    worldwide = _money("lifetimeGrossWorld")
    owg = t.get("openingWeekendGross") or {}
    owg_gross = (owg.get("gross") or {}).get("total") or {}
    opening = None
    if owg_gross.get("amount") is not None:
        weekend_end = None
        wed = owg.get("weekendEndDate")
        if isinstance(wed, str) and len(wed) >= 10:
            try:
                weekend_end = imdbapiPrecisionDate(
                    year=int(wed[0:4]), month=int(wed[5:7]), day=int(wed[8:10])
                )
            except ValueError:
                weekend_end = None
        opening = imdbapiOpeningWeekendGross(
            gross=imdbapiMoney(amount=str(owg_gross["amount"]), currency=owg_gross.get("currency")),
            weekendEndDate=weekend_end,
        )

    result = imdbapiBoxOffice(
        domesticGross=domestic,
        worldwideGross=worldwide,
        openingWeekendGross=opening,
        productionBudget=budget,
    )
    if not any([result.domesticGross, result.worldwideGross, result.openingWeekendGross, result.productionBudget]):
        return None
    return result


async def list_title_more_like_this(
    client: ImdbClient, title_id: str, limit: int = 20
) -> imdbapiListTitlesResponse:
    """List titles similar to a given title (IMDb recommendations)."""
    tid = title_id if title_id.startswith("tt") else f"tt{title_id}"
    data = await client.graphql(
        queries.GET_MORE_LIKE_THIS_QUERY, {"id": tid, "first": limit}, "GetMoreLikeThis"
    )
    edges = ((data.get("title") or {}).get("moreLikeThisTitles") or {}).get("edges") or []
    titles = []
    for edge in edges:
        node = edge.get("node") or {}
        if node.get("id") == tid:
            continue
        t = _to_title_summary(node)
        if t:
            titles.append(t)
    return imdbapiListTitlesResponse(titles=titles)