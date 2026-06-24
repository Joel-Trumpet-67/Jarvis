import { requireOwner } from "../../../_lib/auth.js";
import { loadRegistry, saveRegistry } from "../../../_lib/kv.js";

export async function onRequestPost(context) {
  const { error } = await requireOwner(context);
  if (error) return error;

  const toolId = context.params.id;
  const registry = await loadRegistry(context.env);
  const tool = registry.find((t) => t.tool_id === toolId);
  if (!tool) {
    return new Response(JSON.stringify({ error: "tool not found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  }

  tool.approved = true;
  tool.rejected = false;
  tool.rejection_reason = null;
  await saveRegistry(context.env, registry);

  return new Response(JSON.stringify(tool), { headers: { "Content-Type": "application/json" } });
}
