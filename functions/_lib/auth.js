async function hmacSign(secret, data) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(data));
  return btoa(String.fromCharCode(...new Uint8Array(sig)));
}

export async function createSessionCookie(env, payload) {
  const body = btoa(JSON.stringify(payload));
  const sig = await hmacSign(env.SECRET_KEY, body);
  return `${body}.${sig}`;
}

export async function verifySessionCookie(env, cookieValue) {
  if (!cookieValue) return null;
  const [body, sig] = cookieValue.split(".");
  if (!body || !sig) return null;
  const expected = await hmacSign(env.SECRET_KEY, body);
  if (expected !== sig) return null;
  try {
    return JSON.parse(atob(body));
  } catch {
    return null;
  }
}

export function getCookie(request, name) {
  const header = request.headers.get("Cookie") || "";
  const match = header.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export function setCookieHeader(name, value, opts = {}) {
  const parts = [`${name}=${encodeURIComponent(value)}`, "HttpOnly", "Path=/", "SameSite=Lax"];
  if (opts.maxAge !== undefined) parts.push(`Max-Age=${opts.maxAge}`);
  if (opts.secure) parts.push("Secure");
  return parts.join("; ");
}

export async function getSession(context) {
  const cookie = getCookie(context.request, "session");
  return verifySessionCookie(context.env, cookie);
}

export async function requireLogin(context) {
  const session = await getSession(context);
  if (!session) {
    return {
      error: new Response(JSON.stringify({ error: "login required" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    };
  }
  return { session };
}

export async function requireOwner(context) {
  const { session, error } = await requireLogin(context);
  if (error) return { error };
  if (session.role !== "owner") {
    return {
      error: new Response(JSON.stringify({ error: "owner only" }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      }),
    };
  }
  return { session };
}
