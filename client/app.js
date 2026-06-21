const loginScreen = document.getElementById("login-screen");
const appScreen = document.getElementById("app-screen");
const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");
const displayNameEl = document.getElementById("display-name");
const logoutBtn = document.getElementById("logout-btn");
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const micBtn = document.getElementById("mic-btn");
const approvalCard = document.getElementById("approval-card");
const approvalList = document.getElementById("approval-list");

let currentUser = null;
let pendingPollHandle = null;

function addBubble(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function showLogin() {
  loginScreen.hidden = false;
  appScreen.hidden = true;
  if (pendingPollHandle) {
    clearInterval(pendingPollHandle);
    pendingPollHandle = null;
  }
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
  loginScreen.hidden = true;
  appScreen.hidden = false;
  chatLog.innerHTML = "";

  const history = await API.chatHistory();
  for (const entry of history) {
    addBubble(entry.role === "user" ? "user" : "assistant", entry.content);
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
  loginError.hidden = true;
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  try {
    const user = await API.login(username, password);
    await enterApp(user);
  } catch (err) {
    loginError.textContent = err.message;
    loginError.hidden = false;
  }
});

logoutBtn.addEventListener("click", async () => {
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
    } else {
      showLogin();
    }
  } catch {
    showLogin();
  }
})();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js");
  });
}
