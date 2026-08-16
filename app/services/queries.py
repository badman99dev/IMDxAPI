"""Verified GraphQL queries against IMDb's internal API.

These query strings were taken from imdb-unofficial-api (etrnkz) and
imdbGraphQLPHP (duck7000) and verified to return real data from
`https://api.graphql.imdb.com/`.
"""

# --- Title detail (single combined call) ---
GET_TITLE_QUERY = """
query GetTitle($id: ID!) {
  title(id: $id) {
    id
    titleText { text }
    originalTitleText { text }
    titleType { text }
    isAdult
    releaseYear { year endYear }
    primaryImage { url width height }
    runtime { seconds }
    ratingsSummary { aggregateRating voteCount }
    titleGenres { genres { genre { text } } }
    plot { plotText { plainText } }
    countriesOfOrigin { countries { id text } }
    spokenLanguages { spokenLanguages { id text } }
    principalCredits {
      credits(limit: 10) {
        name { id nameText { text } }
        category { text }
      }
    }
  }
}
"""

# --- Metacritic (separate call) ---
GET_METACRITIC_QUERY = """
query Metacritic($id: ID!) {
  title(id: $id) {
    metacritic {
      url
      metascore { score reviewCount }
    }
  }
}
"""

# --- Batch titles (up to 5 via aliased subqueries) ---
def batch_titles_query(count: int) -> str:
    """Build a query that fetches `count` titles by ID via aliased subqueries."""
    parts = []
    args = []
    for i in range(count):
        args.append(f"$id{i}: ID!")
        parts.append(
            f't{i}: title(id: $id{i}) {{ id titleText {{ text }} '
            f"originalTitleText {{ text }} titleType {{ text }} "
            f"releaseYear {{ year endYear }} primaryImage {{ url width height }} "
            f"runtime {{ seconds }} "
            f"titleGenres {{ genres {{ genre {{ text }} }} }} "
            f"ratingsSummary {{ aggregateRating voteCount }} "
            f"plot {{ plotText {{ plainText }} }} "
            f"metacritic {{ url metascore {{ score reviewCount }} }} }}"
        )
    return (
        "query BatchGet(" + ", ".join(args) + ") { "
        + " ".join(parts)
        + " }"
    )



# --- Batch name enrichment (fill directors/writers/stars) ---
def batch_names_query(name_ids: list[str]) -> str:
    """Fetch full name details for the given IDs via aliased subqueries."""
    parts = []
    args = []
    for i, nid in enumerate(name_ids):
        args.append(f"$id{i}: ID!")
        parts.append(
            f'n{i}: name(id: $id{i}) {{ id nameText {{ text }} '
            f"primaryImage {{ url width height }} "
            f"akas(first: 20) {{ edges {{ node {{ text }} }} }} "
            f"primaryProfessions {{ category {{ text }} }} "
            f"birthDate {{ dateComponents {{ year month day }} }} "
            f"deathDate {{ dateComponents {{ year month day }} }} }}"
        )
    return (
        "query BatchNames(" + ", ".join(args) + ") { "
        + " ".join(parts)
        + " }"
    )


# --- Main search ---
SEARCH_QUERY = """
query Search($searchTerm: String!, $first: Int!, $after: String) {
  mainSearch(first: $first, after: $after, options: {searchTerm: $searchTerm, type: TITLE, includeAdult: true}) {
    edges {
      node {
        entity {
          ... on Title {
            id
            titleText { text }
            originalTitleText { text }
            titleType { text }
            releaseYear { year }
            primaryImage { url width height }
            ratingsSummary { aggregateRating }
          }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

# --- Advanced search (constraints/sort built dynamically in service) ---
# The `{CONSTRAINTS}` and `{SORT}` placeholders are replaced by build_advanced_query().
ADVANCED_SEARCH_QUERY = """
query AdvancedSearch($first: Int!, $after: String) {
  advancedTitleSearch(first: $first, after: $after{SORT}{CONSTRAINTS}) {
    total
    edges {
      node {
        title {
          id
          titleText { text }
          originalTitleText { text }
          titleType { text }
          releaseYear { year endYear }
          primaryImage { url width height }
          runtime { seconds }
          ratingsSummary { aggregateRating voteCount }
          plot { plotText { plainText } }
          metacritic { metascore { score } }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

# --- Name detail (combined) ---
GET_NAME_QUERY = """
query GetName($id: ID!) {
  name(id: $id) {
    id
    nameText { text }
    primaryImage { url width height }
    birthDate { dateComponents { day month year } }
    deathDate { dateComponents { day month year } }
    bios(first: 5) { edges { node { text { plainText } } } }
    birthLocation { text }
    deathLocation { text }
    deathCause { text }
    birthName { text }
    height { measurement { value } }
    knownFor(first: 10) {
      edges { node { ... on NameKnownFor { title { id titleText { text } } } } }
    }
    primaryProfessions {
      category { text }
    }
    akas(first: 50) { edges { node { text } } }
    meterRanking { currentRank rankChange { changeDirection difference } }
  }
}
"""
