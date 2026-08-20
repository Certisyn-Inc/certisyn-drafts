#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// CAP-1 REFERENCE EMITTER
//
// Derives a Coverage Attestation from a Certisyn canonical verdict document.
// Node built-ins only. Deterministic: no clock, no randomness, no network. The
// as_of value is lifted from the source document and never generated here.
//
// It emits TWO strata deliberately, because they behave differently and the
// difference is the finding:
//
//   modules  — every dispatched unit is individually named with an outcome and
//              a reason, so the stratum reconciles and conforms.
//   checks   — the engine reports a catalogued total and an executed count, and
//              the remainder is arithmetic rather than accounting. R1 refuses it.
//
// The second stratum is emitted rather than suppressed. A profile whose author
// hides the stratum his own engine fails is not a profile, it is a brochure.
// ─────────────────────────────────────────────────────────────────────────────
import { readFileSync } from 'node:fs';

// Engine outcome/reason pairs -> the closed CAP-1 disposition vocabulary.
// Every pair the engine can produce maps to exactly one disposition, or the
// emitter refuses. An unmapped pair is a specification question, not a default.
const DISPOSITION = {
  'skipped:not_applicable'  : 'not_applicable',
  'skipped:flag_disabled'   : 'disabled_by_policy',
  'skipped:unsupported'     : 'unsupported_input',
  'skipped:out_of_scope'    : 'out_of_scope',
  'skipped:budget_exhausted': 'resource_exhausted',
  'skipped:depth_exceeded'  : 'resource_exhausted',
  'failed:error'            : 'failed',
  'failed:timeout'          : 'resource_exhausted',
  'errored:error'           : 'failed',
  'unavailable:missing'     : 'unavailable',
  'withheld:policy'         : 'withheld',
  // Two dispositions the engine produces only in its per-unit check accounting.
  // Both map to not_applicable, and both keep their own detail, because the
  // distinction between them is real: one module was never dispatched for this
  // subject class, the other ran and the condition it tests did not obtain.
  'not_dispatched:module_not_dispatched_for_subject_class'   : 'not_applicable',
  'condition_not_met:owning_module_executed_condition_not_met': 'not_applicable',
};

