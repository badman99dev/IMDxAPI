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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = env.ORIGIN_BASE || PRIMARY;

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

    return new Response(finalResp.body, {
      status: finalResp.status,
      statusText: finalResp.statusText,
      headers: respHeaders,
    });
  },
};
