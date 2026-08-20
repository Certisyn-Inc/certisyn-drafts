#!/usr/bin/env node
// CAP-1 conformance runner. One command, no arguments, no network, no clock.
//   node run.mjs
import { verify } from './verify.mjs';
import { positives, negatives } from './vectors.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';

const rows = []; let pass = 0, fail = 0;
const line = (s) => console.log(s);

line('CAP-1 CONFORMANCE CLASS');
line('='.repeat(78));
line('');
line('POSITIVE VECTORS — each must conform');
for (const v of positives) {
  const r = verify(v.doc);
  const ok = r.ok; ok ? pass++ : fail++;
  rows.push({ id: v.id, kind: 'positive', expected: 'conform', ok, rules: r.failures.map(f => f.rule) });
  line(`  ${v.id}  ${ok ? 'CONFORMS' : 'REFUSED  <-- UNEXPECTED'}   ${v.why}`);
  if (!ok) for (const f of r.failures) line(`         ${f.rule}: ${f.grounds}`);
}

line('');
line('NEGATIVE CONTROLS — each must be refused, BY THE RULE IT TARGETS');
for (const v of negatives) {
  const r = verify(v.doc);
  const hit = r.failures.some(f => f.rule === v.rule);
  const ok = !r.ok && hit;
  ok ? pass++ : fail++;
  rows.push({ id: v.id, kind: 'negative', target: v.rule, ok,
              refused: !r.ok, rules: [...new Set(r.failures.map(f => f.rule))] });
  const verdict = r.ok ? 'ACCEPTED  <-- CONTROL DID NOT FIRE'
                : hit  ? 'REFUSED'
                       : 'REFUSED BY THE WRONG RULE  <-- NOT COUNTED';
  line(`  ${v.id}  ${verdict}   ${v.rule}`);
  line(`         ${v.why}`);
  if (!r.ok && !hit) line(`         fired instead: ${[...new Set(r.failures.map(f => f.rule))].join(', ')}`);
}

// Rule coverage: which normative rules have at least one control that fires on them.
const RULES = ['R1-no-silent-remainder','R2-closed-disposition','R3-withholding-digest-bound',
  'R4-denominator-basis','R5-counts-well-formed','R6-absence-is-scoped',
  'R7-incomplete-not-clean','R8-supports-bounds-citation'];
const exercised = new Set(negatives.filter(v => {
  const r = verify(v.doc); return !r.ok && r.failures.some(f => f.rule === v.rule);
}).map(v => v.rule));
const unexercised = RULES.filter(r => !exercised.has(r));

line('');
line('RULE COVERAGE');
line(`  normative rules      ${RULES.length}`);
line(`  exercised by control ${exercised.size}`);
line(`  unexercised          ${unexercised.length ? unexercised.join(', ') : 'none'}`);

line('');
line('DECLARED GAPS — stated rather than left to be found');
line('  · R0 shape rules are exercised only incidentally. A malformed document is refused,');
line('    but no control isolates each shape rule individually.');
line('  · The class tests the VERIFIER against its own vectors. Producer and verifier here');
line('    share an author, so this establishes that the rules are implementable and that');
line('    every rule fires against an injected defect. It establishes nothing about the');
line('    adequacy of the specification. The class becomes two-sided the first time it');
line('    refuses a document its author did not write.');
line('  · No timing, ordering or concurrency property is tested. None is claimed.');

const record = { profile: 'cap/1', class: 'cap-1-conformance/1.0.0',
  positives: positives.length, negatives: negatives.length, passed: pass, failed: fail,
  rules_total: RULES.length, rules_exercised: [...exercised].sort(), rules_unexercised: unexercised,
  establishes: 'The eight normative rules are implementable and each fires against an injected defect in a document differing from the positive base by exactly one mutation.',
  does_not_establish: 'Specification adequacy, producer independence, timing behaviour, or conformance of any implementation other than the reference verifier in this directory.',
  results: rows };
record.record_digest = createHash('sha256').update(JSON.stringify(record)).digest('hex');
mkdirSync(new URL('./runs/', import.meta.url), { recursive: true });
writeFileSync(new URL('./runs/conformance_run.json', import.meta.url), JSON.stringify(record, null, 1));

line('');
line('='.repeat(78));
line(`RESULT  ${fail === 0 ? 'PASS' : 'FAIL'}   ${pass} of ${pass + fail} checks`);
line(`RECORD  runs/conformance_run.json   sha256 ${record.record_digest}`);
process.exit(fail === 0 ? 0 : 1);
