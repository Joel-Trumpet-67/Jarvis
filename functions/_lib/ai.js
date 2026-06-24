import { loadProfile, saveProfile, loadHistory, appendHistory, loadRegistry, saveRegistry } from "./kv.js";
import { chat } from "./llm.js";

const PROPOSE_TOOL_RE = /<propose_tool>([\s\S]*?)<\/propose_tool>/;
const MEMORY_UPDATE_RE = /<memory_update>([\s\S]*?)<\/memory_update>/;

function extractBlock(text, re) {
  const match = text.match(re);
  if (!match) return { cleaned: text, payload: null };
  let payload = null;
  try {
    payload = JSON.parse(match[1]);
  } catch {
    payload = null;
  }
  const cleaned = text.replace(match[0], "").trim();
  return { cleaned, payload };
}

function buildSystemPrompt(displayName, profile, tools) {
  const toolLines =
    tools
      .map(
        (t) =>
          `- ${t.tool_id} (${t.approved ? "approved" : t.rejected ? "rejected" : "pending approval"}): ${t.description}`
      )
      .join("\n") || "No tools registered yet.";

  const facts = (profile.facts || []).map((f) => `- ${f}`).join("\n") || "No stored facts yet.";
  const preferences = JSON.stringify(profile.preferences || {}, null, 2);

  return `You are Jarvis, a personal AI assistant for ${displayName}.

Always refer to ${displayName} by name when it feels natural. You have persistent memory of facts and preferences about ${displayName}. Reference this context naturally without being asked to.

Known facts about ${displayName}:
${facts}

Known preferences:
${preferences}

Available tools in the registry:
${toolLines}

Two special blocks you can append to the very end of your reply. Both are stripped before ${displayName} sees the message, so never mention them out loud.

1. If ${displayName} tells you to remember something, states a preference, or corrects a fact you got wrong, append exactly one block:
<memory_update>{"add_facts": ["short factual statement"], "remove_facts": ["exact old fact text to remove, only when correcting a mistake"], "preferences": {"key": "value"}}</memory_update>
Omit keys you don't need. Never repeat a fact you have already been corrected on.

2. If ${displayName} asks for something that needs a capability not in the tool registry above, write the tool yourself and append exactly one block:
<propose_tool>{"tool_id": "snake_case_id", "description": "plain English description", "code": "python function code as a string"}</propose_tool>
Never propose a tool that is already listed above, approved, pending, or rejected.
`;
}

export async function generateResponse(env, username, displayName, message) {
  const profile = await loadProfile(env, username);
  const registry = await loadRegistry(env);
  const history = (await loadHistory(env, username)).slice(-20);

  const systemPrompt = buildSystemPrompt(displayName, profile, registry);
  const messages = [
    ...history.map((h) => ({ role: h.role, content: h.content })),
    { role: "user", content: message },
  ];

  let reply = await chat(env, systemPrompt, messages);

  const memoryResult = extractBlock(reply, MEMORY_UPDATE_RE);
  reply = memoryResult.cleaned;
  if (memoryResult.payload) {
    const { add_facts = [], remove_facts = [], preferences = {} } = memoryResult.payload;
    profile.facts = (profile.facts || []).filter((f) => !remove_facts.includes(f));
    for (const f of add_facts) {
      if (!profile.facts.includes(f)) profile.facts.push(f);
    }
    profile.preferences = { ...(profile.preferences || {}), ...preferences };
    await saveProfile(env, username, profile);
  }

  const toolResult = extractBlock(reply, PROPOSE_TOOL_RE);
  reply = toolResult.cleaned;
  const toolPayload = toolResult.payload;
  if (toolPayload && toolPayload.tool_id && toolPayload.description && toolPayload.code) {
    const exists = registry.some((t) => t.tool_id === toolPayload.tool_id);
    if (!exists) {
      registry.push({
        tool_id: toolPayload.tool_id,
        description: toolPayload.description,
        code: toolPayload.code,
        approved: false,
        rejected: false,
        rejection_reason: null,
      });
      await saveRegistry(env, registry);
    }
  }

  await appendHistory(env, username, "user", message);
  await appendHistory(env, username, "assistant", reply);

  return reply;
}
