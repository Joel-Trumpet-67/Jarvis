import { requireLogin } from "../../_lib/auth.js";
import { loadHistory } from "../../_lib/kv.js";

export async function onRequestGet(context) {
  const { session, error } = await requireLogin(context);
  if (error) return error;

  const history = await loadHistory(context.env, session.user);
  return new Response(JSON.stringify(history), { headers: { "Content-Type": "application/json" } });
}
