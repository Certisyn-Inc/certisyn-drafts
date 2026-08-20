// ─────────────────────────────────────────────────────────────────────────────
// CAP-1 CONFORMANCE VECTORS
//
// Every negative control is the positive base with EXACTLY ONE mutation. That
// constraint is the point: if a control differs in two ways, a refusal does not
// tell you which defect the verifier caught, and a class built that way reports
// coverage it does not have.
//
// Each control declares the rule it targets. The runner asserts not merely that
// the control was refused, but that it was refused BY THAT RULE. A control
// refused for the wrong reason is reported as such and is not counted.
// ─────────────────────────────────────────────────────────────────────────────
const D = '0'.repeat(64);
const clone = (o) => JSON.parse(JSON.stringify(o));

// PV-01 — the base. A complete run over a catalogued detector population.
export const base = {
  profile: 'cap/1',
  producer: { name: 'reference', version: 'cap-1-ref/1.0.0', policy: 'policy/1' },
  subject: { kind: 'artefact', ref: 'vector-subject', digest: { algorithm: 'SHA-256', value: 'a'.repeat(64) } },
  strata: [{
    id: 'detectors',
    population: 'catalogued detector units',
    basis: { kind: 'catalogue', catalogue_version: '1.0.0', catalogue_digest: 'b'.repeat(64) },
    eligible: 6, examined: 4,
    unexamined: [
      { unit: 'pdf.ts',   disposition: 'not_applicable',    detail: 'subject is not a PDF' },
      { unit: 'audio.ts', disposition: 'not_applicable',    detail: 'subject carries no audio stream' }
    ],
    supports: ['absence-of-detector-finding']
  }],
  absence_assertions: [
    { assertion: 'No manipulation indicator was observed.', stratum: 'detectors',
      qualifier: 'Not observed within the examined units of this stratum.' }
  ],
  integrity: { complete: true, uncapped_verdict: 'pass', capped_to: null, unaccounted: [],
    statement: 'Every dispatched unit reached a recorded outcome.' }
};

// PV-02 — legitimate policy and scope dispositions, still complete.
const pv02 = clone(base);
pv02.strata[0].eligible = 8;
pv02.strata[0].unexamined.push(
  { unit: 'secrets.ts', disposition: 'disabled_by_policy', detail: 'off under the governing policy' },
  { unit: 'cloud.ts',   disposition: 'out_of_scope',       detail: 'outside the authorised scope' });

// PV-03 — a failure, correctly reported as incomplete and capping the verdict.
const pv03 = clone(base);
pv03.strata[0].eligible = 7;
pv03.strata[0].unexamined.push({ unit: 'video.ts', disposition: 'failed', detail: 'decoder error' });
pv03.integrity = { complete: false, uncapped_verdict: 'pass', capped_to: 'indeterminate', unaccounted: ['video.ts'],
  statement: 'One unit failed. The verdict is capped and may not be read as clean.' };

// PV-04 — a withheld unit, digest-bound, correctly accounted.
const pv04 = clone(base);
pv04.strata[0].eligible = 7;
pv04.strata[0].unexamined.push({ unit: 'selector.ts', disposition: 'withheld', withheld_digest: 'c'.repeat(64) });

// PV-05 — two strata at different granularity: units and records.
const pv05 = clone(base);
pv05.strata.push({
  id: 'records', population: 'messages eligible in the queried table',
  basis: { kind: 'enumeration', enumeration_method: 'SELECT COUNT(*) over the table under the authorised date range' },
  eligible: 1000, examined: 1000, unexamined: [], supports: ['absence-of-message'] });
pv05.absence_assertions.push({ assertion: 'No message matching the term was observed.', stratum: 'records' });

export const positives = [
  { id: 'PV-01', why: 'complete run, catalogued basis',              doc: base },
  { id: 'PV-02', why: 'policy and scope dispositions, still complete', doc: pv02 },
  { id: 'PV-03', why: 'failure reported and verdict capped',           doc: pv03 },
  { id: 'PV-04', why: 'withholding digest-bound',                      doc: pv04 },
  { id: 'PV-05', why: 'two strata at different granularity',           doc: pv05 }
];

// ── negative controls: one mutation each ────────────────────────────────────
const mut = (fn) => { const d = clone(base); fn(d); return d; };

export const negatives = [
  { id: 'NC-01', rule: 'R1-no-silent-remainder', why: 'two units vanish from the accounting; the counts no longer reconcile',
    doc: mut(d => { d.strata[0].eligible = 8; }) },

  { id: 'NC-02', rule: 'R2-closed-disposition', why: 'an open reason string replaces a vocabulary member',
    doc: mut(d => { d.strata[0].unexamined[0].disposition = 'other'; }) },

  { id: 'NC-03', rule: 'R3-withholding-digest-bound', why: 'a unit is withheld with no digest of what was withheld',
    doc: mut(d => { d.strata[0].unexamined[0] = { unit: 'selector.ts', disposition: 'withheld' }; }) },

  { id: 'NC-04', rule: 'R4-denominator-basis', why: 'a catalogue denominator is asserted without naming the catalogue',
    doc: mut(d => { delete d.strata[0].basis.catalogue_digest; }) },

  { id: 'NC-05', rule: 'R5-counts-well-formed', why: 'examined exceeds eligible',
    doc: mut(d => { d.strata[0].examined = 9; d.strata[0].eligible = 6;
                    d.strata[0].unexamined = []; d.strata[0].eligible = 9; d.strata[0].examined = 11; }) },

  { id: 'NC-06', rule: 'R6-absence-is-scoped', why: 'an absence is asserted against no population',
    doc: mut(d => { d.absence_assertions[0].stratum = 'a-stratum-that-does-not-exist'; }) },

  { id: 'NC-07', rule: 'R7-incomplete-not-clean', why: 'a unit failed and the run is still reported complete',
    doc: mut(d => { d.strata[0].eligible = 7;
                    d.strata[0].unexamined.push({ unit: 'video.ts', disposition: 'failed' }); }) },

  { id: 'NC-08', rule: 'R8-supports-bounds-citation', why: 'a cited stratum states no supported claim classes',
    doc: mut(d => { delete d.strata[0].supports; }) },

  { id: 'NC-09', rule: 'R1-no-silent-remainder', why: 'a count-only ledger: the disposition totals are present but no unit is named',
    doc: mut(d => { d.strata[0].unexamined = []; }) },

  { id: 'NC-10', rule: 'R7-incomplete-not-clean', why: 'incomplete is declared but no capped verdict is given',
    doc: mut(d => { d.integrity.complete = false; d.integrity.capped_to = null; }) }
];
