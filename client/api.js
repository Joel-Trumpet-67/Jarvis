const API = {
  async _json(res) {
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(body.error || "Request failed");
    }
    return body;
  },

  login(username, password) {
    return fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    }).then(this._json);
  },

  logout() {
    return fetch("/api/auth/logout", { method: "POST" }).then(this._json);
  },

  me() {
    return fetch("/api/auth/me").then(this._json);
  },

  chatHistory() {
    return fetch("/api/chat/history").then(this._json);
  },

  sendMessage(message) {
    return fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    }).then(this._json);
  },

  pendingTools() {
    return fetch("/api/tools/pending").then(this._json);
  },

  approveTool(toolId) {
    return fetch(`/api/tools/${encodeURIComponent(toolId)}/approve`, {
      method: "POST",
    }).then(this._json);
  },

  rejectTool(toolId, reason) {
    return fetch(`/api/tools/${encodeURIComponent(toolId)}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    }).then(this._json);
  },
};
