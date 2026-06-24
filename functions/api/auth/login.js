import { getUsers, timingSafeEqual } from "../../_lib/users.js";
import { createSessionCookie, setCookieHeader } from "../../_lib/auth.js";

export async function onRequestPost(context) {
  const { request, env } = context;
  const data = await request.json().catch(() => ({}));
  const username = (data.username || "").trim().toLowerCase();
  const password = data.password || "";

  const users = getUsers(env);
  const user = users[username];
  if (!user || !timingSafeEqual(password, user.password)) {
    return new Response(JSON.stringify({ error: "invalid credentials" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookie = await createSessionCookie(env, {
    user: username,
    role: user.role,
    display_name: user.display_name,
  });

  return new Response(JSON.stringify({ username, role: user.role, display_name: user.display_name }), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Set-Cookie": setCookieHeader("session", cookie, { secure: true, maxAge: 60 * 60 * 24 * 30 }),
    },
  });
}
