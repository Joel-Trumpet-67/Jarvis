import { requireLogin } from "../_lib/auth.js";
import { generateResponse } from "../_lib/ai.js";

export async function onRequestPost(context) {
  const { session, error } = await requireLogin(context);
  if (error) return error;

  const data = await context.request.json().catch(() => ({}));
  const message = (data.message || "").trim();
  if (!message) {
    return new Response(JSON.stringify({ error: "message is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const reply = await generateResponse(context.env, session.user, session.display_name, message);
    return new Response(JSON.stringify({ reply }), { headers: { "Content-Type": "application/json" } });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
