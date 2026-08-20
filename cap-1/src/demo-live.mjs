#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// CAP-1 APPLIED TO A REAL ENGINE — the before-and-after demonstration.
//
// Node built-ins only. No network. Two committed snapshots of a canonical
// Certisyn verdict document, taken from the live scan path either side of a
// real defect and its correction on 11 August 2026.
//
//   BEFORE  The engine published a catalogued total and an executed count and
//           left the remainder as arithmetic. CAP-1 refuses it: 221 units whose
//           fate is unrecorded. This is the defect the profile found in its own
//           author's engine on first contact.
//
//   AFTER   The engine publishes per-unit accounting for every unexecuted
//           check, derived from the module ledger, and asserts at build time
//           that the accounting reconciles with the count. CAP-1 conforms.
//
// The BEFORE snapshot is retained permanently. A profile whose author deletes
// the evidence that his own system failed it is not a profile.
// ─────────────────────────────────────────────────────────────────────────────
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { emit } from './emit.mjs';
import { verify, summarise } from './verify.mjs';

const here = (p) => new URL(p, import.meta.url);
const before = JSON.parse(readFileSync(here('./fixtures/certisyn-verdict-document-before.json'), 'utf8'));
const after  = JSON.parse(readFileSync(here('./fixtures/certisyn-verdict-document-after.json'), 'utf8'));

const show = (label, att) => {
  const r = verify(att);
  console.log(`${label}  ${r.ok ? 'CONFORMS' : 'REFUSED'}`);
  for (const s of summarise(att)) {
    const pct = (100 * s.fraction).toFixed(1).padStart(5);
    const d = Object.entries(s.dispositions).map(([k, v]) => `${k}=${v}`).join('  ') || 'none';
    console.log(`    ${String(s.id).padEnd(9)} ${String(s.examined).padStart(4)} / ${String(s.eligible).padEnd(4)} ${pct}%   ${d}`);
  }
  for (const f of r.failures) console.log(`    ${f.rule}  ${f.grounds}\n        ${JSON.stringify(f.evidence)}`);
  return r;
};

console.log('CAP-1 APPLIED TO A LIVE CERTISYN VERDICT DOCUMENT');
console.log('='.repeat(78));
console.log(`subject   ${after.subject?.ref}  ${after.subject?.media_type ?? ''}  ${after.subject?.size_bytes ?? ''} bytes`);
console.log('');

const a = emit(before);
const ra = show('BEFORE  engine publishes counts only     ', a);
console.log('');
const b = emit(after);
const rb = show('AFTER   engine publishes the accounting  ', b);

console.log('');
console.log('='.repeat(78));
const expected = !ra.ok && ra.failures.some(f => f.rule === 'R1-no-silent-remainder') && rb.ok;
console.log(expected
  ? 'RESULT  PASS   BEFORE is refused for the silent remainder; AFTER reconciles and conforms.'
  : 'RESULT  FAIL   the demonstration did not behave as specified.');

const record = {
  profile: 'cap/1', demonstration: 'cap-1-live/2.0.0',
  subject_ref: after.subject?.ref ?? null,
  before: { conforms: ra.ok, refused_by: [...new Set(ra.failures.map(f => f.rule))],
            remainder: ra.failures.find(f => f.rule === 'R1-no-silent-remainder')?.evidence?.remainder ?? null },
  after:  { conforms: rb.ok, strata: summarise(b) },
  defect_closed: 'apps/core/src/lib/forensics/index.ts now emits coverage.not_run_units, one entry per unexecuted catalogued check, and throws rather than emit a remainder that reconciles only by arithmetic.',
  establishes: 'That the profile detects an unaccounted remainder in a real production engine, and that closing it is a bounded change which the profile then accepts.',
  does_not_establish: 'Specification adequacy. Producer and verifier share an author. It becomes two-sided the first time the verifier refuses a document its author did not write.'
};
record.record_digest = createHash('sha256').update(JSON.stringify(record)).digest('hex');
writeFileSync(here('./runs/live_run.json'), JSON.stringify(record, null, 1));
console.log(`RECORD  runs/live_run.json   sha256 ${record.record_digest}`);
process.exit(expected ? 0 : 1);
