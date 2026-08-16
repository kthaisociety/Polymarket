"use strict";

const state = {
  library: null,
  view: "ongoing",
  selectedOngoing: 0,
};

const app = document.querySelector("#app");
const tabs = [...document.querySelectorAll(".nav-tab")];

for (const tab of tabs) {
  tab.addEventListener("click", () => {
    state.view = tab.dataset.view;
    for (const item of tabs) {
      item.classList.toggle("is-active", item === tab);
      item.setAttribute("aria-selected", String(item === tab));
    }
    render();
  });
}

fetch("/api/library", { headers: { Accept: "application/json" } })
  .then((response) => {
    if (!response.ok) {
      throw new Error(`Research library returned ${response.status}.`);
    }
    return response.json();
  })
  .then((library) => {
    state.library = library;
    document.querySelector("#ongoing-count").textContent = String(library.counts.ongoing);
    document.querySelector("#finalized-count").textContent = String(library.counts.finalized);
    document.querySelector("#library-mode").textContent = library.library_kind;
    render();
  })
  .catch((error) => {
    app.replaceChildren(
      element("section", "error-state", null, [
        element("p", "eyebrow", "LIBRARY ERROR"),
        element("h1", null, "The research records could not be loaded."),
        element("p", null, error.message),
      ]),
    );
  });

function render() {
  if (state.library === null) {
    return;
  }
  if (state.view === "finalized") {
    renderFinalized();
    return;
  }
  renderOngoing();
}

function renderOngoing() {
  const items = state.library.ongoing;
  if (items.length === 0) {
    app.replaceChildren(
      element("section", "empty-state", null, [
        element("p", "eyebrow", "ONGOING RESEARCH"),
        element("h1", null, "No exploratory research receipt is available."),
      ]),
    );
    return;
  }
  const selected = items[Math.min(state.selectedOngoing, items.length - 1)];
  app.replaceChildren(buildIndex(items), buildOngoingDocument(selected));
}

function buildIndex(items) {
  const list = element("ol", "index-list");
  items.forEach((item, index) => {
    const button = element("button", "index-button", null, [
      element("span", "index-title", item.title),
      element("span", "index-meta", `${item.status} · ${formatDate(item.updated_at)}`),
    ]);
    button.type = "button";
    button.classList.toggle("is-selected", index === state.selectedOngoing);
    button.addEventListener("click", () => {
      state.selectedOngoing = index;
      renderOngoing();
    });
    const listItem = document.createElement("li");
    listItem.append(button);
    list.append(listItem);
  });
  return element("aside", "research-index", null, [
    element("header", "index-header", null, [
      element("p", "eyebrow", "ACTIVE QUESTIONS"),
      element("h2", null, `${items.length} research question${items.length === 1 ? "" : "s"}`),
    ]),
    list,
  ]);
}

function buildOngoingDocument(item) {
  const documentHeader = element("header", "document-header", null, [
    element("div", "status-line", null, [
      element("span", null, item.status),
      element("span", null, "No validated finding"),
      element("span", null, formatDate(item.updated_at)),
    ]),
    element("h1", null, item.question),
    element("p", "document-subhead", item.current_conclusion),
  ]);

  const mainColumn = element("div", "main-column", null, [
    reportSection("Current conclusion", [
      element("div", "evidence-callout", null, [
        element("strong", null, "Candidate rejected out of time"),
        element("p", null, item.audit_verdict.replaceAll("_", " ").toLowerCase()),
      ]),
    ]),
    reportSection("Untouched-period evidence", [buildBenchmarkChart(item.benchmarks)]),
    reportSection("Research design", [buildOrderedList(item.method_steps, "ordered-method")]),
    reportSection("Next lawful step", [element("p", null, item.next_step)]),
    reportSection("Limitations", [buildList(item.caveats, "plain-list caveat-list")]),
  ]);

  const sideColumn = element("aside", "side-column", null, [
    sideSection("Research snapshot", buildMetricTable(item)),
    sideSection("Exact provenance", buildProvenance(item.provenance)),
    sideSection("Harness-observed fields", buildList(item.actual_field_accesses, "plain-list")),
  ]);

  return element("article", "research-document", null, [
    documentHeader,
    element("div", "document-grid", null, [mainColumn, sideColumn]),
  ]);
}

