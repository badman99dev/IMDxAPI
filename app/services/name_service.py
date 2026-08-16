"""Name service: maps IMDb GraphQL name responses to Tiffara name models."""

from __future__ import annotations

from typing import Optional

from ..schemas.common import imdbapiImage, imdbapiPrecisionDate
from ..schemas.name import imdbapiName, imdbapiNameMeterRanking
from . imdb_client import ImdbClient
from . import queries


def _to_image(data) -> Optional[imdbapiImage]:
    if not data:
        return None
    return imdbapiImage(url=data.get("url"), width=data.get("width"), height=data.get("height"))


def _to_date(date_data) -> Optional[imdbapiPrecisionDate]:
    if not date_data:
        return None
    dc = date_data.get("dateComponents") or {}
    if not any(dc.get(k) for k in ("year", "month", "day")):
        return None
    return imdbapiPrecisionDate(
        year=dc.get("year"), month=dc.get("month"), day=dc.get("day")
    )


def _to_name(data) -> Optional[imdbapiName]:
    """Map a raw IMDb name GraphQL node to a Tiffara imdbapiName."""
    if not data:
        return None

    bios = data.get("bios") or {}
    biography = None
    for edge in (bios.get("edges") or []):
        plain = (((edge or {}).get("node") or {}).get("text") or {}).get("plainText")
        if plain:
            biography = plain
            break

    professions = []
    for p in data.get("primaryProfessions") or []:
        text = (p.get("category") or {}).get("text")
        if text:
            professions.append(text)

    akas = []
    for edge in (data.get("akas") or {}).get("edges", []):
        text = (edge.get("node") or {}).get("text")
        if text:
            akas.append(text)

    meter = data.get("meterRanking") or {}
    meter_ranking = None
    if meter.get("currentRank") is not None:
        change = meter.get("rankChange") or {}
        meter_ranking = imdbapiNameMeterRanking(
            currentRank=meter.get("currentRank"),
            changeDirection=change.get("changeDirection"),
            difference=change.get("difference"),
        )

    height_cm = None
    if data.get("height") and (data["height"].get("measurement") or {}).get("value"):
        try:
            height_cm = int(data["height"]["measurement"]["value"])
        except (ValueError, TypeError):
            height_cm = None

    birth_name = data.get("birthName")
    if isinstance(birth_name, dict):
        birth_name = birth_name.get("text")

    return imdbapiName(
        id=data.get("id"),
        displayName=(data.get("nameText") or {}).get("text"),
        primaryImage=_to_image(data.get("primaryImage")),
        primaryProfessions=professions or None,
        biography=biography,
        heightCm=height_cm,
        birthName=birth_name,
        birthDate=_to_date(data.get("birthDate")),
        birthLocation=(data.get("birthLocation") or {}).get("text"),
        deathDate=_to_date(data.get("deathDate")),
        deathLocation=(data.get("deathLocation") or {}).get("text"),
        deathReason=data.get("deathCause"),
        alternativeNames=akas or None,
        meterRanking=meter_ranking,
    )


async def get_name(client: ImdbClient, name_id: str) -> Optional[imdbapiName]:
    """Fetch a person's details by name ID."""
    nid = name_id if name_id.startswith("nm") else f"nm{name_id}"
    data = await client.graphql(queries.GET_NAME_QUERY, {"id": nid}, "GetName")
    name_data = data.get("name")
    if not name_data or not (name_data.get("nameText") or {}).get("text"):
        return None
    return _to_name(name_data)
