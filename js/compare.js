DIS.renderNav("compare.html");
const ui = id => document.getElementById(id);
let dataset = null, comparison = null, selected = new Set(), chart = null, busy = false;
let backendDataset = null;

function notice(text, bad = false) {
  ui("exportStatus").textContent = text;
  ui("exportStatus").className = "notice " + (bad ? "bad" : "good");
}

function number(value) {
  return value == null ? "Unavailable" : value.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
}

function chosen() {
  return comparison.scenarios.filter(item => selected.has(item.id));
}

function setBusy(value) {
  busy = value;
  ["downloadPdf", "downloadCsv", "all", "none", "reportTitle", "includeForecast"].forEach(id => ui(id).disabled = value);
  ui("list").querySelectorAll("button,input").forEach(element => element.disabled = value);
}

function load() {
  if (busy) return;
  const next = DIS.getDataset();
  if (DIS.datasetKey(next) !== DIS.datasetKey(dataset)) { selected.clear(); backendDataset = null; }
  dataset = next;
  ui("empty").hidden = Boolean(dataset?.rows?.length);
  ui("content").hidden = !dataset?.rows?.length;
  if (!dataset?.rows?.length) return;
  try { comparison = DIS_COMPARISON.prepare(dataset, DIS.getScenarios(), DIS); }
  catch (error) { ui("content").hidden = true; ui("empty").hidden = false; notice(error.message, true); return; }
  const ids = new Set(comparison.scenarios.map(item => item.id));
  selected = new Set([...selected].filter(id => ids.has(id)));
  if (!selected.size) comparison.scenarios.slice(-3).forEach(item => selected.add(item.id));
  ui("datasetInfo").textContent = `${dataset.name} · ${dataset.rows.length.toLocaleString()} rows · Currency: ${comparison.currency || "unspecified"}`;
  const messages = [];
  if (!comparison.scenarios.length) messages.push("No saved scenarios for this file yet. You can still download its business results.");
  if (comparison.excluded) messages.push(`${comparison.excluded} saved scenario(s) were left out because they belong to another file, need saving again, or have incomplete inputs.`);
  if (comparison.baseline.profit === null) messages.push("Profit comparison needs complete cost and expense data. Missing values are shown as unavailable.");
  ui("selectionNote").textContent = messages.join(" ");
  renderList(); render();
}

function renderList() {
  ui("list").replaceChildren(...comparison.scenarios.map(item => {
    const row = document.createElement("div"); row.className = "scenario-choice";
    const label = document.createElement("label"), input = document.createElement("input");
    input.type = "checkbox"; input.checked = selected.has(item.id);
    input.addEventListener("change", () => { input.checked ? selected.add(item.id) : selected.delete(item.id); render(); });
    label.append(input, document.createTextNode(" " + item.name));
    const remove = document.createElement("button"); remove.className = "btn danger small"; remove.textContent = "Delete";
    remove.setAttribute("aria-label", "Delete " + item.name);
    remove.onclick = () => { DIS.deleteScenario(item.id); selected.delete(item.id); load(); };
    row.append(label, remove); return row;
  }));
}

