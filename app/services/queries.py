"""Verified GraphQL queries against IMDb's internal API.

These query strings were taken from imdb-unofficial-api (etrnkz) and
imdbGraphQLPHP (duck7000) and verified to return real data from
`https://api.graphql.imdb.com/`.
"""

from typing import Optional

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
    interests(first: 20) {
      edges { node { id primaryText { text } type } }
    }
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

# --------------------------------------------------------------------------- #
# Phase-2: Title sub-endpoints (verified against api.graphql.imdb.com)
# --------------------------------------------------------------------------- #

# --- Credits (optional category filter + cursor pagination) ---
def credits_query(limit: int, after: Optional[str] = None, categories: Optional[list] = None) -> str:
    """Fetch title credits with optional category filter + pagination."""
    filter_str = ""
    if categories:
        joined = '","'.join(categories)
        filter_str = f', filter: {{categories: ["{joined}"]}}'
    after_str = f', after: "{after}"' if after else ""
    return f"""
query GetCredits($id: ID!) {{
  title(id: $id) {{
    credits(first: {limit}{after_str}{filter_str}) {{
      total
      edges {{
        node {{
          name {{
            nameText {{ text }}
            id
            primaryImage {{ url width height }}
            akas(first: 20) {{ edges {{ node {{ text }} }} }}
            primaryProfessions {{ category {{ text }} }}
          }}
          category {{ id text }}
          ... on Cast {{
            characters {{ name }}
          }}
        }}
      }}
      pageInfo {{ hasNextPage endCursor }}
    }}
  }}
}}
"""


# --- Release dates ---
GET_RELEASE_DATES_QUERY = """
query GetReleaseDates($id: ID!, $first: Int!, $after: ID) {
  title(id: $id) {
    releaseDates(first: $first, after: $after) {
      total
      edges {
        node {
          country { id text }
          day month year
          attributes { text }
        }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""


# --- AKAs ---
GET_AKAS_QUERY = """
query GetAkas($id: ID!) {
  title(id: $id) {
    akas(first: 50) {
      edges {
        node {
          text
          country { id text }
          language { id text }
          attributes { text }
        }
      }
    }
  }
}
"""


# --- Seasons ---
GET_SEASONS_QUERY = """
query GetSeasons($id: ID!) {
  title(id: $id) {
    episodes {
      displayableSeasons(first: 30) {
        total
        edges {
          node {
            season
            text
          }
        }
      }
    }
  }
}
"""


def season_totals_query(seasons: list) -> str:
    """Build an aliased query returning episode totals for each season."""
    parts = []
    for i, s in enumerate(seasons):
        parts.append(
            f's{i}: title(id: $id) {{ episodes {{ episodes(first: 1, '
            f'filter: {{includeSeasons: ["{s}"]}}) {{ total }} }} }}'
        )
    return "query GetSeasonTotals($id: ID!) { " + " ".join(parts) + " }"


# --- Episodes ---
def episodes_query(limit: int, after: Optional[str] = None, season: Optional[str] = None) -> str:
    """Fetch episodes with optional season filter + pagination."""
    filter_str = ""
    if season:
        filter_str = f', filter: {{includeSeasons: ["{season}"]}}'
    after_str = f', after: "{after}"' if after else ""
    return f"""
query GetEpisodes($id: ID!) {{
  title(id: $id) {{
    episodes {{
      episodes(first: {limit}{after_str}{filter_str}) {{
        total
        edges {{
          node {{
            id
            titleText {{ text }}
            plot {{ plotText {{ plainText }} }}
            primaryImage {{ url width height }}
            releaseDate {{ day month year }}
            runtime {{ seconds }}
            ratingsSummary {{ aggregateRating voteCount }}
            series {{
              displayableEpisodeNumber {{
                episodeNumber {{ episodeNumber text }}
                displayableSeason {{ season text }}
              }}
            }}
          }}
        }}
        pageInfo {{ hasNextPage endCursor }}
      }}
    }}
  }}
}}
"""


# --- Images (optional type filter + pagination) ---
def images_query(limit: int, after: Optional[str] = None, types: Optional[list] = None) -> str:
    """Return a query for title images with optional type filter."""
    filter_str = ""
    if types:
        joined = '","'.join(types)
        filter_str = f', filter: {{types: ["{joined}"]}}'
    after_str = f', after: "{after}"' if after else ""
    return f"""
