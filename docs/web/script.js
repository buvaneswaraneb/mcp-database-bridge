const root = document.documentElement;
const themeToggle = document.getElementById("themeToggle");
const progressBar = document.getElementById("progressBar");
const toast = document.getElementById("toast");

const savedTheme = localStorage.getItem("db-bridge-theme");
if (savedTheme) root.dataset.theme = savedTheme;

themeToggle.addEventListener("click", () => {
  const nextTheme = root.dataset.theme === "light" ? "dark" : "light";
  root.dataset.theme = nextTheme;
  localStorage.setItem("db-bridge-theme", nextTheme);
});

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll(".reveal").forEach((element) => revealObserver.observe(element));

const sections = [...document.querySelectorAll("main section[id]")];
const navLinks = [...document.querySelectorAll(".top-nav a")];

window.addEventListener("scroll", () => {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  progressBar.style.width = `${scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0}%`;

  let current = "";
  sections.forEach((section) => {
    if (window.scrollY >= section.offsetTop - 150) current = section.id;
  });
  navLinks.forEach((link) => link.classList.toggle("active", link.getAttribute("href") === `#${current}`));
}, { passive: true });

const flowSteps = [
  {
    label: "TOOL CALL / list_databases",
    title: "Find available data sources",
    copy: "The agent begins by discovering every database currently mounted through `DB_DIR` or `DB_PATH`.",
    code: `{\n  "method": "tools/call",\n  "params": {\n    "name": "list_databases",\n    "arguments": {}\n  }\n}`
  },
  {
    label: "TOOL CALL / get_schema",
    title: "Understand the table shape",
    copy: "Before writing SQL, the agent can inspect columns, data types, and nullability to avoid invalid assumptions.",
    code: `{\n  "name": "get_schema",\n  "arguments": {\n    "db_name": "sample.db",\n    "table_name": "orders"\n  }\n}`
  },
  {
    label: "POLICY / run_select",
    title: "Reject unsafe operations",
    copy: "The bridge checks for forbidden keywords and confirms the statement begins with SELECT before execution.",
    code: `forbidden = [\n  "INSERT", "UPDATE", "DELETE",\n  "DROP", "CREATE", "ALTER",\n  "TRUNCATE", "PRAGMA"\n]`
  },
  {
    label: "RESPONSE / JSON-RPC",
    title: "Return a bounded result",
    copy: "SQLite rows are serialized as JSON and capped at 100 records before returning through standard output.",
    code: `{\n  "rows": [{ "name": "Widget B" }],\n  "count": 1,\n  "note": "Limited to 100 rows max"\n}`
  }
];

document.querySelectorAll(".walkthrough-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".walkthrough-tab").forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");
    const step = flowSteps[Number(tab.dataset.step)];
    document.getElementById("flowLabel").textContent = step.label;
    document.getElementById("flowTitle").textContent = step.title;
    document.getElementById("flowCopy").textContent = step.copy;
    document.getElementById("flowCode").textContent = step.code;
  });
});

document.querySelectorAll(".setup-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".setup-tab").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".setup-panel").forEach((panel) => panel.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.target).classList.add("active");
  });
});

let toastTimer;
function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 1800);
}

document.querySelectorAll(".copy-button").forEach((button) => {
  button.addEventListener("click", async () => {
    const code = button.parentElement.querySelector("code").textContent.trim();
    try {
      await navigator.clipboard.writeText(code);
      showToast("Copied to clipboard");
    } catch {
      showToast("Clipboard access unavailable");
    }
  });
});

const queryInput = document.getElementById("queryInput");
const labResult = document.getElementById("labResult");
const labStatus = document.getElementById("labStatus");
const forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "PRAGMA"];

function checkQuery() {
  const query = queryInput.value.trim();
  const upper = query.toUpperCase();
  const keyword = forbidden.find((word) => new RegExp(`\\b${word}\\b`).test(upper));
  const isSelect = upper.startsWith("SELECT");
  const allowed = Boolean(query) && isSelect && !keyword;

  labResult.className = `lab-result ${allowed ? "allowed" : "blocked"}`;
  labStatus.innerHTML = `<i></i> ${allowed ? "policy passed" : "policy rejected"}`;
  labStatus.querySelector("i").style.background = allowed ? "var(--accent)" : "var(--red)";

  if (allowed) {
    labResult.innerHTML = `<span class="result-code">200 / ALLOWED</span><div><strong>Read-only policy passed.</strong><p>This query begins with SELECT and contains no blocked write keywords.</p></div>`;
  } else {
    const reason = keyword ? `Write operation '${keyword}' is not allowed.` : query ? "Only SELECT queries are allowed." : "Enter a query to test.";
    labResult.innerHTML = `<span class="result-code">403 / BLOCKED</span><div><strong>Query rejected before execution.</strong><p>${reason}</p></div>`;
  }
}

document.getElementById("checkQuery").addEventListener("click", checkQuery);
document.querySelectorAll(".query-example").forEach((button) => {
  button.addEventListener("click", () => {
    queryInput.value = button.dataset.query;
    checkQuery();
  });
});

document.querySelectorAll(".accordion-item > button").forEach((button) => {
  button.addEventListener("click", () => {
    const item = button.parentElement;
    const open = item.classList.toggle("open");
    button.setAttribute("aria-expanded", String(open));
  });
});

const troubleSearch = document.getElementById("troubleSearch");
const troubleItems = [...document.querySelectorAll(".accordion-item")];
troubleSearch.addEventListener("input", () => {
  const term = troubleSearch.value.trim().toLowerCase();
  let visible = 0;
  troubleItems.forEach((item) => {
    const match = item.textContent.toLowerCase().includes(term) || item.dataset.search.includes(term);
    item.classList.toggle("filtered-out", !match);
    if (match) visible += 1;
  });
  document.getElementById("noResults").style.display = visible ? "none" : "block";
});
