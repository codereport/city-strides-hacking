(() => {
  if (location.protocol !== "file:") return;

  const apiRoot = "http://127.0.0.1:8765/api/runs";
  const page = document.body.dataset.runPage;
  const style = document.createElement("style");
  style.textContent = `
    .local-manager { margin-top:18px; padding:12px 14px; border:1px solid #4c3c66; border-radius:10px; background:rgba(35,27,49,.9); color:#d8cbea; font-size:13px; }
    .local-manager.error { border-color:#8f433a; background:#351d1a; color:#ffd0ca; }
    .run-card { display:grid; min-width:0; gap:8px; }
    .run-card .run { height:100%; }
    .run-actions { display:grid; }
    .run-actions button { border:1px solid #4b504a; border-radius:8px; padding:8px 10px; background:#171a18; color:#f6f3ea; font:inherit; font-weight:800; cursor:pointer; }
    .run-actions .complete { border-color:#709d3d; color:#b8ff55; }
    .run-actions button:disabled { opacity:.45; cursor:wait; }
  `;
  document.head.append(style);

  const status = document.createElement("div");
  status.className = "local-manager";
  status.textContent = page === "upcoming"
    ? "Local run management is enabled. Keep the route planner server running on port 8765."
    : "Completed runs are sorted by the time they were marked complete.";
  document.querySelector("header").append(status);

  if (page !== "upcoming") return;

  const setBusy = busy => {
    document.querySelectorAll(".run-actions button").forEach(button => {
      button.disabled = busy;
    });
  };

  async function completeRun(filename) {
    setBusy(true);
    status.classList.remove("error");
    status.textContent = "Moving run to Past runs…";
    try {
      const response = await fetch(`${apiRoot}/complete`, {
        method: "POST",
        headers: {"Content-Type": "text/plain;charset=UTF-8"},
        body: JSON.stringify({filename}),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || response.statusText);
      location.reload();
    } catch (error) {
      status.classList.add("error");
      status.textContent = `Could not complete this run: ${error.message}. Start or restart the route planner server on port 8765.`;
      setBusy(false);
    }
  }

  for (const link of [...document.querySelectorAll(".runs > .run")]) {
    const filename = decodeURIComponent(new URL(link.href).pathname.split("/").pop());
    const card = document.createElement("article");
    card.className = "run-card";
    link.replaceWith(card);
    card.append(link);
    const actions = document.createElement("div");
    actions.className = "run-actions";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "complete";
    button.textContent = "Completed";
    button.onclick = () => completeRun(filename);
    actions.append(button);
    card.append(actions);
  }
})();
