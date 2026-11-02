/* Keep API keys on the server and display file contents as plain text. */
DIS.renderNav("assistant.html");
const ui = (id) => document.getElementById(id);
const SESSION_KEY = "dis.assistant.dataset";
let selected = null, analysis = null, scenario = null, busy = false;

function status(message, bad = false) {
  ui("status").textContent = message;
  ui("status").className = "notice " + (bad ? "bad" : "good");
}
function message(text, role, result = null) {
  const element = document.createElement("div");
  element.className = "message " + role;
  element.textContent = text;
  if (result) {
    const source = document.createElement("div");
    source.className = "provenance";
    source.textContent = result.source === "groq_grounded" ? "AI selected · verified business facts" : "Local grounded answer";
    const details = document.createElement("details"), summary = document.createElement("summary"), evidence = document.createElement("p");
    summary.textContent = "View answer sources";
    evidence.textContent = result.context_used.join(", ");
    details.append(summary, evidence);
    source.append(details);
    if (result.warnings.length) {
      const warning = document.createElement("p"); warning.textContent = result.warnings.join(" "); source.append(warning);
    }
    element.append(source);
  }
  ui("messages").append(element);
  ui("messages").scrollTop = ui("messages").scrollHeight;
}
function setBusy(value) {
  busy = value;
  ui("sendQuestion").disabled = value || !selected;
  ui("question").disabled = value || !selected;
  ["sampleData", "dashboardData", "businessFile", "scenarioSelect", "clearChat"].forEach(id => ui(id).disabled = value);
}
function listText(id, lines) {
  ui(id).replaceChildren(...lines.map(text => { const li = document.createElement("li"); li.textContent = text; return li; }));
}
function renderAnalysis() {
  const a = analysis;
  const format = (n) => n == null ? "Unavailable" : Number(n).toLocaleString(undefined, { maximumFractionDigits:2 });
  ui("findingsCard").hidden = ui("analysisCard").hidden = false;
  listText("findings", a.findings);
  listText("limitations", a.limitations);
  ui("analysisKpis").replaceChildren(...a.kpis.slice(0,4).map(k => {
    const card = document.createElement("div"); card.className = "kpi";
    const label = document.createElement("div"); label.className = "label"; label.textContent = k.label;
    const value = document.createElement("div"); value.className = "value"; value.textContent = format(k.value);
    card.append(label,value); return card;
  }));
  const rows = a.dataset_kind === "expenses" ? a.by_category : a.by_product;
  const columns = a.dataset_kind === "sales" ? ["product","revenue","units","gross_margin"] : a.dataset_kind === "expenses" ? ["category","amount","share_pct"] : ["product","description","stock","gross_margin"];
  const tr = document.createElement("tr");
  columns.forEach(c => { const th = document.createElement("th"); th.textContent = c.replaceAll("_"," "); tr.append(th); });
  ui("analysisHead").replaceChildren(tr);
  ui("analysisRows").replaceChildren(...rows.slice(0,10).map(r => {
    const tr = document.createElement("tr");
    columns.forEach(c => { const td = document.createElement("td"); td.textContent = typeof r[c] === "number" || r[c] == null ? format(r[c]) : String(r[c]); tr.append(td); }); return tr;
  }));
  ui("analysisNote").textContent = `Currency: ${a.currency || "unspecified"}. Margin/share values are percentages. Showing up to 10 records; the assistant checks the full product ranking. ${a.quality.analyzed_rows.toLocaleString()} rows analyzed; ${a.quality.duplicate_rows_removed} duplicate and ${a.quality.invalid_rows_excluded} invalid rows excluded.`;
}
function renderScenarios() {
  const select = ui("scenarioSelect");
  select.replaceChildren(new Option("Actual results", ""));
  const ds = DIS.getDataset();
  if (selected?.dashboardKey && selected.dashboardKey === DIS.datasetKey(ds)) {
    DIS.getScenarios().filter(s => s.datasetKey === selected.dashboardKey).forEach(s => select.add(new Option(s.name,s.id)));
  }
  scenario = null;
}
async function activate(upload, dashboardKey = null) {
  const nextAnalysis = await DIS_API.getAnalysis(upload.dataset_id);
  selected = {id:upload.dataset_id, name:upload.filename, dashboardKey};
  analysis = nextAnalysis;
  try { sessionStorage.setItem(SESSION_KEY,JSON.stringify(selected)); } catch (_) {}
  ui("messages").replaceChildren();
  message(`Selected ${selected.name}. I will answer using this file's ${analysis.dataset_kind} results.`,"assistant");
  ui("datasetInfo").textContent = `${selected.name} · ${analysis.quality.analyzed_rows.toLocaleString()} rows`;
  renderAnalysis(); renderScenarios();
  status("Dataset ready. Ask about the analysis or a what-if change.");
}
async function upload(file, dashboardKey = null) {
  setBusy(true); status("Uploading and analyzing the selected file…");
  try { await activate(await DIS_API.uploadFile(file),dashboardKey); }
  catch (error) { status(error.message, true); }
  finally { setBusy(false); }
}
function dashboardFile(ds) {
  return new File([DIS.toBackendCSV(ds)],ds.name.replace(/\.[^.]+$/,"") + ".csv",{type:"text/csv"});
}
ui("businessFile").onchange = e => { const file = e.target.files[0]; if(file) upload(file); e.target.value = ""; };
ui("sampleData").onclick = () => upload(new File([SAMPLE_CSV],"sample_sales.csv",{type:"text/csv"}));
ui("dashboardData").onclick = () => {
  const ds = DIS.getDataset();
  if (!ds?.rows?.length) return status("Load data on the Upload Data page first, or try sample sales here.", true);
  upload(dashboardFile(ds),DIS.datasetKey(ds));
};
ui("scenarioSelect").onchange = async () => {
  scenario = null;
  const saved = DIS.getScenarios().find(s => s.id === ui("scenarioSelect").value && s.datasetKey === selected.dashboardKey);
  if (!saved) return status("Question context: actual results.");
  setBusy(true);
  try {
    const base = await DIS_API.getBaseline(selected.id);
    const p = saved.params;
    scenario = await DIS_API.simulate(base,{price_pct:p.price || 0,cost_pct:p.cost || 0,marketing_pct:p.marketing || 0,expenses_pct:p.expenses || 0},{elasticity:p.elasticity,marketing_lift:p.marketingLift});
    status(`Selected scenario: ${saved.name}. Its estimates were recalculated for this dataset.`);
  } catch(error) { ui("scenarioSelect").value = ""; status(error.message,true); }
  finally { setBusy(false); }
};
ui("chatForm").onsubmit = async e => {
  e.preventDefault();
  const question = ui("question").value.trim();
  if (!question || busy || !selected) return;
  message(question,"user"); ui("question").value = ""; setBusy(true); status("Finding the relevant business facts…");
  try {
    const result = await DIS_API.chat(selected.id,question,scenario);
    message(result.answer,"assistant",result);
    status(result.source === "groq_grounded" ? "Answer checked against calculated facts." : "Answer ready from the local grounded question router.");
  } catch(error) { message(error.message,"assistant error"); status(error.message,true); }
  finally { setBusy(false); ui("question").focus(); }
};
ui("question").addEventListener("keydown", e => { if(e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ui("chatForm").requestSubmit(); } });
ui("suggestions").addEventListener("click", e => { if(e.target.tagName === "BUTTON" && selected && !busy) { ui("question").value = e.target.textContent; ui("chatForm").requestSubmit(); } });
ui("clearChat").onclick = () => { ui("messages").replaceChildren(); message("Conversation cleared. The selected dataset is unchanged.","assistant"); };
(async () => {
  if (!await DIS_API.checkHealth()) return status("Backend unavailable. Start python -m uvicorn main:app --port 8001, then refresh this page.",true);
  status("Backend connected. Upload a file or try sample sales.");
  try {
    const prior = JSON.parse(sessionStorage.getItem(SESSION_KEY));
    if (prior?.id) await activate({dataset_id:prior.id,filename:prior.name},prior.dashboardKey);
  } catch (_) { sessionStorage.removeItem(SESSION_KEY); status("Choose a dataset. Files must be uploaded again after the backend restarts."); }
  setBusy(false);
})();
