#!/usr/bin/env node
// Third implementation, exercised where it will actually be used.
//
// verify.html is the implementation most relying parties will run, because it is
// the only one that needs nothing installed. An implementation the conformance
// class does not exercise is an implementation nobody has checked. This runs it
// in a real browser engine, over the same fifteen vectors as the other two, and
// records every network request the page attempts.
//
// Two things are established here and they are separate:
//   1. Agreement — verify.html agrees with verify.mjs on all fifteen vectors,
//      rule for rule, which makes the cross-implementation class three-sided.
//   2. Isolation — the page issues no request other than the local document
//      itself. This is observed at the browser's request interception layer,
//      not inferred from a substring search over the source.
//
// Requires playwright and a chromium build. If neither is present this exits 3
// and says so, rather than passing quietly.

import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { verify as verifyNode } from './verify.mjs';
import { positives, negatives } from './vectors.mjs';

// playwright is a harness dependency, not a dependency of the verifier. The
// verifier under test has none, which is the whole point of it. Resolve from the
// local tree, then from the global root, then give up loudly.
let chromium;
{
  const { execSync } = await import('node:child_process');
  const candidates = ['playwright'];
  try {
    candidates.push(`${execSync('npm root -g', { encoding: 'utf8' }).trim()}/playwright/index.js`);
  } catch { /* npm not present; the local candidate is all there is */ }
  for (const c of candidates) {
    try {
      const m = await import(c);
      chromium = m.chromium ?? m.default?.chromium;
      if (chromium) break;
    } catch { /* try the next */ }
  }
  if (!chromium) {
    console.error('browsercheck: playwright is not available. This class did not run.');
    console.error('That is a gap, not a pass. Install playwright or record the omission.');
    process.exit(3);
  }
}

const htmlPath = new URL('./verify.html', import.meta.url);
const html = readFileSync(htmlPath, 'utf8');
const htmlDigest = createHash('sha256').update(html).digest('hex');

const cases = [
  ...positives.map((v) => ({ id: v.id, kind: 'positive', doc: v.doc, expect: 'conform' })),
  ...negatives.map((v) => ({ id: v.id, kind: 'negative', doc: v.doc, expect: 'refuse', rule: v.rule })),
];

const requests = [];
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();

// Every request the page attempts, of every resource type, including the
// document load itself. Nothing is allowed through that is not recorded.
context.on('request', (r) => requests.push({ url: r.url(), method: r.method(), type: r.resourceType() }));

const page = await context.newPage();
await page.goto(htmlPath.href, { waitUntil: 'load' });

const disagreements = [];
const incorrect = [];

for (const c of cases) {
  const inBrowser = await page.evaluate((doc) => {
    const r = verify(doc);
    return { ok: r.ok, rules: (r.failures || []).map((f) => f.rule).sort() };
  }, c.doc);

  const inNode = verifyNode(c.doc);
  const nodeRules = (inNode.failures || []).map((f) => f.rule).sort();

  if (inBrowser.ok !== inNode.ok || JSON.stringify(inBrowser.rules) !== JSON.stringify(nodeRules)) {
    disagreements.push({ id: c.id, browser: inBrowser, node: { ok: inNode.ok, rules: nodeRules } });
  }

  const conformed = inBrowser.ok;
  const wanted = c.expect === 'conform';
  if (conformed !== wanted) incorrect.push({ id: c.id, expected: c.expect, got: conformed ? 'conform' : 'refuse' });
  // A negative control must be refused by the rule it targets, not by some other rule.
  if (c.kind === 'negative' && !inBrowser.rules.includes(c.rule)) {
    incorrect.push({ id: c.id, expected_rule: c.rule, got_rules: inBrowser.rules });
  }
}

await browser.close();

// The document itself is a file:// load and is expected. Anything else is not.
const external = requests.filter((r) => !r.url.startsWith('file://'));

const record = {
  class: 'cap-1-browser-implementation/1.0.0',
  implementation: 'verify.html (single file, browser engine)',
  engine: 'chromium, headless, request interception enabled',
  subject_digest: { algorithm: 'SHA-256', value: htmlDigest },
  vectors: cases.length,
  disagreements,
  incorrect,
  agreement: disagreements.length === 0 && incorrect.length === 0,
  network: {
    requests_observed: requests.length,
    external_requests: external.length,
    external_detail: external,
    method: 'BrowserContext request events, every resource type, recorded before dispatch',
  },
  establishes:
    'The single-file HTML verifier agrees with the reference implementation on every vector and refuses each negative control by the rule it targets, and issues no request beyond the local document. Isolation is observed at the interception layer rather than inferred from the source text.',
  does_not_establish:
    'Author independence. All three implementations and the vectors originate with the same party. It also does not establish behaviour in engines other than the one recorded above.',
};

record.record_digest = createHash('sha256')
  .update(JSON.stringify({ ...record, record_digest: undefined }))
  .digest('hex');

writeFileSync(new URL('./runs/browser_run.json', import.meta.url), JSON.stringify(record, null, 1));

const bad = disagreements.length + incorrect.length + external.length;
console.log(
  `browser implementation: ${cases.length} vectors, ${disagreements.length} disagreements, ` +
    `${incorrect.length} incorrect, ${requests.length} request(s) observed, ${external.length} external`,
);
if (bad) {
  console.error('browsercheck FAILED');
  process.exit(1);
}
console.log('verify.html agrees with verify.mjs on every vector and reached nothing.');
