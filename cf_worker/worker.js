import { applyCdnCache } from "./cdn_cache.js";

const PRIMARY = "https://imdxapi.vercel.app"; // single origin

// Cloudflare apne internal headers incoming request me inject karta hai
// (CF-Connecting-IP, CF-Ray, CF-IPCountry, CF-Visitor, X-Forwarded-*, X-Real-IP).
// Agar yeh headers origin ko as-is forward karein to CF edge "request already
// CF se ho chuki hai" samajh ke Error 1000/1003 de deta hai. Isliye strip karo.
const CF_INJECTED_HEADERS = [
  "cf-connecting-ip",
  "cf-ray",
  "cf-ipcountry",
  "cf-visitor",
  "cf-worker",
  "x-forwarded-for",
  "x-forwarded-proto",
  "x-forwarded-host",
  "x-real-ip",
];

// Cache-Tag hierarchy — selective purging via POST /__purge.
// Har response apne data type ke tags leta hai, taaki ek tag purge karte hi
// us type ke saare cached responses invalidate ho jayen.
function getCacheTags(pathname) {
  const tags = [];
  if (/^\/titles(\/|:|$)/.test(pathname)) tags.push("titles");
  if (/^\/names(\/|:|$)/.test(pathname)) tags.push("names");
  if (/^\/search\//.test(pathname)) tags.push("search");
  if (/^\/chart\//.test(pathname)) tags.push("chart");
  if (/^\/interests/.test(pathname)) tags.push("interests");
  return tags;
}

async function fetchOrigin(url, request, origin) {
  const headers = new Headers(request.headers);
  for (const h of CF_INJECTED_HEADERS) {
    headers.delete(h);
  }
  headers.set("Host", new URL(origin).host);
  const proxyReq = new Request(url, {
    method: request.method,
    headers,
    body: request.method !== "GET" && request.method !== "HEAD" ? request.body : null,
    // Real proxy behavior: kabhi bhi redirect internally follow MAT karo.
    // Origin ka 302/Set-Cookie seedha client ko forward hota hai, client
    // redirect handle karta hai.
    redirect: "manual",
  });
  return await fetch(proxyReq);
}

function jsonError(status, message) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// POST /__purge — Workers Cache selective invalidation.
// Body (JSON): {"tags":["titles"]} | {"pathPrefixes":["/titles/"]} | {"purgeEverything":true}
// Auth: header `X-Purge-Key: <PURGE_KEY>` (env var / wrangler secret).
async function handlePurge(request, env, ctx) {
  if (request.method !== "POST") {
    return jsonError(405, "method_not_allowed");
  }
  const key = request.headers.get("X-Purge-Key");
  if (!key || key !== env.PURGE_KEY) {
    return jsonError(401, "unauthorized");
  }
  let body = {};
  try {
    body = await request.json();
  } catch (e) {
    return jsonError(400, "invalid_json");
  }
  const opts = {};
  if (body.purgeEverything) opts.purgeEverything = true;
  else {
    if (Array.isArray(body.tags)) opts.tags = body.tags;
    if (Array.isArray(body.pathPrefixes)) opts.pathPrefixes = body.pathPrefixes;
  }
  if (!opts.purgeEverything && !opts.tags && !opts.pathPrefixes) {
    return jsonError(400, "nothing_to_purge");
  }
  const result = await ctx.cache.purge(opts);
  if (!result.success) {
    return new Response(
      JSON.stringify({ error: "purge_failed", errors: result.errors }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
  return new Response(JSON.stringify({ success: true, purged: opts }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const origin = env.ORIGIN_BASE || PRIMARY;

    // Internal purge endpoint — kabhi origin ko forward nahi karta.
    if (url.pathname === "/__purge") {
      return handlePurge(request, env, ctx);
    }

    let resp;
    try {
      const target = new URL(url.pathname + url.search, origin);
      resp = await fetchOrigin(target, request, origin);
      // Cloudflare edge blocks (e.g. SSRF "DNS points to prohibited IP") return
      // 403 with an HTML error page — that's NOT a backend 403 (backend returns
      // JSON). Treat HTML 403 as origin-unreachable -> 502.
      const isCfEdgeBlock =
        resp.status === 403 &&
        (resp.headers.get("content-type") || "").includes("text/html");
      if (isCfEdgeBlock) {
        return jsonError(502, "origin_unreachable");
      }
    } catch (e) {
      return jsonError(502, "origin_unreachable");
    }

    // Apply CDN cache headers (from cdn_cache.js) — backend only computes,
    // the Worker handles edge caching. Unmatched routes pass through unchanged.
    let finalResp = applyCdnCache(request, resp);

    const respHeaders = new Headers(finalResp.headers);
    respHeaders.set("X-Origin-Server", "1");
    respHeaders.set("Access-Control-Allow-Origin", "*");
    respHeaders.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    respHeaders.set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Auth-Token, X-App-Version-Code, X-App-Version-Name");

    // Attach Cache-Tag for cacheable responses (Workers Cache selective purge).
    const tags = getCacheTags(url.pathname);
    if (tags.length > 0) {
      respHeaders.set("Cache-Tag", tags.join(","));
    }

    return new Response(finalResp.body, {
      status: finalResp.status,
      statusText: finalResp.statusText,
      headers: respHeaders,
    });
  },
};
