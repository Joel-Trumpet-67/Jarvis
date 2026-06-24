export async function loadProfile(env, username) {
  const raw = await env.JARVIS_KV.get(`profile:${username}`);
  return raw ? JSON.parse(raw) : { name: username, preferences: {}, facts: [] };
}

export async function saveProfile(env, username, profile) {
  await env.JARVIS_KV.put(`profile:${username}`, JSON.stringify(profile));
}

export async function loadHistory(env, username) {
  const raw = await env.JARVIS_KV.get(`history:${username}`);
  return raw ? JSON.parse(raw) : [];
}

export async function appendHistory(env, username, role, content) {
  const history = await loadHistory(env, username);
  history.push({ role, content, ts: Date.now() });
  await env.JARVIS_KV.put(`history:${username}`, JSON.stringify(history));
  return history;
}

export async function loadRegistry(env) {
  const raw = await env.JARVIS_KV.get("tools:registry");
  return raw ? JSON.parse(raw) : [];
}

export async function saveRegistry(env, registry) {
  await env.JARVIS_KV.put("tools:registry", JSON.stringify(registry));
}