export function emit(doc, opts = {}) {
  const cov = doc?.coverage;
  if (!cov) throw new Error('source document carries no coverage block; nothing to attest');
  const strata = [];
  const unmapped = [];

  // ── stratum: modules ──────────────────────────────────────────────────────
  const mods = Array.isArray(cov.modules) ? cov.modules : [];
  const examinedMods = mods.filter(m => m.outcome === 'completed');
  const unexamined = [];
  for (const m of mods) {
    if (m.outcome === 'completed') continue;
    const key = `${m.outcome}:${m.reason}`;
    const disposition = DISPOSITION[key];
    if (!disposition) { unmapped.push(key); continue; }
    const e = { unit: m.module, disposition };
    if (m.reason) e.detail = `engine outcome ${m.outcome}, reason ${m.reason}`;
    unexamined.push(e);
  }
  strata.push({
    id: 'modules',
    population: 'detector modules dispatched for this subject class',
    basis: { kind: 'enumeration',
             enumeration_method: 'every module the engine dispatched, recorded with its outcome and reason at dispatch time' },
    eligible: mods.length,
    examined: examinedMods.length,
    unexamined,
    supports: ['absence-of-module-finding']
  });

  // ── stratum: checks ───────────────────────────────────────────────────────
  // Two behaviours, and the difference is the whole demonstration.
  //
  // Without a catalogue map the emitter can supply only the engine's counts, the
  // remainder is arithmetic rather than accounting, and R1 refuses the stratum.
  // That is the correct outcome and it is emitted rather than suppressed.
  //
  // With a catalogue map — the catalogued identifiers and the module that owns
  // each namespace — every unexecuted identifier is named individually and its
  // disposition is DERIVED from the module ledger rather than assumed. The
  // stratum then reconciles and conforms.
  if (typeof cov.catalogued === 'number' && typeof cov.executed === 'number') {
    const engineUnits = Array.isArray(cov.not_run_units) ? cov.not_run_units : null;
    const map = opts.catalogue ?? null;
    let unex = [];
    if (engineUnits) {
      // The engine supplies its own per-unit accounting. Prefer it over any
      // external reconstruction: the engine holds the module ledger and can
      // distinguish a module never dispatched from one that ran without the
      // check firing. An external map cannot, and collapses both.
      for (const u of engineUnits) {
        const key = `${u.outcome}:${u.reason}`;
        const disposition = DISPOSITION[key];
        if (!disposition) { unmapped.push(key); continue; }
        unex.push({ unit: u.id, disposition, detail: `engine: module ${u.module}, outcome ${u.outcome}, reason ${u.reason}` });
      }
    } else if (map && Array.isArray(map.ids)) {
      const ledger = new Map(mods.map(m => [m.module, m]));
      // Executed identifiers are derived from the findings the document actually
      // carries, not from a separate count. A count and a record that disagree is
      // the defect this profile exists to surface, so the record wins.
      const executedIds = new Set(
        (Array.isArray(cov.executed_ids) ? cov.executed_ids
          : (Array.isArray(doc.findings) ? doc.findings.map(f => f && f.id).filter(Boolean) : []))
        .filter(id => map.ids.includes(id)));
      const owners = (id) => (map.namespace_modules?.[id.split('.')[0]] ?? []);
      for (const id of map.ids) {
        if (executedIds.has(id)) continue;
        const own = owners(id);
        const recs = own.map(m => ledger.get(m)).filter(Boolean);
        let disposition, detail;
        if (recs.length && recs.every(r => r.outcome !== 'completed')) {
          const r = recs.find(x => DISPOSITION[`${x.outcome}:${x.reason}`]) ?? recs[0];
          disposition = DISPOSITION[`${r.outcome}:${r.reason}`];
          if (!disposition) { unmapped.push(`${r.outcome}:${r.reason}`); continue; }
          detail = `owning module ${r.module} recorded ${r.outcome} with reason ${r.reason}`;
        } else if (recs.length) {
          disposition = 'not_applicable';
          detail = `owning module ${recs.map(r => r.module).join(', ')} executed; the condition this check tests did not obtain`;
        } else {
          disposition = 'not_applicable';
          detail = `owning module ${own.join(', ') || 'unresolved'} was not dispatched for this subject class`;
        }
        unex.push({ unit: id, disposition, detail });
      }
    }
    const eligible = cov.catalogued;
    const examined = engineUnits || (map && Array.isArray(map.ids)) ? (eligible - unex.length) : cov.executed;
    strata.push({
      id: 'checks',
      population: 'catalogued check identifiers',
      basis: { kind: 'catalogue',
               catalogue_version: String(map?.catalog_version ?? doc.organ_version ?? 'unknown'),
               catalogue_digest: opts.catalogueDigest ?? '0'.repeat(64) },
      eligible, examined, unexamined: unex,
      supports: ['absence-of-check-finding']
    });
  }

  if (unmapped.length)
    throw new Error(`unmapped engine outcome:reason pairs, refusing rather than defaulting: ${[...new Set(unmapped)].join(', ')}`);

  const complete = cov.integrity?.complete === true;
  const out = {
    profile: 'cap/1',
    producer: { name: String(doc.organ ?? 'unknown'), version: String(doc.organ_version ?? 'unknown'),
                policy: String(doc.provenance?.policy ?? 'unstated') },
    subject: { kind: doc.subject?.kind ?? 'artefact', ref: String(doc.subject?.ref ?? 'unknown'),
               ...(doc.subject?.digest ? { digest: doc.subject.digest } : {}) },
    strata,
    absence_assertions: [{
      assertion: 'No finding was recorded by any module that did not execute.',
      stratum: 'modules',
      qualifier: 'Bounded by the modules stratum. Not a statement about checks that were catalogued and not dispatched.'
    }],
    integrity: {
      complete,
      uncapped_verdict: cov.integrity?.uncapped_verdict ?? null,
      capped_to: complete ? null : (cov.integrity?.capped_to ?? 'indeterminate'),
      unaccounted: cov.integrity?.unaccounted_modules ?? [],
      statement: String(cov.integrity?.statement ?? 'no integrity statement supplied by the source document')
    },
    as_of: String(doc.assessed_at ?? '')
  };
  return out;
}

if (process.argv[1] && process.argv[1].endsWith('emit.mjs')) {
  const p = process.argv[2];
  if (!p) { console.error('usage: node emit.mjs <verdict-document.json>'); process.exit(2); }
  const mapPath = process.argv[3];
  const opts = mapPath ? { catalogue: JSON.parse(readFileSync(mapPath, 'utf8')) } : {};
  console.log(JSON.stringify(emit(JSON.parse(readFileSync(p, 'utf8')), opts), null, 1));
}
