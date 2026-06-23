import { getUsers, timingSafeEqual } from "../functions/_lib/users.js";
import {
  createSessionCookie,
  setCookieHeader,
  getSession,
  requireLogin,
  requireOwner,
} from "../functions/_lib/auth.js";
import { loadHistory, loadRegistry, saveRegistry } from "../functions/_lib/kv.js";
import { generateResponse } from "../functions/_lib/ai.js";

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...extraHeaders },
  });
}

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    const method = request.method;

    if (pathname === "/api/auth/login" && method === "POST") {
      const data = await request.json().catch(() => ({}));
      const username = (data.username || "").trim().toLowerCase();
      const password = data.password || "";
      const user = getUsers(env)[username];
      if (!user || !timingSafeEqual(password, user.password)) {
        return json({ error: "invalid credentials" }, 401);
      }
      const cookie = await createSessionCookie(env, {
        user: username,
        role: user.role,
        display_name: user.display_name,
      });
      return json(
        { username, role: user.role, display_name: user.display_name },
        200,
        { "Set-Cookie": setCookieHeader("session", cookie, { secure: true, maxAge: 60 * 60 * 24 * 30 }) }
      );
    }

    if (pathname === "/api/auth/logout" && method === "POST") {
      return json({ ok: true }, 200, { "Set-Cookie": setCookieHeader("session", "", { maxAge: 0 }) });
    }

    if (pathname === "/api/auth/me" && method === "GET") {
      const session = await getSession({ request, env });
      if (!session) return json({ authenticated: false });
      return json({
        authenticated: true,
        username: session.user,
        role: session.role,
        display_name: session.display_name,
      });
    }

    if (pathname === "/api/chat" && method === "POST") {
      const { session, error } = await requireLogin({ request, env });
      if (error) return error;
      const data = await request.json().catch(() => ({}));
      const message = (data.message || "").trim();
      if (!message) return json({ error: "message is required" }, 400);
      try {
        const reply = await generateResponse(env, session.user, session.display_name, message);
        return json({ reply });
      } catch (err) {
        return json({ error: err.message }, 500);
      }
    }

    if (pathname === "/api/chat/history" && method === "GET") {
      const { session, error } = await requireLogin({ request, env });
      if (error) return error;
      return json(await loadHistory(env, session.user));
    }

    if (pathname === "/api/tools" && method === "GET") {
      const { error } = await requireLogin({ request, env });
      if (error) return error;
      return json(await loadRegistry(env));
    }

    if (pathname === "/api/tools/pending" && method === "GET") {
      const { error } = await requireLogin({ request, env });
      if (error) return error;
      const registry = await loadRegistry(env);
      return json(registry.filter((t) => !t.approved && !t.rejected));
    }

    const approveMatch = pathname.match(/^\/api\/tools\/([^/]+)\/approve$/);
    if (approveMatch && method === "POST") {
      const { error } = await requireOwner({ request, env });
      if (error) return error;
      const registry = await loadRegistry(env);
      const tool = registry.find((t) => t.tool_id === approveMatch[1]);
      if (!tool) return json({ error: "tool not found" }, 404);
      tool.approved = true;
      tool.rejected = false;
      tool.rejection_reason = null;
      await saveRegistry(env, registry);
      return json(tool);
    }

    const rejectMatch = pathname.match(/^\/api\/tools\/([^/]+)\/reject$/);
    if (rejectMatch && method === "POST") {
      const { error } = await requireOwner({ request, env });
      if (error) return error;
      const data = await request.json().catch(() => ({}));
      const registry = await loadRegistry(env);
      const tool = registry.find((t) => t.tool_id === rejectMatch[1]);
      if (!tool) return json({ error: "tool not found" }, 404);
      tool.approved = false;
      tool.rejected = true;
      tool.rejection_reason = data.reason || null;
      await saveRegistry(env, registry);
      return json(tool);
    }

    if (pathname.startsWith("/api/")) {
      return json({ error: "not found" }, 404);
    }

    return env.ASSETS.fetch(request);
  },
};