function renderFinalized() {
  if (state.library.finalized.length > 0) {
    app.replaceChildren(
      element("section", "empty-state", null, [
        element("p", "eyebrow", "FINALIZED RESEARCH"),
        element("h1", null, "Canonical finalized-report projection is not connected."),
      ]),
    );
    return;
  }
  const empty = state.library.finalized_empty_state;
  app.replaceChildren(
    element("section", "empty-state", null, [
      element("p", "eyebrow", empty.eyebrow),
      element("h1", null, empty.title),
      element("p", "document-subhead", empty.explanation),
      element("div", "empty-notice", "No exploratory receipt is displayed as finalized research."),
      element("section", "empty-section", null, [
        element("p", "section-label", "PUBLICATION STANDARD"),
        element("h2", null, "Every future report will preserve these sections"),
        buildOrderedList(empty.required_sections, "ordered-method"),
      ]),
    ]),
  );
}

function buildBenchmarkChart(benchmarks) {
  const max = Math.max(...benchmarks.map((benchmark) => benchmark.mse));
  const chart = element("div", "benchmark-chart");
  chart.append(element("p", "metric-label", "2023 mean squared error · lower is better"));
  for (const benchmark of benchmarks) {
    const bar = element("div", "benchmark-bar");
    bar.style.width = `${Math.max(3, (benchmark.mse / max) * 100)}%`;
    if (benchmark.role === "candidate") {
      bar.classList.add("is-candidate");
    }
    if (benchmark.role === "strongest_baseline") {
      bar.classList.add("is-strongest");
    }
    chart.append(
      element("div", "benchmark-row", null, [
        element("span", "benchmark-label", benchmark.label),
        element("div", "benchmark-track", null, [bar]),
        element("span", "benchmark-value", benchmark.mse.toFixed(1)),
      ]),
    );
  }
  return chart;
}

function buildMetricTable(item) {
  const rows = [
    ["Source", item.source_label],
    ["Regions", String(item.sample.regions)],
    ["Aligned rows", String(item.sample.rows)],
    ["Test year", String(item.sample.test_year)],
    ["Candidates", "8 lagged variables"],
    ["Harness actions", String(item.harness_action_count)],
    ["Disposition", item.disposition.replaceAll("_", " ")],
  ];
  const body = document.createElement("tbody");
  for (const [label, value] of rows) {
    body.append(
      element("tr", null, null, [element("td", null, label), element("td", null, value)]),
    );
  }
  return element("table", "metric-table", null, [body]);
}

function buildProvenance(provenance) {
  const list = element("div", "provenance-list");
  for (const [key, value] of Object.entries(provenance)) {
    list.append(
      element("div", "provenance-row", null, [
        element("span", "provenance-key", key.replaceAll("_", " ")),
        element("span", "provenance-value", String(value)),
      ]),
    );
  }
  return list;
}

function reportSection(title, children) {
  return element("section", "report-section", null, [
    element("p", "section-label", "ANALYSIS"),
    element("h2", null, title),
    ...children,
  ]);
}

function sideSection(title, child) {
  return element("section", "report-section", null, [
    element("p", "section-label", title),
    child,
  ]);
}

function buildOrderedList(values, className) {
  const list = element("ol", className);
  for (const value of values) {
    list.append(element("li", null, value));
  }
  return list;
}

function buildList(values, className) {
  const list = element("ul", className);
  for (const value of values) {
    list.append(element("li", null, value.replaceAll("_", " ")));
  }
  return list;
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function element(tag, className = null, text = null, children = []) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text !== null) {
    node.textContent = text;
  }
  for (const child of children) {
    node.append(child);
  }
  return node;
}
