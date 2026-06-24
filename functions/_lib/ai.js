import { loadProfile, saveProfile, loadHistory, appendHistory, loadRegistry, saveRegistry, loadList, saveList } from "./kv.js";
import { chat } from "./llm.js";
import { getWeather } from "./weather.js";

const PROPOSE_TOOL_RE = /<propose_tool>([\s\S]*?)<\/propose_tool>/;
const MEMORY_UPDATE_RE = /<memory_update>([\s\S]*?)<\/memory_update>/;
const DATA_UPDATE_RE = /<data_update>([\s\S]*?)<\/data_update>/;
const ACTION_RE = /<action>([\s\S]*?)<\/action>/;

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

function buildSystemPrompt(displayName, profile, tools, lists, weather) {
  const toolLines =
    tools
      .map(
        (t) =>
          `- ${t.tool_id} (${t.approved ? "approved" : t.rejected ? "rejected" : "pending approval"}): ${t.description}`
      )
      .join("\n") || "No tools registered yet.";

  const facts = (profile.facts || []).map((f) => `- ${f}`).join("\n") || "No stored facts yet.";
  const preferences = JSON.stringify(profile.preferences || {}, null, 2);

  const notesLines = lists.notes.map((n) => `- [${n.id}] ${n.text}`).join("\n") || "None.";
  const tasksLines =
    lists.tasks.map((t) => `- [${t.id}] ${t.done ? "(done) " : ""}${t.text}${t.due ? ` (due ${t.due})` : ""}`).join("\n") ||
    "None.";
  const goalsLines = lists.goals.map((g) => `- [${g.id}] ${g.text}`).join("\n") || "None.";
  const shoppingLines = lists.shopping.map((s) => `- [${s.id}] ${s.text}`).join("\n") || "None.";
  const remindersLines =
    lists.reminders.map((r) => `- [${r.id}] ${r.text}${r.due ? ` (due ${r.due})` : ""}`).join("\n") || "None.";

  const weatherLine = weather
    ? `Current weather: ${weather.temperatureF}°F, ${weather.condition}, wind ${weather.windSpeedMph}mph.`
    : "Current weather: not available (no location shared this session).";

  return `You are Jarvis, a personal AI assistant for ${displayName}.

Always refer to ${displayName} by name when it feels natural. You have persistent memory of facts and preferences about ${displayName}. Reference this context naturally without being asked to.

Known facts about ${displayName}:
${facts}

Known preferences:
${preferences}

${weatherLine}

Notes:
${notesLines}

Tasks:
${tasksLines}

Goals:
${goalsLines}

Shopping list:
${shoppingLines}

Reminders:
${remindersLines}

Available tools in the registry:
${toolLines}

Special blocks you can append to the very end of your reply. All are stripped before ${displayName} sees the message, so never mention them out loud. Use at most one of each kind per reply, only when actually needed.

1. Memory: when ${displayName} tells you to remember something, states a preference, or corrects a fact you got wrong:
<memory_update>{"add_facts": ["short factual statement"], "remove_facts": ["exact old fact text to remove, only when correcting a mistake"], "preferences": {"key": "value"}}</memory_update>
Omit keys you don't need. Never repeat a fact you have already been corrected on.

2. Data: to add/complete/remove notes, tasks, goals, shopping items, or reminders (reference existing items by the [id] shown above):
<data_update>{"notes_add": ["text"], "notes_remove": ["id"], "tasks_add": [{"text": "text", "due": "YYYY-MM-DD or null"}], "tasks_complete": ["id"], "tasks_remove": ["id"], "goals_add": ["text"], "goals_remove": ["id"], "shopping_add": ["text"], "shopping_remove": ["id"], "reminders_add": [{"text": "text", "due": "ISO datetime or null"}], "reminders_remove": ["id"]}</data_update>
Omit keys you don't need.

3. Action: to trigger something on ${displayName}'s phone right now:
<action>{"type": "tel"|"sms"|"maps"|"mail"|"facetime"|"shortcut"|"vibrate"|"clipboard"|"share", "value": "string"}</action>
- tel/sms/facetime: value is the phone number. mail: value is the email address (or "address?subject=...&body=..."). maps: value is a place/address query.
- shortcut: value is the exact name of an iOS Shortcut to run (for HomeKit, alarms, calendar, WiFi, automations).
- vibrate: value can be empty.
- clipboard: value is the text to copy.
- share: value is the text to share via the share sheet.
Only emit this when ${displayName} explicitly asked for that action.

4. Tool proposal: if ${displayName} asks for something that needs a capability not in the tool registry above, write the tool yourself and append exactly one block:
<propose_tool>{"tool_id": "snake_case_id", "description": "plain English description", "code": "python function code as a string"}</propose_tool>
Never propose a tool that is already listed above, approved, pending, or rejected.
`;
}

