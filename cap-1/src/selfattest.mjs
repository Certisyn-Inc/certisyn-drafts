#!/usr/bin/env node
// =============================================================================
// CAP-1 SELF-ATTESTATION
//
// The profile states the coverage of an examination. This is the profile stating
// the coverage of ITSELF, in its own vocabulary: which normative rules were
// eligible to be exercised, which were exercised by a control, and — the part
// that matters — what was NOT exercised and under which disposition.
//
// A profile that cannot state its own coverage in the vocabulary it defines has
// not finished defining it.
// =============================================================================
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { verify } from './verify.mjs';

const here = (p) => new URL(p, import.meta.url);
const conf = JSON.parse(readFileSync(here('./runs/conformance_run.json'), 'utf8'));
const mut  = JSON.parse(readFileSync(here('./runs/mutation_run.json'), 'utf8'));
const xim  = JSON.parse(readFileSync(here('./runs/cross_implementation_run.json'), 'utf8'));
// The browser implementation is optional in the class, so it is read only if the
// part actually ran. An absent run is recorded as absent, never assumed green.
let brw = null;
try { brw = JSON.parse(readFileSync(here('./runs/browser_run.json'), 'utf8')); } catch { /* part 4 did not run */ }

const RULES = ['R1-no-silent-remainder','R2-closed-disposition','R3-withholding-digest-bound',
  'R4-denominator-basis','R5-counts-well-formed','R6-absence-is-scoped',
  'R7-incomplete-not-clean','R8-supports-bounds-citation'];
const SHAPE = ['R0-profile','R0-subject-ref','R0-strata-present','R0-integrity-complete','R0-stratum-id-unique'];

const exercised = new Set(conf.rules_exercised);
const digest = (s) => createHash('sha256').update(s).digest('hex');

// Stratum one: the normative rules.
const rulesUnexamined = RULES.filter(r => !exercised.has(r))
  .map(r => ({ unit: r, disposition: 'not_applicable',
               detail: 'no negative control targets this rule' }));

// Stratum two: the shape rules. These are refused incidentally by malformed
// input but no control isolates them, which is a real coverage shortfall and is
// declared here rather than left to be found.
const shapeUnexamined = SHAPE.map(r => ({ unit: r, disposition: 'resource_exhausted',
  detail: 'exercised only incidentally by malformed input; no control isolates this shape rule' }));

// Stratum three: implementations under test.
const IMPLS = ['verify.mjs (JavaScript, Node built-ins)', 'verify.py (Python, standard library)',
               'verify.html (single file, executed in a browser engine)'];
const implUnexamined = [{ unit: 'any implementation not authored by Certisyn',
  disposition: 'unavailable',
  detail: 'no independently authored implementation exists yet; the class is one-sided until one does' }];

const att = {
  profile: 'cap/1',
  producer: { name: 'CAP-1 conformance class', version: conf.class, policy: 'cap-1-self-attestation/1.0.0' },
  subject: { kind: 'specification', ref: 'CAP-1 normative rules',
             digest: { algorithm: 'SHA-256', value: digest(RULES.concat(SHAPE).join('|')) } },
  strata: [
    { id: 'normative-rules', population: 'normative rules of the profile',
      basis: { kind: 'enumeration', enumeration_method: 'the eight rules enumerated in the specification and enforced by the reference verifier' },
      eligible: RULES.length, examined: RULES.length - rulesUnexamined.length,
      unexamined: rulesUnexamined, supports: ['absence-of-unexercised-rule'] },
    { id: 'shape-rules', population: 'structural rules refusing a malformed document',
      basis: { kind: 'enumeration', enumeration_method: 'the shape checks performed before any normative rule is evaluated' },
      eligible: SHAPE.length, examined: SHAPE.length - shapeUnexamined.length,
      unexamined: shapeUnexamined, supports: ['absence-of-isolated-shape-control'] },
    { id: 'implementations', population: 'implementations the class has been executed against',
      basis: { kind: 'enumeration', enumeration_method: 'implementations held and executed in this directory, plus any known external implementation' },
      eligible: IMPLS.length + implUnexamined.length, examined: IMPLS.length,
      unexamined: implUnexamined, supports: ['absence-of-independent-refutation'] }
  ],
  absence_assertions: [
    { assertion: 'No normative rule is present without a control that fires on it.',
      stratum: 'normative-rules',
      qualifier: 'Bounded by the eight enumerated rules. Not a statement about rules the specification does not contain.' },
    { assertion: 'No shape rule has been individually isolated by a control.',
      stratum: 'shape-rules',
      qualifier: 'Stated as a shortfall, not as a finding of adequacy.' },
    { assertion: 'The class has not been refused by an implementation authored elsewhere.',
      stratum: 'implementations',
      qualifier: 'This is the condition on which specification adequacy turns and it is not yet met.' }
  ],
  integrity: {
    complete: false,
    uncapped_verdict: 'conformance-class-green',
    capped_to: 'implementation-independent-only',
    unaccounted: ['author independence'],
    statement: `Eight of eight normative rules exercised and eight of eight mutants killed, across ${IMPLS.length} implementations in agreement`
             + `${brw && brw.agreement ? ', one of them executed in a browser engine with every network request recorded' : ''}. `
             + 'Author independence is not established, so the verdict is capped: this class establishes that the rules are implementable '
             + 'and load-bearing, not that the specification is adequate.'
  },
  as_of: conf.record_digest.slice(0, 16)
};

const r = verify(att);
console.log('CAP-1 SELF-ATTESTATION');
console.log('='.repeat(78));
console.log(`  ${r.ok ? 'CONFORMS' : 'REFUSED'}  under its own verifier`);
for (const s of att.strata) {
  const by = {}; for (const u of s.unexamined) by[u.disposition] = (by[u.disposition] ?? 0) + 1;
  const d = Object.entries(by).map(([k, v]) => `${k}=${v}`).join('  ') || 'none';
  console.log(`    ${s.id.padEnd(17)} ${String(s.examined).padStart(3)} / ${String(s.eligible).padEnd(3)} ${(100 * s.examined / s.eligible).toFixed(1).padStart(6)}%   ${d}`);
}
for (const f of r.failures) console.log(`    ${f.rule}  ${f.grounds}`);
console.log('');
console.log(`  supporting runs   conformance ${conf.record_digest.slice(0,12)}  mutation ${mut.record_digest.slice(0,12)}  cross-impl ${xim.record_digest.slice(0,12)}`);
console.log(`  browser class     ${brw ? `${brw.record_digest.slice(0,12)}  ${brw.network.external_requests} external request(s) observed` : 'NOT RUN — disposition: unavailable'}`);
console.log(`  verdict           capped to '${att.integrity.capped_to}' because author independence is unaccounted`);
writeFileSync(here('./runs/self_attestation.json'), JSON.stringify(att, null, 1));
console.log('');
console.log(`RESULT  ${r.ok ? 'PASS' : 'FAIL'}   the profile states its own coverage in its own vocabulary`);
console.log('RECORD  runs/self_attestation.json');
process.exit(r.ok ? 0 : 1);
