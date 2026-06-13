const state = {
  models: [],
  databases: [],
  activeModel: "",
  activeDatabase: localStorage.getItem("db-bridge-database") || "sample.db",
  chats: JSON.parse(localStorage.getItem("db-bridge-chats") || "[]"),
  currentChatId: null,
  abortController: null,
  sessionId: localStorage.getItem("db-bridge-session") || (crypto.randomUUID ? crypto.randomUUID() : `session-${Date.now()}`),
};
localStorage.setItem("db-bridge-session", state.sessionId);

const elements = Object.fromEntries([
  "history", "conversationTitle", "modelSelect", "activeDatabase", "sidebarDatabase",
  "composerContext", "welcome", "messages", "composer", "messageInput", "sendButton",
  "stopButton", "databasePanel", "databaseList", "metadataCard", "backdrop", "toast",
].map((id) => [id, document.getElementById(id)]));

const root = document.documentElement;
root.dataset.theme = localStorage.getItem("db-bridge-theme") || "dark";

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / (1024 ** index)).toFixed(index ? 1 : 0)} ${units[index]}`;
}

let toastTimer;
function toast(message, type = "success") {
  elements.toast.textContent = message;
  elements.toast.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => elements.toast.className = "toast", 2400);
}

function persistChats() {
  localStorage.setItem("db-bridge-chats", JSON.stringify(state.chats.slice(0, 20)));
}

function currentChat() {
  return state.chats.find((chat) => chat.id === state.currentChatId);
}

function newChat() {
  state.currentChatId = null;
  elements.conversationTitle.textContent = "New database chat";
  elements.messages.innerHTML = "";
  elements.welcome.classList.remove("hidden");
  renderHistory();
  elements.messageInput.focus();
}

function renderHistory() {
  elements.history.innerHTML = state.chats.map((chat) => `
    <button class="${chat.id === state.currentChatId ? "active" : ""}" data-chat-id="${chat.id}">
      ${escapeHtml(chat.title)}
    </button>`).join("");
  elements.history.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => loadChat(button.dataset.chatId));
  });
}

function loadChat(id) {
  state.currentChatId = id;
  const chat = currentChat();
  if (!chat) return newChat();
  elements.conversationTitle.textContent = chat.title;
  elements.welcome.classList.add("hidden");
  elements.messages.innerHTML = "";
  chat.messages.forEach((message) => appendMessage(message.role, message.content, message.activity, false));
  renderHistory();
  scrollToBottom();
}

function ensureChat(firstMessage) {
  if (currentChat()) return currentChat();
  const chat = {
    id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    title: firstMessage.slice(0, 46),
    messages: [],
  };
  state.chats.unshift(chat);
  state.currentChatId = chat.id;
  elements.conversationTitle.textContent = chat.title;
  persistChats();
  renderHistory();
  return chat;
}

function activityMarkup(activity) {
  if (!activity?.length) return "";
  return `<details class="activity" open>
    <summary>MCP ACTIVITY · ${activity.length} TOOL CALL${activity.length === 1 ? "" : "S"}</summary>
    <div class="activity-list">${activity.map((item) => `
      <div class="activity-item">
        <span class="activity-tool">${escapeHtml(item.tool)}</span>
        <span class="activity-status ${item.status}">${escapeHtml(item.status)}</span>
        <span class="activity-result">${escapeHtml(JSON.stringify({ arguments: item.arguments, result: item.result }, null, 2))}</span>
      </div>`).join("")}</div>
  </details>`;
}

function appendMessage(role, content, activity = [], save = true) {
  elements.welcome.classList.add("hidden");
  const article = document.createElement("article");
  article.className = `message ${role}`;
  article.innerHTML = `
    <div class="message-avatar">${role === "user" ? "YOU" : "DB"}</div>
    <div>
      <div class="message-head"><strong>${role === "user" ? "You" : "DB/BRIDGE"}</strong><span>${role === "user" ? "QUESTION" : "GROQ + MCP"}</span></div>
      <div class="message-content">${escapeHtml(content)}</div>
      ${activityMarkup(activity)}
    </div>`;
  elements.messages.appendChild(article);
  if (save) {
    currentChat().messages.push({ role, content, activity });
    persistChats();
  }
  scrollToBottom();
  return article;
}

function appendThinking() {
  const article = document.createElement("article");
  article.className = "message assistant";
  article.innerHTML = `<div class="message-avatar">DB</div><div><div class="message-head"><strong>DB/BRIDGE</strong><span>MCP ROUTING</span></div><div class="thinking">Inspecting database context...</div></div>`;
  elements.messages.appendChild(article);
  scrollToBottom();
  return article;
}

function scrollToBottom() {
  document.getElementById("conversation").scrollTop = document.getElementById("conversation").scrollHeight;
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("X-Session-ID", state.sessionId);
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "Request failed.");
  return payload;
}

async function loadModels() {
  try {
    const payload = await api("/api/models");
    state.models = payload.models;
    elements.modelSelect.innerHTML = state.models.map((model) => `<option value="${escapeHtml(model.id)}">${escapeHtml(model.label)}</option>`).join("");
    state.activeModel = localStorage.getItem("db-bridge-model") || state.models[0]?.id || "";
    if (!state.models.some((model) => model.id === state.activeModel)) state.activeModel = state.models[0]?.id || "";
    elements.modelSelect.value = state.activeModel;
  } catch (error) {
    toast(error.message, "error");
  }
}

function updateDatabaseContext() {
  elements.activeDatabase.textContent = state.activeDatabase || "No database";
  elements.sidebarDatabase.textContent = state.activeDatabase || "No database";
  elements.composerContext.textContent = `${state.activeDatabase || "No database"} via MCP`;
  localStorage.setItem("db-bridge-database", state.activeDatabase || "");
}

async function loadDatabases() {
  try {
    state.databases = await api("/api/databases");
    if (!state.databases.some((database) => database.name === state.activeDatabase)) {
      state.activeDatabase = state.databases[0]?.name || "";
    }
    updateDatabaseContext();
    renderDatabases();
  } catch (error) {
    toast(error.message, "error");
  }
}

function renderDatabases() {
  elements.databaseList.innerHTML = state.databases.map((database) => `
    <div class="database-row ${database.name === state.activeDatabase ? "active" : ""}">
      <span class="status-dot"></span>
      <span class="database-row-info"><strong>${escapeHtml(database.name)}</strong><small>${formatBytes(database.size)} · ${database.sample ? "bundled sample" : "temporary upload"}</small></span>
      <span class="database-actions">
        <button data-action="metadata" data-name="${escapeHtml(database.name)}">Info</button>
        <button data-action="select" data-name="${escapeHtml(database.name)}">Use</button>
        ${database.sample ? "" : `<button class="delete" data-action="delete" data-name="${escapeHtml(database.name)}">Delete</button>`}
      </span>
    </div>`).join("") || `<div class="temporary-warning"><span>No databases available.</span></div>`;
  elements.databaseList.querySelectorAll("button").forEach((button) => button.addEventListener("click", handleDatabaseAction));
}

async function handleDatabaseAction(event) {
  const { action, name } = event.currentTarget.dataset;
  if (action === "select") {
    state.activeDatabase = name;
    updateDatabaseContext();
    renderDatabases();
    toast(`Using ${name}`);
  }
  if (action === "metadata") {
    try {
      const data = await api(`/api/databases/${encodeURIComponent(name)}/metadata`);
      elements.metadataCard.textContent = JSON.stringify(data, null, 2);
      elements.metadataCard.classList.remove("hidden");
    } catch (error) { toast(error.message, "error"); }
  }
  if (action === "delete" && confirm(`Delete temporary database '${name}'?`)) {
    try {
      await api(`/api/databases/${encodeURIComponent(name)}`, { method: "DELETE" });
      await loadDatabases();
      toast(`Deleted ${name}`);
    } catch (error) { toast(error.message, "error"); }
  }
}

async function uploadDatabase(file) {
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  try {
    const database = await api("/api/databases/upload", { method: "POST", body: form });
    state.activeDatabase = database.name;
    await loadDatabases();
    toast(`Uploaded ${database.name}`);
  } catch (error) {
    toast(error.message, "error");
  }
}

function setBusy(busy) {
  elements.sendButton.disabled = busy;
  elements.sendButton.classList.toggle("hidden", busy);
  elements.stopButton.classList.toggle("hidden", !busy);
}

async function sendMessage(text) {
  if (!text.trim() || !state.activeModel) return;
  const chat = ensureChat(text.trim());
  appendMessage("user", text.trim());
  elements.messageInput.value = "";
  resizeInput();
  const thinking = appendThinking();
  setBusy(true);
  state.abortController = new AbortController();

  try {
    const requestMessages = chat.messages.map(({ role, content }) => ({ role, content }));
    const payload = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: state.activeModel, database: state.activeDatabase || null, messages: requestMessages }),
      signal: state.abortController.signal,
    });
    thinking.remove();
    appendMessage("assistant", payload.answer, payload.activity);
  } catch (error) {
    thinking.remove();
    if (error.name !== "AbortError") {
      appendMessage("assistant", `Request failed: ${error.message}`);
      toast(error.message, "error");
    }
  } finally {
    state.abortController = null;
    setBusy(false);
  }
}

function resizeInput() {
  elements.messageInput.style.height = "auto";
  elements.messageInput.style.height = `${Math.min(elements.messageInput.scrollHeight, 180)}px`;
}

function openDatabasePanel() {
  elements.databasePanel.classList.add("open");
  elements.databasePanel.setAttribute("aria-hidden", "false");
  elements.backdrop.classList.remove("hidden");
  loadDatabases();
}

function closePanels() {
  elements.databasePanel.classList.remove("open");
  elements.databasePanel.setAttribute("aria-hidden", "true");
  document.getElementById("sidebar").classList.remove("open");
  elements.backdrop.classList.add("hidden");
}

elements.composer.addEventListener("submit", (event) => { event.preventDefault(); sendMessage(elements.messageInput.value); });
elements.messageInput.addEventListener("input", resizeInput);
elements.messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); elements.composer.requestSubmit(); }
});
elements.modelSelect.addEventListener("change", () => {
  state.activeModel = elements.modelSelect.value;
  localStorage.setItem("db-bridge-model", state.activeModel);
});
elements.stopButton.addEventListener("click", () => state.abortController?.abort());
document.getElementById("newChat").addEventListener("click", newChat);
document.getElementById("themeToggle").addEventListener("click", () => {
  root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
  localStorage.setItem("db-bridge-theme", root.dataset.theme);
});
document.getElementById("databasePill").addEventListener("click", openDatabasePanel);
document.getElementById("openDatabasePanel").addEventListener("click", openDatabasePanel);
document.getElementById("closeDatabasePanel").addEventListener("click", closePanels);
document.getElementById("refreshDatabases").addEventListener("click", loadDatabases);
elements.backdrop.addEventListener("click", closePanels);
document.getElementById("databaseUpload").addEventListener("change", (event) => uploadDatabase(event.target.files[0]));
document.getElementById("openSidebar").addEventListener("click", () => {
  document.getElementById("sidebar").classList.add("open");
  elements.backdrop.classList.remove("hidden");
});
document.getElementById("closeSidebar").addEventListener("click", closePanels);
document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => sendMessage(button.dataset.prompt)));

Promise.all([loadModels(), loadDatabases()]).then(() => {
  renderHistory();
  newChat();
});
