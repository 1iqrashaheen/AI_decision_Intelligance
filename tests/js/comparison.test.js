const test = require("node:test");
const assert = require("node:assert/strict");
const DIS = require("../../js/app.js");
const comparison = require("../../js/comparison.js");

function dataset(name="sales.csv") {
  return {name,loadedAt:"2026-10-28T10:00:00Z",rows:[
    {date:"2024-01-01",product:"Alpha",units:10,price:20,unit_cost:8,marketing_spend:5,expenses:15},
    {date:"2024-02-01",product:"Beta",units:5,price:10,unit_cost:7,marketing_spend:2,expenses:3},
  ],report:{filledZero:0}};
}

function scenario(ds, overrides={}) {
  return {id:"one",name:"Price +10%",datasetKey:DIS.datasetKey(ds),
    params:{price:.1,cost:0,marketing:0,expenses:0,elasticity:-1.2,marketingLift:.15},
    result:{revenue:999999,profit:999999}, ...overrides};
}

test("only compare scenarios saved for this exact dataset",()=>{
  const ds=dataset(),other=dataset("other.csv");
  const r=comparison.prepare(ds,[scenario(ds),scenario(other,{id:"other"}),scenario(ds,{id:"legacy",datasetKey:undefined})],DIS);
  assert.equal(r.scenarios.length,1);
  assert.equal(r.excluded,2);
});
test("recalculate stale saved totals using the existing engine",()=>{
  const ds=dataset(),r=comparison.prepare(ds,[scenario(ds)],DIS);
  assert.equal(r.baseline.profit,110);
  assert.ok(Math.abs(r.scenarios[0].result.revenue-242)<.001);
  assert.ok(Math.abs(r.scenarios[0].result.profit-115.8)<.001);
});
test("missing or imputed expenses must not create profit",()=>{
  const ds=dataset(); ds.report.filledZero=1;
  const r=comparison.prepare(ds,[scenario(ds)],DIS);
  assert.equal(r.baseline.profit,null);
  assert.equal(r.scenarios.length,0);
  assert.equal(r.baseline.cogs,115);
});
test("zero baseline has no invented percentage change",()=>{
  assert.deepEqual(comparison.change(20,0),{amount:20,percent:null});
  assert.deepEqual(comparison.change(null,10),{amount:null,percent:null});
});
test("corrupt and nonfinite assumptions are excluded",()=>{
  const ds=dataset(),s=scenario(ds);s.params.elasticity=Infinity;
  assert.equal(comparison.prepare(ds,[s],DIS).scenarios.length,0);
});
test("export requests contain inputs rather than saved result figures",()=>{
  const ds=dataset(),r=comparison.prepare(ds,[scenario(ds)],DIS);
  const request=comparison.request("upload-id","Team report",r.scenarios);
  assert.equal(request.dataset_id,"upload-id");
  assert.equal(request.scenarios[0].changes.price_pct,.1);
  assert.equal(request.scenarios[0].revenue,undefined);
  assert.equal(comparison.request("upload-id","",[]).scenarios.length,0);
  assert.throws(()=>comparison.request("upload-id","Report",Array(13).fill(r.scenarios[0])));
  assert.throws(()=>comparison.request("upload-id","Report",[{...r.scenarios[0],name:"   "}]));
});
test("shared upload conversion preserves quoted product names and missing costs",()=>{
  const ds=dataset();ds.rows[0].product='Item, "quoted"';ds.report.filledZero=1;
  const parsed=DIS.parseCSV(DIS.toBackendCSV(ds));
  assert.equal(parsed.records[0].product,'Item, "quoted"');
  assert.equal(parsed.records[0].marketing_spend,"");
  assert.equal(parsed.records[0].expenses,"");
  assert.equal(parsed.records[0].unit_cost,"8");
});
