#!/usr/bin/env node
// =============================================================================
// VERIFIER MUTATION TESTING
//
// The conformance class proves that a defective DOCUMENT is refused. It says
// nothing about whether a defective VERIFIER would be caught. This does.
//
// Each mutant is the verifier with exactly one normative rule silenced. The
// class is then run against the mutant. If the class still passes, that rule
// has no control exercising it and the class is reporting coverage it does not
// have. Eight rules, eight mutants, eight expected failures.
// =============================================================================
import { readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { positives, negatives } from './vectors.mjs';

const RULES = ['R1-no-silent-remainder','R2-closed-disposition','R3-withholding-digest-bound',
  'R4-denominator-basis','R5-counts-well-formed','R6-absence-is-scoped',
  'R7-incomplete-not-clean','R8-supports-bounds-citation'];

const src = readFileSync(new URL('./verify.mjs', import.meta.url), 'utf8');
// Silence one rule by making the failure recorder ignore it. One-line injection,
// so the mutant differs from the original by exactly one behaviour.
const inject = (rule) => src.replace(
  'const F = (rule, grounds, evidence) => fail.push({ rule, grounds, evidence });',
  `const F = (rule, grounds, evidence) => { if (rule === ${JSON.stringify(rule)}) return; fail.push({ rule, grounds, evidence }); };`);

const runClass = async (verifyFn) => {
  let pass = 0, fail = 0;
  for (const v of positives) { const r = verifyFn(v.doc); r.ok ? pass++ : fail++; }
  for (const v of negatives) {
    const r = verifyFn(v.doc);
    (!r.ok && r.failures.some(f => f.rule === v.rule)) ? pass++ : fail++;
  }
  return { pass, fail };
};

console.log('VERIFIER MUTATION TESTING');
console.log('='.repeat(78));
console.log('  each mutant silences exactly one normative rule; the class must then FAIL');
console.log('');

const rows = []; let survived = 0;
// baseline
const base = await import('./verify.mjs');
const b = await runClass(base.verify);
console.log(`  baseline   ${b.fail === 0 ? 'PASS' : 'FAIL'}   ${b.pass}/${b.pass + b.fail}`);
if (b.fail !== 0) { console.log('  baseline is not green; aborting'); process.exit(1); }
console.log('');

for (const rule of RULES) {
  const path = new URL(`./.mutant-${rule}.mjs`, import.meta.url);
  writeFileSync(path, inject(rule));
  const m = await import(path.href + `?v=${rule}`);
  const r = await runClass(m.verify);
  const killed = r.fail > 0;          // class went red => the mutant was caught
  if (!killed) survived++;
  rows.push({ rule, killed, failed_checks: r.fail, passed: r.pass });
  console.log(`  ${rule.padEnd(30)} ${killed ? 'KILLED' : 'SURVIVED  <-- rule is unexercised'}   ${r.fail} check(s) failed`);
  unlinkSync(path);
}

console.log('');
console.log('='.repeat(78));
const ok = survived === 0;
console.log(`RESULT  ${ok ? 'PASS' : 'FAIL'}   ${RULES.length - survived} of ${RULES.length} mutants killed`);
const rec = { class: 'cap-1-mutation/1.0.0', rules: RULES.length, killed: RULES.length - survived,
  survived, results: rows,
  establishes: 'Every normative rule is load-bearing: silencing any one of them makes the conformance class fail, so no rule is present without a control exercising it.',
  does_not_establish: 'That the rules are sufficient. A rule absent from the specification entirely cannot be mutated, and would not be detected by this method.' };
rec.record_digest = createHash('sha256').update(JSON.stringify(rec)).digest('hex');
writeFileSync(new URL('./runs/mutation_run.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(`RECORD  runs/mutation_run.json   sha256 ${rec.record_digest}`);
process.exit(ok ? 0 : 1);
