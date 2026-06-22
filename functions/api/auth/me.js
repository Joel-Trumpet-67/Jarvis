import { getSession } from "../../_lib/auth.js";

export async function onRequestGet(context) {
  const session = await getSession(context);
  if (!session) {
    return new Response(JSON.stringify({ authenticated: false }), {
      headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(
    JSON.stringify({
      authenticated: true,
      username: session.user,
      role: session.role,
      display_name: session.display_name,
    }),
    { headers: { "Content-Type": "application/json" } }
  );
}
