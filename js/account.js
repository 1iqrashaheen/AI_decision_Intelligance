DIS.renderNav('account.html');
const field = id => document.getElementById(id);
function status(text, bad = false) {
  field('status').textContent = text;
  field('status').className = 'notice ' + (bad ? 'bad' : 'good');
}
function busy(value) {
  document.querySelectorAll('button').forEach(button => button.disabled = value);
}
async function showAccount(user) {
  DIS.setAccount(user);
  DIS.renderNav('account.html');
  field('signedIn').hidden = !user;
  field('signedOut').hidden = Boolean(user);
  if (!user) return;
  field('identity').textContent = user.email;
  const datasets = await DIS.accountRequest('saved/datasets');
  field('datasets').replaceChildren(...datasets.map(ds => new Option(ds.filename + ' · ' + ds.uploaded_at, ds.id)));
  field('restore').disabled = !datasets.length;
}
field('credentials').onsubmit = async event => {
  event.preventDefault();
  busy(true);
  try {
    const action = event.submitter?.value || 'login';
    const result = await DIS.accountRequest('auth/' + action, {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email:field('email').value.trim(), password:field('password').value})});
    field('password').value = '';
    await showAccount(result.user);
    status('Signed in. You can upload new data or open a saved dataset.');
  } catch (error) { status(error.message, true); }
  finally { busy(false); field('restore').disabled = !field('datasets').options.length; }
};
field('logout').onclick = async () => {
  busy(true);
  try {
    await DIS.accountRequest('auth/logout', {method:'POST'});
    await showAccount(null);
    status('Signed out. Your saved data remains in your account.');
  } catch (error) { status(error.message, true); }
  finally { busy(false); }
};
field('restore').onclick = async () => {
  busy(true);
  try {
    const id = field('datasets').value;
    const data = await DIS.accountRequest('saved/datasets/' + encodeURIComponent(id));
    const analysis = await DIS.accountRequest('analysis/' + encodeURIComponent(id));
    const scenarios = await DIS.accountRequest('saved/scenarios');
    const saved = scenarios.map(row => ({...row.scenario, id:'server-' + row.id, serverId:row.id,
      name:row.name, datasetKey:row.dataset_id, savedAt:row.created_at}));
    if (analysis.dataset_kind !== 'sales') {
      sessionStorage.setItem('dis.assistant.dataset', JSON.stringify({id, name:data.filename}));
      window.location.href = 'assistant.html';
      return;
    }
    const headers = Object.keys(data.rows[0] || {});
    const clean = DIS.cleanRows(data.rows, DIS.detectMapping(headers));
    if (!clean.rows.length || clean.rows.length !== data.rows.length || clean.report.filledZero) {
      // Preserve the full server dataset when the sales-only dashboard cannot represent it.
      sessionStorage.setItem('dis.assistant.dataset', JSON.stringify({id, name:data.filename}));
      window.location.href = 'assistant.html';
      return;
    }
    const ds = {name:data.filename, loadedAt:data.uploaded_at, backendId:id, rows:clean.rows, report:clean.report};
    if (!DIS.setDataset(ds) || !DIS.setScenarios(saved)) throw new Error('This browser has insufficient storage. Try a smaller file.');
    window.location.href = 'index.html';
  } catch (error) { status(error.message, true); busy(false); }
};
(async () => {
  try {
    const user = await DIS.accountRequest('auth/me');
    await showAccount(user);
    status('Your account is ready.');
  } catch (error) {
    await showAccount(null);
    status(error.message.includes('Register or log in') ? 'Sign in or create an account. You can also use the guest demo.' : error.message, true);
  }
})();
