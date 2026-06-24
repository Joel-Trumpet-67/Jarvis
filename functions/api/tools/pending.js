import { requireLogin } from "../../_lib/auth.js";
import { loadRegistry } from "../../_lib/kv.js";

export async function onRequestGet(context) {
  const { error } = await requireLogin(context);
  if (error) return error;

  const registry = await loadRegistry(context.env);
  const pending = registry.filter((t) => !t.approved && !t.rejected);
  return new Response(JSON.stringify(pending), { headers: { "Content-Type": "application/json" } });
}
