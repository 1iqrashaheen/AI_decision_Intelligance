const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");

for (const url of ["https://example.vercel.app", "http://localhost:8001", "http://127.0.0.1:5500", "file:///project/index.html"]) {
  test(`API routing and health request from ${url}`, async () => {
    const location = new URL(url);
    const calls = [];
    const context = vm.createContext({
      window: {location, addEventListener() {}},
      document: {getElementById() {}, querySelector() {}},
      fetch: async (url) => { calls.push(url); return {ok:true, json:async () => ({status:"ok"})}; },
    });
    vm.runInContext(fs.readFileSync(require.resolve("../../js/api.js"), "utf8") + ";globalThis.api = DIS_API;", context);
    assert.equal(await context.api.checkHealth(), true);
    const expected = location.hostname === "example.vercel.app" ? location.origin : "http://localhost:8001";
    // A local server on port 8001 keeps its current hostname.
    assert.equal(calls[0], `${expected}/api/health`);
  });
}