function render() {
  const list = chosen(), base = comparison.baseline;
  ui("comparisonCount").textContent = list.length ? `Comparing ${list.length} scenario(s) with the original data.` : "Showing the original data only. Downloads will include the business results without scenarios.";
  const columns = [{name:"Original (actual)", result:base}, ...list];
  const head = document.createElement("thead"), heading = document.createElement("tr");
  ["Metric", ...columns.map(item => item.name)].forEach(text => { const cell = document.createElement("th"); cell.textContent = text; heading.append(cell); });
  head.append(heading);
  const body = document.createElement("tbody");
  for (const [label, key] of [["Units sold","units"],["Revenue","revenue"],["Cost of goods","cogs"],["Marketing","marketing"],["Other expenses","expenses"],["Total costs","totalCosts"],["Net profit","profit"],["Net margin (%)","margin"]]) {
    const row = document.createElement("tr"), name = document.createElement("th"); name.scope = "row"; name.textContent = label; row.append(name);
    columns.forEach((item,index) => {
      const value = item.result[key], cell = document.createElement("td"); cell.className = "num";
      cell.textContent = number(key === "margin" && value !== null ? value * 100 : value);
      if (index && key !== "margin") {
        const delta = DIS_COMPARISON.change(value, base[key]);
        const extra = document.createElement("span"); extra.className = "comparison-delta";
        extra.textContent = delta.amount === null ? "" : delta.percent === null ? "Change: " + number(delta.amount) + "; percentage unavailable from zero" : (delta.percent >= 0 ? "+" : "") + number(delta.percent) + "% vs original";
        cell.append(extra);
      }
      row.append(cell);
    });
    body.append(row);
  }
  ui("table").style.minWidth = (120 * (columns.length + 1)) + "px";
  ui("table").replaceChildren(head,body);
  ui("risks").replaceChildren(...list.map(item => {
    const section = document.createElement("section"), title = document.createElement("h3"), inputs = document.createElement("p"), notes = document.createElement("ul");
    title.textContent = item.name;
    const p = item.params;
    inputs.textContent = `Price ${DIS.signedPct(p.price)}, unit costs ${DIS.signedPct(p.cost)}, marketing ${DIS.signedPct(p.marketing)}, other expenses ${DIS.signedPct(p.expenses)}. Price elasticity ${p.elasticity}; marketing lift ${p.marketingLift}.`;
    DIS.riskNotes(p,item.result,base).forEach(text => { const li = document.createElement("li"); li.textContent = text; notes.append(li); });
    section.append(title,inputs,notes); return section;
  }));
  if (chart) { chart.destroy(); chart = null; }
  ui("chartNote").textContent = base.profit === null ? "Profit is unavailable for this file. The table shows the figures that can be calculated." : !DIS.chartsAvailable() ? "The chart could not load. You can still use the table and downloads." : "";
  if (base.profit === null || !DIS.chartsAvailable()) return;
  chart = new Chart(ui("chart"), {type:"bar", data:{labels:columns.map(c=>c.name),datasets:[{label:"Net profit",data:columns.map(c=>c.result.profit),backgroundColor:columns.map((_,i)=>i ? "#3b5bdb" : "#a9b4cf")}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{title:{display:true,text:comparison.currency || "Currency unspecified"}}}}});
}

async function ensureBackendDataset() {
  const key = DIS.datasetKey(dataset);
  if (backendDataset?.key === key) {
    try { await DIS_API.getAnalysis(backendDataset.id); return backendDataset.id; } catch (_) { backendDataset = null; }
  }
  const file = new File([DIS.toBackendCSV(dataset)], dataset.name.replace(/\.[^.]+$/, "") + ".csv", {type:"text/csv"});
  const upload = await DIS_API.uploadFile(file);
  if (DIS.datasetKey(DIS.getDataset()) !== key) throw new Error("The selected dataset changed. Review the comparison before downloading.");
  backendDataset = {id:upload.dataset_id,key};
  return upload.dataset_id;
}

async function download(format) {
  if (busy || !dataset?.rows?.length) return;
  const list = chosen();
  if (list.length > 12) return notice("Select up to 12 scenarios for one report.",true);
  setBusy(true); notice(`Preparing the ${format.toUpperCase()} report from this file's results…`);
  try {
    const id = await ensureBackendDataset();
    const payload = DIS_COMPARISON.request(id, ui("reportTitle").value, list, ui("includeForecast").checked);
    await DIS_API.downloadReport(format,payload);
    notice(`${format.toUpperCase()} downloaded. The report includes the original results${list.length ? " and the selected scenarios" : ""}, findings and notes.`);
  } catch (error) { notice(error.message + " Start the backend from the main project folder if it is not running.", true); }
  finally { setBusy(false); }
}

ui("all").onclick = () => { comparison.scenarios.forEach(item=>selected.add(item.id)); renderList(); render(); };
ui("none").onclick = () => { selected.clear(); renderList(); render(); };
ui("downloadPdf").onclick = () => download("pdf");
ui("downloadCsv").onclick = () => download("csv");
ui("loadSample").onclick = () => { DIS.loadSample(); load(); };
window.addEventListener("storage", load);
load();