query GetImages($id: ID!) {{
  title(id: $id) {{
    images(first: {limit}{after_str}{filter_str}) {{
      total
      edges {{
        node {{
          id
          url
          width
          height
          type
        }}
      }}
      pageInfo {{ hasNextPage endCursor }}
    }}
  }}
}}
"""


# --- Videos ---
GET_VIDEOS_QUERY = """
query GetVideos($id: ID!, $first: Int!) {
  title(id: $id) {
    primaryVideos(first: $first) {
      edges {
        node {
          id
          name { value }
          description { value }
          contentType { id }
          runtime { value }
          thumbnail { url width height }
          videoDimensions { width height }
        }
      }
    }
  }
}
"""


# --- Awards ---
def awards_query(limit: int, after: Optional[str] = None) -> str:
    """Fetch award nominations with pagination."""
    after_str = f', after: "{after}"' if after else ""
    return f"""
query GetAwards($id: ID!) {{
  title(id: $id) {{
    awardNominations(first: {limit}{after_str}) {{
      total
      edges {{
        node {{
          id
          isWinner
          winningRank
          award {{
            id
            text
            event {{ id text }}
            eventEdition {{ year }}
            category {{ text }}
          }}
          notes {{ plainText }}
          awardedEntities {{
            ... on AwardedTitles {{
              secondaryAwardNames {{
                name {{ id nameText {{ text }} primaryImage {{ url width height }} }}
              }}
            }}
            ... on AwardedNames {{
              awardNames {{
                name {{ id nameText {{ text }} primaryImage {{ url width height }} }}
              }}
            }}
          }}
        }}
      }}
      pageInfo {{ hasNextPage endCursor }}
    }}
  }}
}}
"""


# --- Awards: stats (full counts; wins filtered separately) ---
AWARDS_STATS_QUERY = """
query GetAwardsStats($id: ID!) {
  title(id: $id) {
    all: awardNominations(first: 1) { total }
    wins: awardNominations(first: 1, filter: {wins: WINS_ONLY}) { total }
  }
}
"""


# --- Parents guide ---
GET_PARENTS_GUIDE_QUERY = """
query GetParentsGuide($id: ID!) {
  title(id: $id) {
    parentsGuide {
      categories {
        category { id text }
        severity { text votedFor }
        totalSeverityVotes
        guideItems(first: 9999) {
          edges {
            node {
              isSpoiler
              text { plainText }
            }
          }
        }
      }
    }
  }
}
"""


# --- Certificates ---
GET_CERTIFICATES_QUERY = """
query GetCertificates($id: ID!) {
  title(id: $id) {
    certificates(first: 50) {
      total
      edges {
        node {
          rating
          country { id text }
          attributes { text }
        }
      }
    }
  }
}
"""


# --- Company credits (optional category filter + pagination) ---
def company_credits_query(limit: int, after: Optional[str] = None, categories: Optional[list] = None) -> str:
    """Fetch company credits with optional filter + pagination."""
    filter_str = ""
    if categories:
        joined = '","'.join(categories)
        filter_str = f', filter: {{categories: ["{joined}"]}}'
    after_str = f', after: "{after}"' if after else ""
    return f"""
