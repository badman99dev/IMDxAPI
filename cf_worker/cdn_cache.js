// CDN cache controller — mirror of app/main.py CACHE_RULES (FastAPI middleware).
// The Worker (Cloudflare) handles edge caching here; the backend (Python) only
// computes. Edit rules here, NOT in the Python file (backend's controller is
// OFF by default via CDN_CACHE=false). This module ALWAYS applies — no env gate.

// URL substring rules -> edge cache TTL (seconds).
// Mirrors main.py CACHE_RULES order (first match wins).
const CDN_CACHE_RULES = [
  { pattern: /parentsGuide|\/certificates|\/akas|\/releaseDates|\/trivia|\/interests/, ttl: 86400 },
  { pattern: /\/credits|\/episodes|\/videos|\/boxOffice|batchGet|\/filmography/, ttl: 300 },
  { pattern: /\/titles\/|\/names\/|\/seasons|\/images|awardNominations|companyCredits|\/relationships|\/moreLikeThis/, ttl: 3600 },
  { pattern: /\/search\/titles|\/chart\/starmeter/, ttl: 60 },
  { pattern: /\/titles/, ttl: 300 },
];

// Paths that must NEVER be cached at the edge (Swagger UI, static files, docs).
const NO_CACHE_PATHS = [
  /^\/docs/,
  /^\/static\//,
  /^\/openapi/,
  /^\/$/,
];

function isNoCachePath(pathname) {
  return NO_CACHE_PATHS.some((p) => p.test(pathname));
}

function matchCdnRule(pathname) {
  for (const rule of CDN_CACHE_RULES) {
    if (rule.pattern.test(pathname)) return rule;
  }
  return null;
}

// Apply CDN cache headers to a response based on the request URL.
// - Browser: Cache-Control: public, max-age=0 (no browser cache).
// - CDN:     CDN-Cache-Control: max-age=<ttl>, stale-while-revalidate=<ttl>.
// - Mirrors backend middleware: only GET + status 200/404.
// - Strips Set-Cookie for cached routes (session would kill edge caching).
// - `?no-cache` / /docs / /static / /openapi / "/" force fresh (private, no-store).
// Returns the (possibly new) Response. Unmatched routes pass through untouched.
export function applyCdnCache(request, response) {
  const url = new URL(request.url);

  if (request.method !== "GET" || ![200, 404].includes(response.status)) {
    return response;
  }

  if (url.searchParams.has("no-cache") || isNoCachePath(url.pathname)) {
    const h = new Headers(response.headers);
    h.set("Cache-Control", "private, no-store");
    h.set("CDN-Cache-Control", "private, no-store");
    return new Response(response.body, { status: response.status, statusText: response.statusText, headers: h });
  }

  const rule = matchCdnRule(url.pathname);
  if (!rule) return response;

  const headers = new Headers(response.headers);

  // Browser: do NOT cache (max-age=0). CDN: cache via CDN-Cache-Control.
  // s-maxage disables stale-while-revalidate on Cloudflare, so avoid it.
  headers.set("Cache-Control", "public, max-age=0");
  headers.set("CDN-Cache-Control", `max-age=${rule.ttl}, stale-while-revalidate=${rule.ttl}`);

  // Edge caching dies with Set-Cookie present — drop it for cacheable routes.
  if (headers.has("Set-Cookie")) {
    headers.delete("Set-Cookie");
  }

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}
