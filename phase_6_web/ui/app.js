(function () {
  const form = document.getElementById("search-form");
  const resultsEl = document.getElementById("results");
  const statusEl = document.getElementById("status");
  const errorEl = document.getElementById("error");
  const submitBtn = document.getElementById("submit-btn");
  const topKInput = document.getElementById("top_k");
  const topKValueEl = document.getElementById("top_k_value");

  function getApiBase() {
    const override =
      typeof window.__API_BASE__ === "string" && window.__API_BASE__.trim();
    if (override) return override.replace(/\/$/, "");
    if (window.location.protocol === "file:") return "http://127.0.0.1:8000";
    return window.location.origin;
  }
  const API_BASE = getApiBase();

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.hidden = !msg;
  }

  function clearResults() {
    resultsEl.innerHTML = "";
  }

  function syncTopKLabel() {
    if (topKInput && topKValueEl) {
      topKValueEl.textContent = String(topKInput.value);
    }
  }

  if (topKInput) {
    topKInput.addEventListener("input", syncTopKLabel);
    syncTopKLabel();
  }

  function renderSummary(data) {
    const s = data.summary || {};
    const prefs = s.preferences == null || s.preferences === "" ? "(none)" : s.preferences;
    const div = document.createElement("div");
    div.className = "summary";
    div.innerHTML =
      "<strong>Area:</strong> " +
      escapeHtml(String(s.city ?? "")) +
      " · <strong>Budget (max):</strong> " +
      escapeHtml(String(s.max_price_for_two ?? "")) +
      " · <strong>Preferences:</strong> " +
      escapeHtml(String(prefs));
    if (data.used_fallback) {
      div.innerHTML +=
        '<br><span class="badge">Ranked by rating (LLM off or unavailable)</span>';
    }
    resultsEl.appendChild(div);
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function selectedPrice() {
    const checked = form.querySelector('input[name="price_tier"]:checked');
    if (!checked) return 600;
    const n = parseInt(checked.value, 10);
    return Number.isFinite(n) ? n : 600;
  }

  function renderCard(item, index) {
    const el = document.createElement("article");
    el.className = "result-card";
    const rate = item.rate_numeric != null ? item.rate_numeric : "—";
    const cost = item.approx_cost_for_two != null ? item.approx_cost_for_two : "—";
    const loc = item.location || "—";
    const cuis = item.cuisines || "—";
    el.innerHTML =
      "<h3>" +
      (index + 1) +
      ". " +
      escapeHtml(item.name || "") +
      "</h3>" +
      '<p class="meta">Rating: ' +
      escapeHtml(String(rate)) +
      " · Cost (two): " +
      escapeHtml(String(cost)) +
      " · " +
      escapeHtml(loc) +
      "</p>" +
      '<p class="meta">Cuisines: ' +
      escapeHtml(cuis) +
      "</p>";
    if (item.rationale) {
      const p = document.createElement("p");
      p.className = "why";
      p.innerHTML = "<strong>Why:</strong> " + escapeHtml(item.rationale);
      el.appendChild(p);
    }
    return el;
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    showError("");
    clearResults();
    statusEl.textContent = "Loading…";
    submitBtn.disabled = true;

    const citySelect = document.getElementById("city-select");
    const city = citySelect ? citySelect.value.trim() : "";
    const price = selectedPrice();
    const prefsEl = document.getElementById("prefs");
    const prefsRaw = prefsEl ? prefsEl.value.trim() : "";
    const topK = topKInput ? parseInt(topKInput.value, 10) || 10 : 10;

    const body = {
      city,
      price,
      preferences: prefsRaw || null,
      top_k: topK,
    };

    try {
      const res = await fetch(API_BASE + "/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(function () {
        return {};
      });

      if (!res.ok) {
        statusEl.textContent = "";
        showError(data.error || "Request failed (" + res.status + ").");
        return;
      }

      statusEl.textContent = "";
      renderSummary(data);

      if (!data.items || data.items.length === 0) {
        const p = document.createElement("p");
        p.className = "empty";
        p.textContent =
          data.message ||
          "No restaurants matched. Try another locality or a higher budget tier.";
        resultsEl.appendChild(p);
        return;
      }

      data.items.forEach(function (item, i) {
        resultsEl.appendChild(renderCard(item, i));
      });
    } catch (err) {
      statusEl.textContent = "";
      showError(
        "Connection failed. From the project root start the server: python3 -m uvicorn phase_6_web.api:app --host 127.0.0.1 — then open http://127.0.0.1:8000/ (not as a local file)."
      );
    } finally {
      submitBtn.disabled = false;
    }
  });
})();
