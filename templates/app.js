(function initDRReview(global) {
  "use strict";

  const icons = {
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "alert-triangle": '<path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "arrow-down-right": '<path d="m7 7 10 10"/><path d="M17 7v10H7"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "arrow-up-right": '<path d="M7 17 17 7"/><path d="M7 7h10v10"/>',
    "box-select": '<path d="M5 3a2 2 0 0 0-2 2"/><path d="M19 3a2 2 0 0 1 2 2"/><path d="M21 19a2 2 0 0 1-2 2"/><path d="M5 21a2 2 0 0 1-2-2"/><path d="M9 3h1M14 3h1M9 21h1M14 21h1M3 9v1M3 14v1M21 9v1M21 14v1"/>',
    "check": '<path d="m20 6-11 11-5-5"/>',
    "check-circle": '<path d="M22 11.1V12a10 10 0 1 1-5.9-9.1"/><path d="m9 11 3 3L22 4"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "clipboard-check": '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    "copy": '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5"/><path d="M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
    "eye": '<path d="M2.1 12a10.6 10.6 0 0 1 19.8 0 10.6 10.6 0 0 1-19.8 0Z"/><circle cx="12" cy="12" r="3"/>',
    "filter": '<path d="M4 6h16M7 12h10M10 18h4"/>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22v-7"/>',
    "flask": '<path d="M9 3h6M10 9V3h4v6l5 8.5A2 2 0 0 1 17.3 21H6.7A2 2 0 0 1 5 17.5Z"/><path d="M7 15h10"/>',
    "git-compare": '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7M11 18H8a2 2 0 0 1-2-2V9"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "layout-dashboard": '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
    "layers": '<path d="m12.8 2.2-10.2 4a1 1 0 0 0 0 1.8l8.6 3.8a2 2 0 0 0 1.6 0l8.6-3.8a1 1 0 0 0 0-1.8Z"/><path d="m22 12.5-9.2 4.2a2 2 0 0 1-1.6 0L2 12.5M22 17.5l-9.2 4.2a2 2 0 0 1-1.6 0L2 17.5"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "minus": '<path d="M5 12h14"/>',
    "mouse-pointer": '<path d="m4 4 7 17 2.6-7.4L21 11Z"/>',
    "pencil": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "plug": '<path d="M12 22v-5M9 8V2M15 8V2M18 8v3a6 6 0 0 1-12 0V8Z"/>',
    "refresh": '<path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M8 16H3v5"/>',
    "scan-eye": '<path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="1"/><path d="M18.9 12s-2.5 4-6.9 4-6.9-4-6.9-4 2.5-4 6.9-4 6.9 4 6.9 4Z"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V5l8-3 8 3z"/><path d="m9 12 2 2 4-4"/>',
    "sliders": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "zoom-in": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3M11 8v6M8 11h6"/>',
    "zoom-out": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3M8 11h6"/>'
  };

  const navGroups = [
    { label: "Review workspace", items: [
      { id: "overview", label: "Overview", icon: "layout-dashboard", href: "index.html" },
      { id: "screening", label: "Screening", icon: "scan-eye", href: "annotate.html" },
      { id: "review", label: "Review queue", icon: "clipboard-check", href: "review.html" }
    ]},
    { label: "Model lab", items: [
      { id: "explainability", label: "Explainability", icon: "layers", href: "explainability.html" },
      { id: "model-diff", label: "Model comparison", icon: "git-compare", href: "model-diff.html" }
    ]},
    { label: "System", items: [
      { id: "integrations", label: "Integrations", icon: "plug", href: "integrations.html" }
    ]}
  ];

  function renderIcons(root) {
    (root || document).querySelectorAll("[data-icon]").forEach((node) => {
      const path = icons[node.dataset.icon];
      if (!path) return;
      node.innerHTML = `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${path}</svg>`;
    });
  }

  function renderShell() {
    const body = document.body;
    const active = body.dataset.page || "overview";
    const title = body.dataset.title || "DR Review Workspace";
    const sidebar = document.querySelector("[data-sidebar]");
    const topbar = document.querySelector("[data-topbar]");
    if (sidebar) {
      const groups = navGroups.map((group) => `<div class="nav-group"><div class="nav-label">${group.label}</div>${group.items.map((item) => `<a class="nav-link" href="${item.href}"${item.id === active ? ' aria-current="page"' : ""}><span data-icon="${item.icon}"></span>${item.label}</a>`).join("")}</div>`).join("");
      sidebar.innerHTML = `<a class="brand" href="index.html"><span class="brand-copy"><strong>DR Review Workspace</strong><span>Screening Support POC</span></span><span class="poc-badge">POC</span></a><nav class="nav-scroll" aria-label="Primary navigation">${groups}</nav><div class="sidebar-foot"><div class="user-chip"><span class="avatar">RA</span><span><strong>Research workspace</strong><span>Mock data only</span></span></div></div>`;
    }
    if (topbar) {
      topbar.innerHTML = `<div class="topbar-left"><button class="icon-button menu-button" type="button" data-menu-open aria-label="Open navigation"><span data-icon="menu"></span></button><span class="topbar-title">${title}</span></div><div class="topbar-right"><span class="badge"><span class="dot"></span>Mock workspace</span><span class="badge badge--primary">Research use only</span></div>`;
    }
    if (!document.querySelector("[data-mobile-scrim]")) {
      const scrim = document.createElement("button");
      scrim.className = "mobile-scrim";
      scrim.type = "button";
      scrim.dataset.mobileScrim = "";
      scrim.setAttribute("aria-label", "Close navigation");
      document.body.appendChild(scrim);
    }
  }

  function bindMobileNav() {
    const sidebar = document.querySelector("[data-sidebar]");
    const scrim = document.querySelector("[data-mobile-scrim]");
    const setOpen = (open) => {
      sidebar?.classList.toggle("is-open", open);
      scrim?.classList.toggle("is-open", open);
    };
    document.querySelector("[data-menu-open]")?.addEventListener("click", () => setOpen(true));
    scrim?.addEventListener("click", () => setOpen(false));
  }

  function toast(message, error) {
    const region = document.querySelector("[data-toast-region]");
    if (!region) return;
    const item = document.createElement("div");
    item.className = "toast";
    item.setAttribute("role", "status");
    item.innerHTML = `<span data-icon="${error ? "alert-triangle" : "check-circle"}"></span><span>${message}</span><button type="button" aria-label="Dismiss"><span data-icon="x"></span></button>`;
    item.querySelector("button").addEventListener("click", () => item.remove());
    region.appendChild(item);
    renderIcons(item);
    global.setTimeout(() => item.remove(), 4500);
  }

  function bindScreening() {
    const stage = document.querySelector("[data-image-stage]");
    if (!stage) return;
    let zoom = 1;
    const update = () => {
      stage.style.setProperty("--zoom", String(zoom));
      const output = document.querySelector("[data-zoom-output]");
      if (output) output.textContent = `${Math.round(zoom * 100)}%`;
    };
    document.querySelector("[data-zoom-in]")?.addEventListener("click", () => { zoom = Math.min(1.5, zoom + 0.1); update(); });
    document.querySelector("[data-zoom-out]")?.addEventListener("click", () => { zoom = Math.max(0.7, zoom - 0.1); update(); });
    document.querySelector("[data-reset]")?.addEventListener("click", () => { zoom = 1; update(); });
    document.querySelectorAll("[data-tool]").forEach((button) => button.addEventListener("click", () => {
      document.querySelectorAll("[data-tool]").forEach((item) => item.setAttribute("aria-pressed", "false"));
      button.setAttribute("aria-pressed", "true");
    }));
    document.querySelectorAll("[data-decision]").forEach((button) => button.addEventListener("click", async () => {
      const decision = button.dataset.decision;
      if (decision === "CORRECT") {
        document.querySelector("[data-correction-dialog]")?.showModal();
        return;
      }
      try {
        await global.DRReviewAdapter.submitDecision({ task_id: "TASK-0042", roi_id: "ROI-01", decision, final_label: decision === "CONFIRM" ? "MICROANEURYSM" : null });
        const output = document.querySelector("[data-decision-status]");
        if (output) output.textContent = `${decision} saved in this mock session.`;
      } catch (error) { toast(error.message, true); }
    }));
    document.querySelector("[data-save-correction]")?.addEventListener("click", async () => {
      const label = document.querySelector("[data-corrected-label]")?.value;
      await global.DRReviewAdapter.submitDecision({ task_id: "TASK-0042", roi_id: "ROI-01", decision: "CORRECT", final_label: label });
      document.querySelector("[data-correction-dialog]")?.close();
      const output = document.querySelector("[data-decision-status]");
      if (output) output.textContent = "CORRECT saved in this mock session.";
    });
  }

  function bindDialogs() {
    document.querySelectorAll("[data-dialog-close]").forEach((button) => button.addEventListener("click", () => button.closest("dialog")?.close()));
    document.querySelectorAll("[data-dialog-open]").forEach((button) => button.addEventListener("click", () => document.querySelector(button.dataset.dialogOpen)?.showModal()));
  }

  function bindReview() {
    document.querySelectorAll("[data-queue-item]").forEach((button) => button.addEventListener("click", () => {
      document.querySelectorAll("[data-queue-item]").forEach((item) => item.setAttribute("aria-current", "false"));
      button.setAttribute("aria-current", "true");
      const title = document.querySelector("[data-selected-case]");
      if (title) title.textContent = button.dataset.queueItem;
    }));
    document.querySelectorAll("[data-review-action]").forEach((button) => button.addEventListener("click", () => toast(`${button.dataset.reviewAction} recorded in this mock session.`)));
    document.querySelectorAll("[data-queue-tab]").forEach((button) => button.addEventListener("click", () => {
      document.querySelectorAll("[data-queue-tab]").forEach((item) => item.setAttribute("aria-selected", "false"));
      button.setAttribute("aria-selected", "true");
    }));
  }

  function bindExplainability() {
    const stage = document.querySelector("[data-evidence-stage]");
    document.querySelectorAll("[data-evidence-view]").forEach((button) => button.addEventListener("click", () => {
      document.querySelectorAll("[data-evidence-view]").forEach((item) => item.setAttribute("aria-pressed", "false"));
      button.setAttribute("aria-pressed", "true");
      if (stage) stage.dataset.view = button.dataset.evidenceView;
    }));
  }

  function bindModelDiff() {
    const filter = document.querySelector("[data-diff-filter]");
    const search = document.querySelector("[data-diff-search]");
    const apply = () => {
      const type = filter?.value || "all";
      const term = (search?.value || "").toLowerCase();
      document.querySelectorAll("[data-diff-row]").forEach((row) => {
        const matchType = type === "all" || row.dataset.diffRow === type;
        const matchText = row.textContent.toLowerCase().includes(term);
        row.hidden = !(matchType && matchText);
      });
    };
    filter?.addEventListener("change", apply);
    search?.addEventListener("input", apply);
    document.querySelector("[data-run-comparison]")?.addEventListener("click", () => toast("Demo comparison loaded. No model endpoint was called."));
  }

  function bindIntegrations() {
    document.querySelectorAll("[data-test-connection]").forEach((button) => button.addEventListener("click", async () => {
      const kind = button.dataset.testConnection;
      const old = button.textContent;
      button.disabled = true;
      button.textContent = "Testing…";
      try {
        const result = await global.DRReviewAdapter.testConnection(kind);
        const status = document.querySelector(`[data-connection-status="${kind}"]`);
        if (status) status.textContent = result.status === "MOCK_ONLY" ? "Mock only" : "Connected";
        toast(result.message || "Connection available.");
      } catch (error) { toast(error.message, true); }
      finally { button.disabled = false; button.textContent = old; }
    }));
    document.querySelectorAll("[data-copy]").forEach((button) => button.addEventListener("click", async () => {
      const target = document.querySelector(button.dataset.copy);
      if (!target) return;
      try { await navigator.clipboard.writeText(target.textContent.trim()); toast("Configuration copied."); }
      catch (_) { toast("Copy is unavailable in this browser context.", true); }
    }));
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderShell();
    renderIcons();
    bindMobileNav();
    bindScreening();
    bindDialogs();
    bindReview();
    bindExplainability();
    bindModelDiff();
    bindIntegrations();
  });
})(window);
