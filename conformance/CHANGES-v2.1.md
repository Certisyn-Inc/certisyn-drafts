# arp_reconcile.py v2.1 -- changes from v2

v2 sha256 106651a821ce6de978ba4493a9d27fc31e2cb1abe478079bcc57c65754f5b197
v2.1 sha256 00b10162e7bba48b9fc300cf07be124e9b454d86a8b9453aa716ce4a2b6e03bf

Two changes, one defect and one guard against the class it belongs to.

## 1. reconcile_currency reported a disposition its own legs did not support

v2, for a `fresh` case, returned the leg

    ("currency", "match", None, DERIVED)

together with the literal disposition string "INDETERMINATE". Those two
disagree. compose() over a single unaxed match leg is APPROVE. The
disposition was hand-written rather than composed, which is exactly the
failure mode the Verdict Arithmetic exists to prevent, and it was the only
place in the harness where a disposition was not the output of compose().

Two things were wrong and both are fixed.

  (1) The disposition is now composed, never written. All three branches
      return compose(legs).

  (2) The `fresh` leg was wrong in substance, not only in bookkeeping. This
      reconciler does not verify freshness; it reads expect_status out of
      the fixture. A leg saying "match" claims ARP established currency. It
      did not. The fresh branch now emits the leg the rest of the
      expectation-derived path already emitted for a case its suite expects
      to be valid: indeterminate on leg-not-independently-verified.

## 2. A structural guard, so the class cannot recur silently

New `checked(ret, where)` asserts that a reconciler's reported disposition
is the one its own legs compose to, and hard-stops if not. Nothing in v2
forced the third element of a reconciler's return to be compose(legs) -- it
was a convention, and a convention that can be broken without the run
noticing is not a guarantee. Applied at the section-1d call site, so both
reconcile_currency and reconcile_emilia_generic pass through it.

The same pair is backported to arp_eatf.py, which gains compose_ex (fail
closed AND report the gate a refusal was reached at) and the same checked()
guard. Its results are unchanged in both configurations: the anchor and
no-anchor JSON outputs are byte-identical to the v1 module's.

## What changed in the output

Exactly two rows of 111, both in the currency suite:

    currency/fresh_recent_within_window
    currency/fresh_different_target_not_revoked

    v2   legs: [{"source":"currency","verdict":"match","axis":null,
                 "provenance":"expectation-derived"}]
         disposition INDETERMINATE, refused_at null
    v2.1 legs: [{"source":"currency","verdict":"indeterminate",
                 "axis":"leg-not-independently-verified",
                 "provenance":"expectation-derived"}]
         disposition INDETERMINATE, refused_at "currency"

Unchanged: the disposition counts (REFUSE 79, INDETERMINATE 32), the axis
vocabulary (20 axes emitted, same 20 names), all three construction
identifiers (arp-canonical-claim/1 = 7d90aa1cbee90ef9, arp-subject-digest/1
= f23ecefd99c54182, ep-canonicalization/1 = dc7df29214870f78), and every
self-check.

A second, independent signature of the same defect: in the v2 run those two
rows were the ONLY two INDETERMINATE rows out of 32 carrying a null
`refused_at`. In v2.1 all 32 are populated. The bookkeeping now agrees with
itself in two places rather than disagreeing in two.