query GetCompanyCredits($id: ID!) {{
  title(id: $id) {{
    companyCredits(first: {limit}{after_str}{filter_str}) {{
      total
      edges {{
        node {{
          category {{ text }}
          company {{ id companyText {{ text }} }}
          attributes {{ text }}
        }}
      }}
      pageInfo {{ hasNextPage endCursor }}
    }}
  }}
}}
"""


# --- Box office ---
GET_BOX_OFFICE_QUERY = """
query GetBoxOffice($id: ID!) {
  title(id: $id) {
    productionBudget { budget { amount currency } }
    lifetimeGross(boxOfficeArea: DOMESTIC) { total { amount currency } }
    lifetimeGrossWorld: lifetimeGross(boxOfficeArea: WORLDWIDE) { total { amount currency } }
    openingWeekendGross(boxOfficeArea: DOMESTIC) { gross { total { amount currency } } weekendEndDate }
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


# --- Phase-3: Name filmography (credits) -------------------------------- #
# Categories are raw ID strings e.g. "actor", "director", "archive_footage".
# Credit title maps to a full imdbapiTitle (genres/metacritic/originCountries).
NAME_CREDITS_QUERY = """
query NameCredits($id: ID!, $first: Int!, $after: ID, $categories: [ID!]) {
  name(id: $id) {
    credits(first: $first, after: $after, filter: {categories: $categories}) {
      total
      pageInfo { hasNextPage endCursor }
      edges { node {
        category { id text }
        title {
          id
          titleText { text }
          titleType { id }
          releaseYear { year endYear }
          primaryImage { url width height }
          ratingsSummary { aggregateRating voteCount }
          titleGenres { genres { genre { text } } }
          metacritic { metascore { score reviewCount } }
          countriesOfOrigin { countries { id text } }
        }
      } }
    }
  }
}
"""


# --- Phase-3: Name images ------------------------------------------------ #
NAME_IMAGES_QUERY = """
query NameImages($id: ID!, $first: Int!, $after: ID, $types: [ID!]) {
  name(id: $id) {
    images(first: $first, after: $after, filter: {types: $types}) {
      total
      pageInfo { hasNextPage endCursor }
      edges { node { id type url width height caption { plainText } } }
    }
  }
}
"""


# --- Phase-3: Name relationships ----------------------------------------- #
NAME_RELATIONS_QUERY = """
query NameRelations($id: ID!, $first: Int!) {
  name(id: $id) {
    relations(first: $first) {
      total
      edges { node {
        id
        relationName {
          nameText
          name { id nameText { text } primaryImage { url width height }
                akas(first: 20) { edges { node { text } } }
                primaryProfessions { category { text } } }
        }
        relationshipType { id text }
      } }
    }
    spouses {
      spouse {
        name { id nameText { text } primaryImage { url width height }
              akas(first: 20) { edges { node { text } } }
              primaryProfessions { category { text } } }
      }
      current
      attributes { text }
    }
  }
}
"""


# --- Phase-3: Name trivia ------------------------------------------------ #
NAME_TRIVIA_QUERY = """
query NameTrivia($id: ID!, $first: Int!, $after: ID) {
  name(id: $id) {
    trivia(first: $first, after: $after) {
      total
      pageInfo { hasNextPage endCursor }
      edges { node {
        id
        text { plainText }
        interestScore { usersVoted usersInterested }
      } }
    }
  }
}
"""


# --- Phase-3: StarMeter chart -------------------------------------------- #
STARMETER_QUERY = """
query StarMeter($first: Int!, $after: String) {
  topMeterNames(first: $first, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node {
      id
      nameText { text }
      primaryImage { url width height }
      birthDate { dateComponents { year month day } }
      deathDate { dateComponents { year month day } }
      height { measurement { value } }
      meterRanking { currentRank rankChange { changeDirection difference } }
    } }
  }
}
"""


# --- Phase-3: Interests -------------------------------------------------- #
INTEREST_CATEGORIES_QUERY = """
query InterestCategories($first: Int!, $after: ID) {
  interestCategories(first: $first, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node {
      id
      text
      interests(first: 50) {
        edges { node {
          id
          primaryText { text }
          type
          description { value { plainText } }
          primaryImage { url width height }
          similarInterests(first: 12) {
            edges { node { id primaryText { text } } }
          }
        } }
      }
    } }
  }
}
"""


INTEREST_QUERY = """
query Interest($id: ID!) {
  interest(id: $id) {
    id
    primaryText { text }
    type
    description { value { plainText } }
    primaryImage { url width height }
    similarInterests(first: 20) {
      edges { node { id primaryText { text } } }
    }
  }
}
"""


# --- Phase-3: Batch names ------------------------------------------------- #
BATCH_NAMES_QUERY = """
query BatchNames($ids: [ID!]!) {
  names(ids: $ids) {
    id
    nameText { text }
    primaryImage { url width height }
    akas(first: 50) { edges { node { text } } }
    primaryProfessions { category { text } }
    bios(first: 5) { edges { node { text { plainText } } } }
    birthDate { dateComponents { year month day } }
    deathDate { dateComponents { year month day } }
    birthName { text }
    birthLocation { text }
    deathLocation { text }
    deathCause { text }
    height { measurement { value } }
  }
}
"""
