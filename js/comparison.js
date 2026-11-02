/* Use the existing simulator for comparison; keep files and scenarios separate. */
const DIS_COMPARISON = (() => {
  const moneyFields = ["revenue", "cogs", "marketing", "expenses", "totalCosts", "profit"];

  function baseFor(dataset, engine) {
    const base = engine.totals(dataset.rows);
    const complete = key => dataset.rows.every(row => typeof row[key] === "number" && Number.isFinite(row[key]) && row[key] >= 0);
    if (!complete("units") || !complete("price")) throw new Error("The saved sales data contains invalid units or prices. Upload the file again.");
    if (!complete("unit_cost")) base.cogs = null;
    if (!complete("marketing_spend") || dataset.report?.filledZero > 0) base.marketing = null;
    if (!complete("expenses") || dataset.report?.filledZero > 0) base.expenses = null;
    if ([base.cogs, base.marketing, base.expenses].some(value => value === null)) {
      base.totalCosts = base.profit = base.margin = null;
    } else if (!base.revenue) {
      base.margin = null;
    }
    return base;
  }

  function prepare(dataset, saved, engine) {
    if (!dataset?.rows?.length) return { baseline:null, scenarios:[], excluded:saved.length, currency:null };
    const baseline = baseFor(dataset, engine);
    const key = engine.datasetKey(dataset);
    const scenarios = [];
    for (const item of saved) {
      if (!item.datasetKey || item.datasetKey !== key || baseline.profit === null) continue;
      const params = { ...engine.DEFAULT_ASSUMPTIONS, ...item.params };
      const changes = ["price", "cost", "marketing", "expenses"];
      if (!changes.every(k => Number.isFinite(params[k]) && params[k] >= -1 && params[k] <= 5)) continue;
      if (![params.elasticity, params.marketingLift].every(Number.isFinite)) continue;
      const result = engine.simulate(dataset.rows, params);
      if (!["units", ...moneyFields, "margin"].every(k => Number.isFinite(result[k]))) continue;
      scenarios.push({ ...item, params, result, baseline });
    }
    return { baseline, scenarios, excluded:saved.length - scenarios.length, currency:dataset.currency || null };
  }

  function change(current, original) {
    if (current === null || original === null) return { amount:null, percent:null };
    const amount = current - original;
    return { amount, percent:original === 0 ? null : amount / Math.abs(original) * 100 };
  }

  function request(datasetId, title, chosen, includeForecast = false) {
    if (!datasetId) throw new Error("Select a dataset before exporting a report.");
    if (chosen.length > 12) throw new Error("Select up to 12 scenarios for one report.");
    if (chosen.some(item => !item.name?.trim() || item.name.length > 120)) throw new Error("Scenario names must be between 1 and 120 characters. Save the scenario again with a shorter name.");
    return { dataset_id:datasetId, title:title.trim() || "Business decision report", include_forecast:includeForecast,
      scenarios:chosen.map(item => ({ name:item.name, case:item.case || "custom",
        changes:{price_pct:item.params.price, cost_pct:item.params.cost, marketing_pct:item.params.marketing, expenses_pct:item.params.expenses},
        assumptions:{elasticity:item.params.elasticity, marketing_lift:item.params.marketingLift} })) };
  }

  return { prepare, change, request };
})();

if (typeof module !== "undefined") module.exports = DIS_COMPARISON;
