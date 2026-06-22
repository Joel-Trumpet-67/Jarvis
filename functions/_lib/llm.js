async function anthropicChat(env, systemPrompt, messages, maxTokens) {
  if (!env.ANTHROPIC_API_KEY) throw new Error("ANTHROPIC_API_KEY is not configured");

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: env.AI_MODEL || "claude-sonnet-4-6",
      max_tokens: maxTokens,
      system: systemPrompt,
      messages,
    }),
  });
  if (!res.ok) throw new Error(`anthropic request failed: ${await res.text()}`);
  const data = await res.json();
  return data.content.filter((b) => b.type === "text").map((b) => b.text).join("");
}

function providerEndpoint(env, provider) {
  if (provider === "groq") {
    return {
      url: "https://api.groq.com/openai/v1/chat/completions",
      key: env.GROQ_API_KEY,
      model: env.AI_MODEL || "llama-3.3-70b-versatile",
    };
  }
  if (provider === "ollama") {
    return {
      url: `${(env.OLLAMA_BASE_URL || "http://localhost:11434/v1").replace(/\/$/, "")}/chat/completions`,
      key: "ollama",
      model: env.AI_MODEL || "llama3.1",
    };
  }
  if (provider === "openai") {
    return {
      url: "https://api.openai.com/v1/chat/completions",
      key: env.OPENAI_API_KEY,
      model: env.AI_MODEL || "gpt-4o-mini",
    };
  }
  throw new Error(`Unknown AI_PROVIDER '${provider}'`);
}

async function openaiCompatibleChat(env, provider, systemPrompt, messages, maxTokens) {
  const { url, key, model } = providerEndpoint(env, provider);
  if (!key) throw new Error(`${provider} API key is not configured`);

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
    body: JSON.stringify({
      model,
      max_tokens: maxTokens,
      messages: [{ role: "system", content: systemPrompt }, ...messages],
    }),
  });
  if (!res.ok) throw new Error(`${provider} request failed: ${await res.text()}`);
  const data = await res.json();
  return data.choices[0].message.content || "";
}

export async function chat(env, systemPrompt, messages, maxTokens = 1024) {
  const provider = (env.AI_PROVIDER || "groq").trim().toLowerCase();
  if (provider === "anthropic") return anthropicChat(env, systemPrompt, messages, maxTokens);
  return openaiCompatibleChat(env, provider, systemPrompt, messages, maxTokens);
}
