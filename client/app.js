const appScreen = document.getElementById("app-screen");
const displayNameEl = document.getElementById("display-name");
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const micBtn = document.getElementById("mic-btn");
const muteBtn = document.getElementById("mute-btn");
const approvalCard = document.getElementById("approval-card");
const approvalList = document.getElementById("approval-list");
const briefingCard = document.getElementById("briefing-card");
const listsBtn = document.getElementById("lists-btn");
const listsPanel = document.getElementById("lists-panel");
const listsClose = document.getElementById("lists-close");
const listsTabs = document.querySelectorAll(".lists-tab");
const listsAddForm = document.getElementById("lists-add-form");
const listsAddInput = document.getElementById("lists-add-input");
const listsItemsEl = document.getElementById("lists-items");

let currentUser = null;
let pendingPollHandle = null;
let userLocation = null;
let activeListType = "notes";

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

function getLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => resolve(null),
      { timeout: 5000 }
    );
  });
}

async function renderBriefing() {
  try {
    const briefing = await API.briefing(userLocation);
    const parts = [];
    if (briefing.weather) {
      parts.push(`${briefing.weather.temperatureF}°F, ${briefing.weather.condition}`);
    }
    if (briefing.dueReminders.length > 0) {
      parts.push(`${briefing.dueReminders.length} reminder(s) due: ${briefing.dueReminders.map((r) => r.text).join(", ")}`);
    }
    if (briefing.openTaskCount > 0) {
      parts.push(`${briefing.openTaskCount} open task(s)`);
    }
    if (parts.length === 0) {
      briefingCard.hidden = true;
      return;
    }
    briefingCard.textContent = parts.join(" · ");
    briefingCard.hidden = false;
  } catch {
    briefingCard.hidden = true;
  }
}

function runAction(action) {
  if (!action) return;
  switch (action.type) {
    case "tel":
      window.location.href = `tel:${action.value}`;
      break;
    case "sms":
      window.location.href = `sms:${action.value}`;
      break;
    case "facetime":
      window.location.href = `facetime:${action.value}`;
      break;
    case "mail":
      window.location.href = `mailto:${action.value}`;
      break;
    case "maps":
      window.location.href = `https://maps.apple.com/?q=${encodeURIComponent(action.value)}`;
      break;
    case "shortcut":
      window.location.href = `shortcuts://run-shortcut?name=${encodeURIComponent(action.value)}`;
      break;
    case "vibrate":
      if (navigator.vibrate) navigator.vibrate(200);
      break;
    case "clipboard":
      if (navigator.clipboard) navigator.clipboard.writeText(action.value || "");
      break;
    case "share":
      if (navigator.share) navigator.share({ text: action.value || "" });
      break;
  }
}

async function renderListItems() {
  const items = await API.listItems(activeListType);
  listsItemsEl.innerHTML = "";
  const showCheckbox = activeListType === "tasks";

  for (const item of items) {
    const li = document.createElement("li");
    if (item.done) li.classList.add("done");

    if (showCheckbox) {
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = !!item.done;
      checkbox.addEventListener("change", async () => {
        await API.toggleListItem(activeListType, item.id, checkbox.checked);
        renderListItems();
      });
      li.appendChild(checkbox);
    }

    const span = document.createElement("span");
    span.textContent = item.due ? `${item.text} (due ${item.due})` : item.text;
    li.appendChild(span);

    const removeBtn = document.createElement("button");
    removeBtn.textContent = "✕";
    removeBtn.addEventListener("click", async () => {
      await API.removeListItem(activeListType, item.id);
      renderListItems();
    });
    li.appendChild(removeBtn);

    listsItemsEl.appendChild(li);
  }
}

listsBtn.addEventListener("click", () => {
  listsPanel.hidden = !listsPanel.hidden;
  if (!listsPanel.hidden) renderListItems();
});

listsClose.addEventListener("click", () => {
  listsPanel.hidden = true;
});

for (const tab of listsTabs) {
  tab.addEventListener("click", () => {
    activeListType = tab.dataset.type;
    for (const t of listsTabs) t.classList.toggle("active", t === tab);
    renderListItems();
  });
}
listsTabs[0]?.classList.add("active");

listsAddForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = listsAddInput.value.trim();
  if (!text) return;
  listsAddInput.value = "";
  await API.addListItem(activeListType, text);
  renderListItems();
});

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

  userLocation = await getLocation();
  renderBriefing();
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  addBubble("user", message);
  chatInput.value = "";

  try {
    const { reply, action } = await API.sendMessage(message, userLocation);
    addBubble("assistant", reply);
    Voice.speak(reply);
    runAction(action);
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

muteBtn.addEventListener("click", () => {
  const muted = Voice.toggleMute();
  muteBtn.textContent = muted ? "🔇" : "🔊";
});
muteBtn.textContent = Voice.muted ? "🔇" : "🔊";

Voice.init((transcript) => {
  micBtn.classList.remove("listening");
  chatInput.value = transcript;
  chatForm.requestSubmit();
});

(async function init() {
  await enterApp({ username: "joel", role: "owner", display_name: "Joel" });
})();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js");
  });
}
