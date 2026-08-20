#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// CAP-1 CONFORMANCE VERIFIER
//
// Node built-ins only. No dependencies, no installer, no network, no clock.
// Runs anywhere Node runs, including inside a boundary that admits no packages.
//
// It checks the eight normative rules of the Coverage Attestation Profile.
// Every rule exists because its absence is a way a coverage claim can be false
// while looking complete. Each refusal names the rule and the evidence.
// ─────────────────────────────────────────────────────────────────────────────
import { readFileSync } from 'node:fs';

const DISPOSITIONS = new Set(['not_applicable','disabled_by_policy','unsupported_input',
  'resource_exhausted','failed','unavailable','out_of_scope','withheld']);
const BASIS = new Set(['catalogue','enumeration','declared']);
const HEX = /^[0-9a-f]{32,128}$/;

export function verify(doc) {
  const fail = [];
  const F = (rule, grounds, evidence) => fail.push({ rule, grounds, evidence });

  // R0 — shape. A document that is not a CAP-1 document is refused, not coerced.
  if (!doc || typeof doc !== 'object') return { ok:false, failures:[{rule:'R0-shape',grounds:'not an object'}] };
  if (doc.profile !== 'cap/1') F('R0-shape','profile is not cap/1',{profile:doc.profile ?? null});
  if (!doc.subject || typeof doc.subject.ref !== 'string') F('R0-shape','subject.ref absent',{});
  if (!Array.isArray(doc.strata) || doc.strata.length === 0) F('R0-shape','no strata',{});
  if (!doc.integrity || typeof doc.integrity.complete !== 'boolean') F('R0-shape','integrity.complete absent',{});
  if (fail.length) return { ok:false, failures:fail };

  const ids = new Set();
  for (const s of doc.strata) {
    const at = `strata[${s.id ?? '?'}]`;

    if (typeof s.id !== 'string' || ids.has(s.id)) F('R0-shape','stratum id absent or duplicated',{at});
    ids.add(s.id);

    // R1 — NO SILENT REMAINDER.
    // eligible must equal examined plus every individually accounted unexamined unit.
    // A remainder that reconciles only by arithmetic is a population of units whose
    // fate is unrecorded, and unrecorded units are exactly where a negative hides.
    const un = Array.isArray(s.unexamined) ? s.unexamined : null;
    if (!un) { F('R1-no-silent-remainder','unexamined is not an array',{at}); continue; }
    const sum = s.examined + un.length;
    if (sum !== s.eligible)
      F('R1-no-silent-remainder','eligible does not equal examined plus accounted unexamined',
        {at, eligible:s.eligible, examined:s.examined, accounted:un.length, remainder:s.eligible - sum});

    // R2 — CLOSED DISPOSITION VOCABULARY.
    // An open reason string is where an uncomfortable disposition goes to hide.
    for (const u of un) {
      if (!DISPOSITIONS.has(u.disposition))
        F('R2-closed-disposition','disposition outside the closed vocabulary',{at, unit:u.unit, disposition:u.disposition});
      if (typeof u.unit !== 'string' || !u.unit.length)
        F('R2-closed-disposition','unexamined entry names no unit',{at});

      // R3 — WITHHOLDING IS DIGEST-BOUND.
      // A withheld unit that carries no digest of what was withheld cannot later be
      // shown to be the unit withheld rather than one substituted afterwards.
      if (u.disposition === 'withheld' && !HEX.test(String(u.withheld_digest ?? '')))
        F('R3-withholding-digest-bound','withheld unit carries no digest of the withheld value',{at, unit:u.unit});
    }

    // R4 — DENOMINATOR HAS A BASIS.
    // A catalogue basis must name the catalogue by digest; an enumeration must name
    // its method; a declared basis is admissible but must be marked as the weakest.
    const b = s.basis ?? {};
    if (!BASIS.has(b.kind)) F('R4-denominator-basis','basis.kind absent or outside vocabulary',{at, kind:b.kind ?? null});
    else if (b.kind === 'catalogue' && !HEX.test(String(b.catalogue_digest ?? '')))
      F('R4-denominator-basis','catalogue basis without a catalogue digest',{at});
    else if (b.kind === 'enumeration' && !String(b.enumeration_method ?? '').length)
      F('R4-denominator-basis','enumeration basis without a stated method',{at});

    // R5 — COUNTS ARE NON-NEGATIVE AND EXAMINED CANNOT EXCEED ELIGIBLE.
    if (!(Number.isInteger(s.eligible) && Number.isInteger(s.examined)) || s.eligible < 0 || s.examined < 0)
      F('R5-counts-well-formed','eligible or examined is not a non-negative integer',{at});
    else if (s.examined > s.eligible)
      F('R5-counts-well-formed','examined exceeds eligible',{at, eligible:s.eligible, examined:s.examined});
  }

  // R6 — ABSENCE IS SCOPED.
  // An assertion that something was not observed, made without naming the population
  // it was not observed in, is unfalsifiable and is refused.
  for (const a of (doc.absence_assertions ?? [])) {
    if (!a.stratum || !ids.has(a.stratum))
      F('R6-absence-is-scoped','absence assertion names no stratum, or an unknown one',
        {assertion:String(a.assertion ?? '').slice(0,90), stratum:a.stratum ?? null});
  }

  // R7 — INCOMPLETE EXECUTION MAY NOT BE REPORTED AS CLEAN.
  // If any dispatched unit failed, was exhausted, or could not be dispatched, the
  // run did not complete, and a verdict resting on it must be capped and say so.
  const hardStops = doc.strata.flatMap(s => (s.unexamined ?? [])
    .filter(u => u.disposition === 'failed' || u.disposition === 'resource_exhausted' || u.disposition === 'unavailable')
    .map(u => `${s.id}:${u.unit}:${u.disposition}`));
  if (hardStops.length && doc.integrity.complete === true)
    F('R7-incomplete-not-clean','integrity.complete is true while units failed, exhausted or were unavailable',
      {stops:hardStops.slice(0,6), count:hardStops.length});
  if (doc.integrity.complete === false && !String(doc.integrity.capped_to ?? '').length)
    F('R7-incomplete-not-clean','integrity.complete is false and no capped_to verdict is stated',{});

  // R8 — SUPPORTS IS A BOUND, NOT A DECORATION.
  // Where a stratum is cited by an absence assertion it must state what claim classes
  // its coverage supports, so a reader can see whether the citation is in bounds.
  const cited = new Set((doc.absence_assertions ?? []).map(a => a.stratum));
  for (const s of doc.strata) {
    if (cited.has(s.id) && !(Array.isArray(s.supports) && s.supports.length))
      F('R8-supports-bounds-citation','stratum is cited by an absence assertion but states no supported claim classes',{at:`strata[${s.id}]`});
  }

  return { ok: fail.length === 0, failures: fail };
}

