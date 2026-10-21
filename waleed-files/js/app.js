/* Shared logic: storage, CSV/Excel parsing, cleaning, scenario engine, formatting, nav.
   Every page loads this file, so all pages read the same dataset and saved scenarios. */
const DIS = (() => {
  const KEY_DATA = "dis.dataset";
  const KEY_SC = "dis.scenarios";
  let navActive = null;

  const REQUIRED = ["date", "product", "units", "price", "unit_cost", "marketing_spend", "expenses"];
  const LABELS = {
    date: "Date", product: "Product", units: "Units sold", price: "Unit price",
    unit_cost: "Unit cost", marketing_spend: "Marketing spend", expenses: "Other expenses",
  };
  const ALIASES = {
    date: ["date", "month", "period", "order_date"],
    product: ["product", "item", "sku", "product_name", "name"],
    units: ["units", "quantity", "qty", "units_sold", "sold"],
    price: ["price", "unit_price", "selling_price", "sale_price"],
    unit_cost: ["unit_cost", "cost", "cogs", "cost_price", "unit_cogs"],
    marketing_spend: ["marketing_spend", "marketing", "ad_spend", "marketing_budget", "ads"],
    expenses: ["expenses", "expense", "other_expenses", "operating_expenses", "opex", "overhead"],
  };

  /* ---------- Storage ---------- */
  const store = {
    get(key, fallback) {
      try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; }
      catch (e) { return fallback; }
    },
    set(key, value) {
      try { localStorage.setItem(key, JSON.stringify(value)); return true; }
      catch (e) { return false; }
    },
  };
  const getDataset = () => store.get(KEY_DATA, null);
  const setDataset = (ds) => { const ok = store.set(KEY_DATA, ds); if (navActive) renderNav(navActive); return ok; };
  const clearDataset = () => { try { localStorage.removeItem(KEY_DATA); } catch (e) {} if (navActive) renderNav(navActive); };
  const getScenarios = () => store.get(KEY_SC, []);
  const setScenarios = (list) => store.set(KEY_SC, list);
  function addScenario(sc) {
    const list = getScenarios();
    sc.id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    sc.savedAt = new Date().toISOString();
    list.push(sc);
    setScenarios(list);
    return sc;
  }
  function deleteScenario(id) { setScenarios(getScenarios().filter((s) => s.id !== id)); }

  /* ---------- CSV parsing (handles quotes, commas, CRLF) ---------- */
  function parseCSV(text) {
    text = text.replace(/^﻿/, "");
    const rows = [];
    let row = [], field = "", inQuotes = false;
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (inQuotes) {
        if (ch === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; } else inQuotes = false;
        } else field += ch;
      } else if (ch === '"') inQuotes = true;
      else if (ch === ",") { row.push(field); field = ""; }
      else if (ch === "\n" || ch === "\r") {
        if (ch === "\r" && text[i + 1] === "\n") i++;
        row.push(field); field = "";
        if (row.some((c) => c.trim() !== "")) rows.push(row);
        row = [];
      } else field += ch;
    }
    row.push(field);
    if (row.some((c) => c.trim() !== "")) rows.push(row);
    if (!rows.length) return { headers: [], records: [] };
    const headers = rows[0].map((h) => h.trim());
    const records = rows.slice(1).map((r) => {
      const o = {};
      headers.forEach((h, i) => (o[h] = (r[i] ?? "").trim()));
      return o;
    });
    return { headers, records };
  }

  /* Parse a File object (.csv, .xlsx, .xls) into { headers, records }. */
  function parseFile(file) {
    return new Promise((resolve, reject) => {
      const name = file.name.toLowerCase();
      const reader = new FileReader();
      reader.onerror = () => reject(new Error("Could not read the file."));
      if (name.endsWith(".csv") || name.endsWith(".txt")) {
        reader.onload = () => {
          const out = parseCSV(String(reader.result));
          out.headers.length ? resolve(out) : reject(new Error("The file is empty."));
        };
        reader.readAsText(file);
      } else if (name.endsWith(".xlsx") || name.endsWith(".xls")) {
        if (typeof XLSX === "undefined") return reject(new Error("Excel support did not load (check your internet connection) — try a CSV file."));
        reader.onload = () => {
          try {
            const wb = XLSX.read(reader.result, { type: "array", cellDates: false });
            const sheet = wb.Sheets[wb.SheetNames[0]];
            const csv = XLSX.utils.sheet_to_csv(sheet);
            const out = parseCSV(csv);
            out.headers.length ? resolve(out) : reject(new Error("The first sheet is empty."));
          } catch (e) { reject(new Error("This Excel file could not be read.")); }
        };
        reader.readAsArrayBuffer(file);
      } else {
        reject(new Error("Unsupported file type. Please upload a .csv, .xlsx or .xls file."));
      }
    });
  }

  /* ---------- Column detection and cleaning ---------- */
  const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

  function detectMapping(headers) {
    const mapping = {};
    const used = new Set();
    REQUIRED.forEach((field) => {
      const hit = headers.find((h) => !used.has(h) && ALIASES[field].includes(norm(h)));
      if (hit) { mapping[field] = hit; used.add(hit); } else mapping[field] = "";
    });
    return mapping;
  }

  const toNum = (v) => {
    if (v === "" || v == null) return NaN;
    const n = Number(String(v).replace(/[$,£€\s]/g, ""));
    return Number.isFinite(n) ? n : NaN;
  };

  function monthKey(v) {
    const s = String(v).trim();
    let m = s.match(/^(\d{4})[-/](\d{1,2})/);
    if (m) return m[1] + "-" + m[2].padStart(2, "0");
    m = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/); // dd/mm/yyyy
    if (m) return m[3] + "-" + m[2].padStart(2, "0");
    const d = new Date(s);
    if (!isNaN(d)) return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
    return "";
  }

  /* Turns raw records + mapping into clean rows and a quality report. */
  function cleanRows(records, mapping) {
    const report = {
      totalRows: records.length, kept: 0, duplicates: 0, droppedMissing: 0,
      droppedInvalid: 0, filledZero: 0, badDates: 0, negatives: 0, outliers: [],
    };
    const seen = new Set();
    const rows = [];
    for (const rec of records) {
      const g = (f) => rec[mapping[f]];
      const key = REQUIRED.map((f) => String(g(f) ?? "").trim().toLowerCase()).join("|");
      if (seen.has(key)) { report.duplicates++; continue; }
      seen.add(key);

      const product = String(g("product") ?? "").trim();
      const date = String(g("date") ?? "").trim();
      const units = toNum(g("units")), price = toNum(g("price")), cost = toNum(g("unit_cost"));
      if (!product || !date || [g("units"), g("price"), g("unit_cost")].some((v) => v === "" || v == null)) {
        report.droppedMissing++; continue;
      }
      if (isNaN(units) || isNaN(price) || isNaN(cost)) { report.droppedInvalid++; continue; }
      if (units < 0 || price < 0 || cost < 0) { report.negatives++; report.droppedInvalid++; continue; }
      const mk = monthKey(date);
      if (!mk) { report.badDates++; report.droppedInvalid++; continue; }

      let marketing = toNum(g("marketing_spend")), expenses = toNum(g("expenses"));
      if (isNaN(marketing) || marketing < 0) { marketing = 0; report.filledZero++; }
      if (isNaN(expenses) || expenses < 0) { expenses = 0; report.filledZero++; }
      rows.push({ date, month: mk, product, units, price, unit_cost: cost, marketing_spend: marketing, expenses });
    }
    report.kept = rows.length;

    // Simple outlier check: units more than 3 standard deviations from the mean.
    if (rows.length >= 8) {
      const vals = rows.map((r) => r.units);
      const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
      const sd = Math.sqrt(vals.reduce((a, b) => a + (b - mean) ** 2, 0) / vals.length);
      if (sd > 0) rows.forEach((r) => { if (Math.abs(r.units - mean) > 3 * sd) report.outliers.push(r); });
    }
    return { rows, report };
  }

  /* ---------- Aggregations ---------- */
  function totals(rows) {
    const t = { units: 0, revenue: 0, cogs: 0, marketing: 0, expenses: 0 };
    rows.forEach((r) => {
      t.units += r.units;
      t.revenue += r.units * r.price;
      t.cogs += r.units * r.unit_cost;
      t.marketing += r.marketing_spend;
      t.expenses += r.expenses;
    });
    t.totalCosts = t.cogs + t.marketing + t.expenses;
    t.profit = t.revenue - t.totalCosts;
    t.margin = t.revenue ? t.profit / t.revenue : 0;
    return t;
  }

  function byMonth(rows) {
    const map = {};
    rows.forEach((r) => (map[r.month] = map[r.month] || []).push(r));
    return Object.keys(map).sort().map((m) => ({ month: m, ...totals(map[m]) }));
  }

  function byProduct(rows) {
    const map = {};
    rows.forEach((r) => (map[r.product] = map[r.product] || []).push(r));
    return Object.keys(map).map((p) => {
      const t = totals(map[p]);
      const gross = t.revenue - t.cogs;
      return { product: p, ...t, grossMargin: t.revenue ? gross / t.revenue : 0 };
    }).sort((a, b) => b.revenue - a.revenue);
  }

  /* ---------- Scenario engine ----------
     All formulas are explicit and shown to the user on the What-If page.
       newPrice     = price     × (1 + priceChange)
       newUnitCost  = unit_cost × (1 + costChange)
       newUnits     = units × (1 + elasticity × priceChange) × (1 + marketingLift × marketingChange)
       revenue      = Σ newUnits × newPrice
       COGS         = Σ newUnits × newUnitCost
       marketing    = Σ marketing_spend × (1 + marketingChange)
       expenses     = Σ expenses        × (1 + expensesChange)
       profit       = revenue − COGS − marketing − expenses
     Percent inputs are decimals (0.10 = +10%). Units never go below zero. */
  const DEFAULT_ASSUMPTIONS = { elasticity: -1.2, marketingLift: 0.15 };

  function simulate(rows, p) {
    const a = { ...DEFAULT_ASSUMPTIONS, ...p };
    const priceCh = a.price || 0, costCh = a.cost || 0, mkCh = a.marketing || 0, exCh = a.expenses || 0;
    const volumeFactor = Math.max(0, (1 + a.elasticity * priceCh) * (1 + a.marketingLift * mkCh));
    const t = { units: 0, revenue: 0, cogs: 0, marketing: 0, expenses: 0 };
    rows.forEach((r) => {
      const u = r.units * volumeFactor;
      t.units += u;
      t.revenue += u * r.price * (1 + priceCh);
      t.cogs += u * r.unit_cost * (1 + costCh);
      t.marketing += r.marketing_spend * (1 + mkCh);
      t.expenses += r.expenses * (1 + exCh);
    });
    t.totalCosts = t.cogs + t.marketing + t.expenses;
    t.profit = t.revenue - t.totalCosts;
    t.margin = t.revenue ? t.profit / t.revenue : 0;
    t.volumeFactor = volumeFactor;
    return t;
  }

  /* Best / expected / worst cases: same business changes, different demand assumptions. */
  const CASES = {
    best: { label: "Best case", elasticity: -0.6, marketingLift: 0.25 },
    expected: { label: "Expected case", elasticity: -1.2, marketingLift: 0.15 },
    worst: { label: "Worst case", elasticity: -1.8, marketingLift: 0.05 },
  };

  function riskNotes(p, result, base) {
    const notes = [];
    if ((p.price || 0) >= 0.1) notes.push("Price rise of 10% or more: customers may react more strongly than the elasticity assumption (" + p.elasticity + ") suggests.");
    if ((p.price || 0) <= -0.1) notes.push("Large price cut: profit depends on demand rising enough to make up for the lower margin per unit.");
    if ((p.marketing || 0) >= 0.2) notes.push("Marketing increase of 20% or more: the sales lift (" + p.marketingLift + " per 100% spend) is an assumption, not measured from your data.");
    if ((p.cost || 0) >= 0.1) notes.push("Unit costs rising 10% or more squeezes margin unless prices follow.");
    if ((p.expenses || 0) >= 0.15) notes.push("Expenses rising 15% or more reduces profit directly, with no extra sales assumed.");
    if (result.profit < base.profit) notes.push("Projected profit is below the current baseline.");
    if (result.profit < 0) notes.push("This scenario is projected to run at a loss.");
    if (!notes.length) notes.push("No major risk flags, but all figures are estimates, not guaranteed outcomes.");
    return notes;
  }

  /* ---------- Formatting ---------- */
  const money = (n) => (n < 0 ? "-" : "") + "$" + Math.abs(Math.round(n)).toLocaleString("en-US");
  const num = (n) => Math.round(n).toLocaleString("en-US");
  const pct = (n, d = 1) => (n * 100).toFixed(d) + "%";
  const signedPct = (n, d = 1) => (n > 0 ? "+" : "") + (n * 100).toFixed(d) + "%";
  const deltaClass = (n) => (n > 0.00001 ? "pos" : n < -0.00001 ? "neg" : "neutral");
  const monthLabel = (m) => {
    const [y, mo] = m.split("-");
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][+mo - 1] + " " + y.slice(2);
  };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ---------- Sample data ---------- */
  function loadSample() {
    const { headers, records } = parseCSV(SAMPLE_CSV);
    const { rows, report } = cleanRows(records, detectMapping(headers));
    const ds = { name: "sample_sales.csv", loadedAt: new Date().toISOString(), rows, report };
    setDataset(ds);
    return ds;
  }

  /* ---------- Shared page chrome ---------- */
  function renderNav(active) {
    navActive = active;
    const I = {
      "index.html": '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
      "upload.html": '<path d="M12 16V4m0 0L7 9m5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
      "whatif.html": '<path d="M4 7h9m4 0h3M4 17h3m4 0h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
      "compare.html": '<path d="M5 20V10m7 10V4m7 16v-7"/>',
    };
    const pages = [
      ["index.html", "Dashboard"], ["upload.html", "Upload data"],
      ["whatif.html", "What-if"], ["compare.html", "Compare scenarios"],
    ];
    const el = document.getElementById("topbar");
    if (!el) return;
    const ds = getDataset();
    const foot = ds
      ? '<span class="dot on"></span><div><b>' + esc(ds.name) + "</b><small>" + num(ds.rows.length) + " rows loaded</small></div>"
      : '<span class="dot"></span><div><b>No data loaded</b><small>Upload a file or use the sample</small></div>';
    el.className = "topbar";
    el.innerHTML = '<a class="logo" href="index.html"><span class="logo-mark"><svg viewBox="0 0 24 24"><path d="M4 12h6l4-6h6M10 12l4 6h6"/></svg></span><b>Decision<span>AI</span></b></a><nav class="nav">' +
      pages.map(([href, label]) => '<a href="' + href + '"' + (href === active ? ' class="active" aria-current="page"' : "") + '><svg viewBox="0 0 24 24">' + I[href] + "</svg>" + label + "</a>").join("") +
      '</nav><div class="side-data">' + foot + "</div>";
  }

  if (typeof Chart !== "undefined") {
    Chart.defaults.font.family = '"Figtree", system-ui, sans-serif';
    Chart.defaults.color = "#5d6b7f";
    Chart.defaults.borderColor = "#e8ecf3";
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.elements.bar.borderRadius = 6;
  }

  function chartsAvailable() { return typeof Chart !== "undefined"; }

  return {
    REQUIRED, LABELS, DEFAULT_ASSUMPTIONS, CASES,
    getDataset, setDataset, clearDataset, getScenarios, addScenario, deleteScenario, setScenarios,
    parseCSV, parseFile, detectMapping, cleanRows, loadSample,
    totals, byMonth, byProduct, simulate, riskNotes,
    money, num, pct, signedPct, deltaClass, monthLabel, esc, renderNav, chartsAvailable,
  };
})();

if (typeof module !== "undefined") module.exports = DIS;