function applyDataUpdate(lists, payload) {
  const id = () => Math.random().toString(36).slice(2, 10);

  if (Array.isArray(payload.notes_add)) {
    for (const text of payload.notes_add) lists.notes.push({ id: id(), text, created_at: Date.now() });
  }
  if (Array.isArray(payload.notes_remove)) {
    lists.notes = lists.notes.filter((n) => !payload.notes_remove.includes(n.id));
  }

  if (Array.isArray(payload.tasks_add)) {
    for (const t of payload.tasks_add) {
      lists.tasks.push({ id: id(), text: t.text, due: t.due || null, done: false, created_at: Date.now() });
    }
  }
  if (Array.isArray(payload.tasks_complete)) {
    for (const t of lists.tasks) if (payload.tasks_complete.includes(t.id)) t.done = true;
  }
  if (Array.isArray(payload.tasks_remove)) {
    lists.tasks = lists.tasks.filter((t) => !payload.tasks_remove.includes(t.id));
  }

  if (Array.isArray(payload.goals_add)) {
    for (const text of payload.goals_add) lists.goals.push({ id: id(), text, created_at: Date.now() });
  }
  if (Array.isArray(payload.goals_remove)) {
    lists.goals = lists.goals.filter((g) => !payload.goals_remove.includes(g.id));
  }

  if (Array.isArray(payload.shopping_add)) {
    for (const text of payload.shopping_add) lists.shopping.push({ id: id(), text, created_at: Date.now() });
  }
  if (Array.isArray(payload.shopping_remove)) {
    lists.shopping = lists.shopping.filter((s) => !payload.shopping_remove.includes(s.id));
  }

  if (Array.isArray(payload.reminders_add)) {
    for (const r of payload.reminders_add) {
      lists.reminders.push({ id: id(), text: r.text, due: r.due || null, created_at: Date.now() });
    }
  }
  if (Array.isArray(payload.reminders_remove)) {
    lists.reminders = lists.reminders.filter((r) => !payload.reminders_remove.includes(r.id));
  }

  return lists;
}

export async function generateResponse(env, username, displayName, message, location) {
  const profile = await loadProfile(env, username);
  const registry = await loadRegistry(env);
  const history = (await loadHistory(env, username)).slice(-20);

  const lists = {
    notes: await loadList(env, username, "notes"),
    tasks: await loadList(env, username, "tasks"),
    goals: await loadList(env, username, "goals"),
    shopping: await loadList(env, username, "shopping"),
    reminders: await loadList(env, username, "reminders"),
  };

  let weather = null;
  if (location && location.lat != null && location.lon != null) {
    try {
      weather = await getWeather(location.lat, location.lon);
    } catch {
      weather = null;
    }
  }

  const systemPrompt = buildSystemPrompt(displayName, profile, registry, lists, weather);
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

  const dataResult = extractBlock(reply, DATA_UPDATE_RE);
  reply = dataResult.cleaned;
  if (dataResult.payload) {
    applyDataUpdate(lists, dataResult.payload);
    await saveList(env, username, "notes", lists.notes);
    await saveList(env, username, "tasks", lists.tasks);
    await saveList(env, username, "goals", lists.goals);
    await saveList(env, username, "shopping", lists.shopping);
    await saveList(env, username, "reminders", lists.reminders);
  }

  const actionResult = extractBlock(reply, ACTION_RE);
  reply = actionResult.cleaned;
  const action =
    actionResult.payload && actionResult.payload.type ? actionResult.payload : null;

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

  return { reply, action };
}
