# ⚡ IMDxAPI

RESTful API for movie & TV data backed by IMDb's live (reverse-engineered) GraphQL endpoint.
Request/response structure mirrors the [Tiffara IMDxAPI swagger](https://tiffara.com/imdbapi.swagger.yaml) (v2.7.12).

No API key required. Deployable on Vercel.

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docs: http://localhost:8000/docs

## Endpoints (Phase 1)

| Route | Method | Description |
|---|---|---|
| `/titles` | GET | List/filter/sort titles with cursor pagination |
| `/titles/{titleId}` | GET | Get a single title by IMDb ID |
| `/titles:batchGet` | GET | Get up to 5 titles in one call |
| `/search/titles?query=` | GET | Free-text title search |
| `/names/{nameId}` | GET | Get a person by IMDb ID |

### `/titles` filters

`types`, `genres`, `countryCodes`, `languageCodes`, `nameIds`, `interestIds`,
`startYear`, `endYear`, `minVoteCount`, `maxVoteCount`,
`minAggregateRating`, `maxAggregateRating`

Sort: `sortBy` = `SORT_BY_POPULARITY | SORT_BY_RELEASE_DATE | SORT_BY_USER_RATING | SORT_BY_USER_RATING_COUNT | SORT_BY_YEAR`, `sortOrder` = `ASC | DESC`

## Deploy to Vercel

```bash
vercel --prod
```

`vercel.json` routes everything to `api/index.py` (Mangum adapter).

## Project structure

```
app/
├── main.py              # FastAPI app + routes
├── config.py            # Settings (headers, cache, retries)
├── schemas/             # Pydantic models (Tiffara-exact)
├── services/
│   ├── imdb_client.py   # httpx GraphQL client (retry + TTL cache)
│   ├── queries.py       # Verified IMDb GraphQL queries
│   ├── title_service.py # GraphQL -> Tiffara title model
│   └── name_service.py  # GraphQL -> Tiffara name model
api/index.py             # Vercel entry (Mangum)
```

## Note

IMDb's response includes a disclaimer: public/commercial use of data via this
API is not allowed. Use for private/non-commercial purposes only.