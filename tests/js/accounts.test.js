const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

function environment(fetcher = async () => ({ok:true, json:async () => ({})})) {
  const values = new Map(), session = new Map();
  const context = vm.createContext({
    localStorage:{getItem:key => values.get(key), setItem:(key,value) => values.set(key,value), removeItem:key => values.delete(key)},
    sessionStorage:{getItem:key => session.get(key), setItem:(key,value) => session.set(key,value), removeItem:key => session.delete(key)},
    fetch:fetcher, Blob, FormData,
  });
  vm.runInContext(fs.readFileSync(require.resolve('../../js/app.js'),'utf8') + ';this.dis=DIS;', context);
  return {dis:context.dis, values, session};
}

test('guest and different accounts keep independent browser data', () => {
  const {dis,session} = environment();
  dis.setDataset({name:'guest'});
  session.set('dis.assistant.dataset','private selection');
  dis.setAccount({id:1,email:'one@example.com'});
  assert.equal(dis.getDataset(), null);
  assert.equal(session.get('dis.assistant.dataset'), undefined);
  dis.setDataset({name:'first user'});
  dis.setAccount({id:2,email:'two@example.com'});
  assert.equal(dis.getDataset(), null);
  dis.setDataset({name:'second user'});
  dis.setAccount({id:1,email:'one@example.com'});
  assert.equal(dis.getDataset().name, 'first user');
  dis.setAccount(null);
  assert.equal(dis.getDataset().name, 'guest');
});

test('failed server save never claims a scenario is saved locally', async () => {
  const {dis} = environment(async () => ({ok:false,json:async () => ({error:{message:'Please sign in again'}})}));
  dis.setAccount({id:1});
  dis.setDataset({name:'sales.csv',backendId:'owned',rows:[]});
  await assert.rejects(() => dis.saveScenario({name:'Test'}), /Please sign in again/);
  assert.equal(dis.getScenarios().length,0);
});

test('account scenario saves use dataset ID and cookies without storing bearer tokens', async () => {
  const calls = [];
  const {dis,values} = environment(async (path, options) => {
    calls.push({path,options});
    return {ok:true,json:async () => path.endsWith('saved/scenarios') ? {id:42} : {}};
  });
  dis.setAccount({id:1});
  dis.setDataset({name:'sales.csv',backendId:'owned',rows:[]});
  const saved = await dis.saveScenario({name:'Price +10%',params:{price:0.1}});
  assert.equal(saved.serverId,42);
  assert.equal(saved.datasetKey,'owned');
  const request = calls.find(call => call.path.endsWith('saved/scenarios'));
  assert.equal(request.options.credentials,'same-origin');
  assert.equal(JSON.parse(request.options.body).dataset_id,'owned');
  assert.equal([...values.values()].some(value => value.includes('access_token')),false);
  await dis.deleteScenario(saved.id);
  assert.equal(calls.at(-1).options.method,'DELETE');
  assert.equal(dis.getScenarios().length,0);
});

test('failed scenario deletion keeps the existing scenario available', async () => {
  const {dis} = environment(async () => ({ok:false,json:async () => ({error:{message:'Database unavailable'}})}));
  dis.setAccount({id:1});
  dis.setScenarios([{id:'local',serverId:42}]);
  await assert.rejects(() => dis.deleteScenario('local'), /Database unavailable/);
  assert.equal(dis.getScenarios().length,1);
});
