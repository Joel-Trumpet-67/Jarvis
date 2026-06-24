const appScreen = document.getElementById("app-screen");
const displayNameEl = document.getElementById("display-name");
const logoutBtn = document.getElementById("logout-btn");
const switchAccountBtn = document.getElementById("switch-account-btn");
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const micBtn = document.getElementById("mic-btn");
const approvalCard = document.getElementById("approval-card");
const approvalList = document.getElementById("approval-list");

let currentUser = null;
let pendingPollHandle = null;

const REMEMBER_KEY = "jarvis-remembered-login";

function rememberLogin(username, password) {
  localStorage.setItem(REMEMBER_KEY, JSON.stringify({ username, password }));
}

function getRememberedLogin() {
  try {
    return JSON.parse(localStorage.getItem(REMEMBER_KEY));
  } catch {
    return null;
  }
}

function forgetLogin() {
  localStorage.removeItem(REMEMBER_KEY);
}

function addBubble(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function renderPendingTools() {
  const tools = await API.pendingTools();
  approvalList.innerHTML = "";

  if (tools.length === 0) {
    approvalCard.hidden = true;
    return;
  }

  approvalCard.hidden = false;
  for (const tool of tools) {
    const card = document.createElement("div");
    card.className = "tool-pending";
    card.innerHTML = `
      <div class="tool-id">${tool.tool_id}</div>
      <div class="tool-description">${tool.description}</div>
      <details>
        <summary>View code</summary>
        <pre></pre>
      </details>
      <div class="tool-actions">
        <button class="btn-approve">Approve</button>
        <button class="btn-reject">Reject</button>
      </div>
    `;
    card.querySelector("pre").textContent = tool.code;

    card.querySelector(".btn-approve").addEventListener("click", async () => {
      await API.approveTool(tool.tool_id);
      renderPendingTools();
    });

    card.querySelector(".btn-reject").addEventListener("click", async () => {
      const reason = window.prompt("Reason for rejecting this tool:", "");
      if (reason === null) return;
      await API.rejectTool(tool.tool_id, reason);
      renderPendingTools();
    });

    approvalList.appendChild(card);
  }
}

async function enterApp(user) {
  currentUser = user;
  displayNameEl.textContent = `Jarvis — ${user.display_name}`;
  appScreen.hidden = false;
  chatLog.innerHTML = "";

  const history = await API.chatHistory();
  for (const entry of history) {
    addBubble(entry.role === "user" ? "user" : "assistant", entry.content);
  }

  if (pendingPollHandle) {
    clearInterval(pendingPollHandle);
    pendingPollHandle = null;
  }

  if (user.role === "owner") {
    renderPendingTools();
    pendingPollHandle = setInterval(renderPendingTools, 8000);
  } else {
    approvalCard.hidden = true;
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (loginForm.dataset.submitting === "true") return;
  loginForm.dataset.submitting = "true";
  loginError.hidden = true;
  const submitBtn = loginForm.querySelector('button[type="submit"]');
  if (submitBtn) submitBtn.disabled = true;

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  try {
    const user = await API.login(username, password);
    rememberLogin(username, password);
    await enterApp(user);
  } catch (err) {
    loginError.textContent = err.message;
    loginError.hidden = false;
  } finally {
    loginForm.dataset.submitting = "false";
    if (submitBtn) submitBtn.disabled = false;
  }
});

switchAccountBtn.addEventListener("click", async () => {
  forgetLogin();
  await API.logout();
  currentUser = null;
  showLogin();
});

logoutBtn.addEventListener("click", async () => {
  forgetLogin();
  await API.logout();
  currentUser = null;
  showLogin();
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  addBubble("user", message);
  chatInput.value = "";

  try {
    const { reply } = await API.sendMessage(message);
    addBubble("assistant", reply);
    Voice.speak(reply);
    if (currentUser && currentUser.role === "owner") renderPendingTools();
  } catch (err) {
    addBubble("assistant", `Error: ${err.message}`);
  }
});

micBtn.addEventListener("click", () => {
  if (!Voice.supported) {
    addBubble("assistant", "Voice input is not supported in this browser.");
    return;
  }
  micBtn.classList.add("listening");
  Voice.start();
});

Voice.init((transcript) => {
  micBtn.classList.remove("listening");
  chatInput.value = transcript;
  chatForm.requestSubmit();
});

(async function init() {
  try {
    const status = await API.me();
    if (status.authenticated) {
      await enterApp(status);
      return;
    }
  } catch {
    // fall through to remembered-login attempt
  }

  const remembered = getRememberedLogin();
  if (remembered) {
    try {
      const user = await API.login(remembered.username, remembered.password);
      await enterApp(user);
      return;
    } catch {
      forgetLogin();
    }
  }

  showLogin();
})();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js");
  });
}