export function summarise(doc) {
  const rows = (doc.strata ?? []).map(s => {
    const by = {};
    for (const u of (s.unexamined ?? [])) by[u.disposition] = (by[u.disposition] ?? 0) + 1;
    return { id:s.id, population:s.population, eligible:s.eligible, examined:s.examined,
             fraction: s.eligible ? (s.examined / s.eligible) : 0, dispositions: by };
  });
  return rows;
}

// CLI
if (process.argv[1] && process.argv[1].endsWith('verify.mjs')) {
  const path = process.argv[2];
  if (!path) { console.error('usage: node verify.mjs <cap-1.json>'); process.exit(2); }
  let doc; try { doc = JSON.parse(readFileSync(path, 'utf8')); }
  catch (e) { console.error('REFUSED  unreadable or invalid JSON:', e.message); process.exit(1); }
  const r = verify(doc);
  if (r.ok) {
    console.log('CONFORMS  cap/1');
    for (const s of summarise(doc)) {
      const pct = (100 * s.fraction).toFixed(1).padStart(5);
      const d = Object.entries(s.dispositions).map(([k,v]) => `${k}=${v}`).join('  ') || 'none';
      console.log(`  ${String(s.id).padEnd(14)} ${String(s.examined).padStart(6)} / ${String(s.eligible).padEnd(6)} ${pct}%   ${d}`);
    }
    process.exit(0);
  }
  console.log('REFUSED  cap/1');
  for (const f of r.failures) console.log(`  ${f.rule}  ${f.grounds}\n      ${JSON.stringify(f.evidence ?? {})}`);
  process.exit(1);
}
