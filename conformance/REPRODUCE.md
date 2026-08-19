# ARP harness v2.1 -- reproduction

Everything needed to reproduce every measured number, from a clean checkout,
with no network access at run time. Layout is described in README.md; this
file is the commands.

Three defects Songbo reported on 29 July are fixed here and the fixes are the
reason this file changed:

  - `arp_adapter.py` defaulted its harness path to `../v2/arp_reconcile.py`,
    which existed only in the tree it was written in, so the documented
    one-command reproduction failed on a clean checkout. It now defaults to
    the colocated harness.
  - `run_outcome_vectors.py` recorded the ABSOLUTE path of the vector file in
    its result JSON, so the file was not byte-identical across checkout
    locations even when every verdict in it was. It now records the basename
    and the content hash.
  - The Makefile `lint` target passed `--verbose`, which current idnits does
    not accept, so the documented lint command ran no validation at all.

## 1. Environment

    Python   3.11.15 (CPython, GCC 13.3.0)
    cryptography  46.0.7        <- the only dependency of the RUNNERS
    cbor2         6.1.4         <- BUILDER ONLY, and version-significant

Everything else is the Python standard library. `pip install cryptography`
is sufficient to run every runner in section 3.

`cbor2` is needed by `runners/build_deterministic_encoding_vectors.py` and by
nothing else. Its version matters and is pinned rather than floated: the
provenance recorded in `vectors/arp-deterministic-encoding-v0.2.json` includes
a measurement of cbor2's canonical-mode map ordering, which is RFC 8949
Section 4.2.3 length-first and not the Section 4.2.1 bytewise ordering this
document requires. A different cbor2 might behave differently and the recorded
measurement would then be about a version nobody could identify.

`runners/run_deterministic_encoding_vectors.py` has no third-party dependency
at all, not even `cryptography`. It imports `reference/arp_cbor.py`, which was
split out of `reference/arp_read_ref.py` on 2026-08-18 for exactly that
reason: the runner previously imported the HTTP endpoint and, through it,
`cryptography`, while its own docstring claimed otherwise. If `cryptography` is absent the harness still runs and says
so on its banner; signature legs then report as unverified rather than
silently passing.

    pip install "cryptography==46.0.7"

## 2. Repositories, pinned

    EMILIA Protocol
      https://github.com/emiliaprotocol/emilia-protocol
      125e4f4311f1319fef3f6d55c935c9ea4da5fc1b
      (feat(gate): ship bounded Autonomy Control Plane (#393), 2026-07-26)

    Noa
      https://github.com/NordenSoft/noa
      21eadb38ae494cbeb64d7773486ed7c4a8417754
      (Remediate CodeQL findings and expand security gates (#13), 2026-07-22)

    EATF verifier / CPB corpus
      https://github.com/tyche-institute/eatf-verifier
      cb49226cc0cb0b36ae90c3f0b214e0e7998e7a60
      (docs: record the published Zenodo v0.4.1 archive DOI, 2026-07-27)

    CPB conformance vectors
      https://github.com/action-state-group/scitt-payload-binding
      bc08d78a210f8e77d4abfd8c04c10ea9b57d4390
      (branch cpb-vectors-fixes-pr2 -- PR #2, 21 vectors, two-sided, plus the
       spec-pure reference library under lib/. Steven's pin. main carries only
       the six later kats at the time of this run.)

    AAC Class-1 frozen vector suite
      https://github.com/action-state-group/agent-action-capsule
      10342f504b051a24908053465927efdaea3ec2f6
      (Steven's pin. 32 frozen cases under test-vectors/, SHA256SUMS-verified,
       exercised by two runners that share no code: python/tests and
       go/cmd/vector_runner. main is mid-restructure; do not chase it.)

    ARP draft source
      https://github.com/Certisyn-Inc/scitt-arp-f39
      branch feat/revision-02-canonicalization

Clone each at the pinned commit:

    git clone https://github.com/emiliaprotocol/emilia-protocol && \
      git -C emilia-protocol checkout 125e4f4311f1319fef3f6d55c935c9ea4da5fc1b
    git clone https://github.com/NordenSoft/noa && \
      git -C noa checkout 21eadb38ae494cbeb64d7773486ed7c4a8417754
    git clone https://github.com/tyche-institute/eatf-verifier && \
      git -C eatf-verifier checkout cb49226cc0cb0b36ae90c3f0b214e0e7998e7a60
    git clone https://github.com/action-state-group/scitt-payload-binding cpb && \
      git -C cpb checkout bc08d78a210f8e77d4abfd8c04c10ea9b57d4390 && \
      pip install -e cpb/lib
    git clone https://github.com/action-state-group/agent-action-capsule aac && \
      git -C aac checkout 10342f504b051a24908053465927efdaea3ec2f6 && \
      pip install -e aac/python

## 3. Commands

Run all nine from `conformance/`, in order. Outputs land in `runs/` and
overwrite the committed copies, so `git diff` after a run IS the
reproduction check.

Order matters in one place. `runs/existence_oracle_run.json` records
`spec_source_sha256` over `../draft-hillier-scitt-arp.md`, so it is
evidence about one revision of the draft and its digest changes whenever
the draft does. Freeze the draft source first, then run (h), then run (i).
A run generated before the last edit to the draft will fail the manifest,
which is the intended behaviour and not a defect in the runner.

    # (a) the main run: EMILIA frozen-v1 + the Noa receipt corpus
    python3 harness/arp_reconcile.py \
      --emilia <emilia-protocol>/conformance/clean-room/frozen-v1 \
      --noa    <noa>/conformance \
      --json   runs/arp_run_v21.json

    # (b) the EATF / CPB envelope corpus, BOTH configurations. The two differ
    #     and the difference is a finding, so neither is "the" run.
    python3 harness/arp_eatf.py --corpus <eatf-verifier>/test-vectors \
      --no-trust-anchor --json runs/eatf_run_noanchor.json
    python3 harness/arp_eatf.py --corpus <eatf-verifier>/test-vectors \
      --json runs/eatf_run_anchor.json

    # (c) the EMILIA AEB boundary-vector adapter. No ARP_HARNESS needed.
    python3 harness/arp_adapter.py

    # (d) ARP-OUTCOME-VECTORS v0.2, two-sided
    python3 runners/run_outcome_vectors.py --caid-repo <emilia-protocol>

    # (e) ARP against the CPB conformance vector suite
    python3 runners/run_cpb_vectors.py --cpb-repo <cpb>

    # (f) ARP against the AAC Class-1 frozen suite, PLUS a differential test
    #     of whether AAC's capsule_id and CPB's jcs-n are the same
    #     construction. Stage 3 needs the Go side; without --go-shim it
    #     reports NOT RUN rather than passing on one leg.
    #
    #     Build the shim first. runners/aac_go_shim/main.go is the source;
    #     it must be built INSIDE the AAC checkout because it imports that
    #     module.
    mkdir -p <aac>/go/cmd/digest_shim
    cp runners/aac_go_shim/main.go <aac>/go/cmd/digest_shim/main.go
    (cd <aac>/go && go build -o /tmp/aac_digest ./cmd/digest_shim)

    python3 runners/run_aac_vectors.py --aac-repo <aac> --cpb-repo <cpb> \
      --go-shim /tmp/aac_digest

    # (g) the CPB-01 typed-reference vectors, ARP's contribution to the CPB
    #     suite. Needs BOTH pins: the CPB reference library for the four
    #     CPB-directed vectors, and the CAID registry and reference issuer,
    #     because vector 05 carries payment.release.1 action objects and every
    #     one of them is re-minted here rather than trusted from the file.
    python3 runners/run_typed_ref_vectors.py --cpb-repo <cpb> \
      --caid-repo <emilia-protocol>

    # (h) the existence-oracle class for Section 6.4.4. No pins, no network,
    #     nothing to install beyond `cryptography`; the runner starts the
    #     reference endpoint itself in each configuration it needs.
    #
    #     This command was missing from this list until 2026-08-12, while
    #     section 5 pinned its output. A reviewer following the list therefore
    #     either passed the manifest without reproducing the run, or failed it
    #     after finding the omitted command. Songbo Bu hit the second path.
    #
    #     --timing-samples changes only runs/existence_oracle_timing.json,
    #     which is deliberately NOT pinned. runs/existence_oracle_run.json is
    #     byte-identical at any sample count, on any platform, under any
    #     interpreter.
    #
    #     The runner reads ../draft-hillier-scitt-arp.md, because the run
    #     record binds its result to one revision of the draft. Running the
    #     conformance tree OUTSIDE the repository therefore needs the source
    #     supplied:
    #         --spec-source /path/to/draft-hillier-scitt-arp.md
    #     Until 2026-08-12 its absence produced a bare FileNotFoundError, which
    #     is how the packaged tree failed for both reviewers who ran it.
    python3 runners/run_existence_oracle_vectors.py --timing-samples 60

    # (i) the deterministic-encoding class. No arguments, no third-party
    #     dependency, about a second. Thirteen encoding rows and ten RFC 3986
    #     normalisation rows whose expected values were computed WITHOUT the
    #     implementation under test, plus five mutants each of which must be
    #     caught by exactly the rows designed for it.
    python3 runners/run_deterministic_encoding_vectors.py

    # (j2) which ARP digests survive an ECDSA signature substitution. Needs
    #      cryptography, 200 trials, a few seconds. It measures BOTH
    #      constructions: the -03 Prior-Entry Hash stable 0 of 200, and the
    #      -04 Signing Input Digest stable 200 of 200.
    python3 runners/ecdsa_malleability_probe.py

    # (j) the Section 4.9 Merkle equivalence, executed rather than asserted.
    #     Standing rule 12. About two minutes, no arguments, no dependency.
    python3 runners/merkle_equiv.py

    # (k) check this file against the tree it describes. Two digests here
    #     were stale before this existed, and nothing caught them.
    python3 runners/verify_manifest.py

Three vector files are generated, not hand-written. To regenerate each and
confirm it is byte-identical:

    # needs cbor2==6.1.4; the runner does not
    python3 runners/build_deterministic_encoding_vectors.py && \
      git diff --exit-code vectors/arp-deterministic-encoding-v0.2.json

`build_deterministic_encoding_vectors.py` computes every expected byte string
with cbor2 and its own argument-width and ordering logic, then ASSERTS the
encoder under test against them. A mismatch stops the build and names the row;
it does not rewrite the expectation. Version 0.1 of that class did rewrite it
-- the builder emitted `ref.cbor(value)` into the file -- so regenerating
against a deliberately broken encoder produced a byte-identical file and the
diff above detected nothing. To confirm the assertion is live, widen a length
argument in `reference/arp_cbor.py` and re-run; the build must stop.

    python3 runners/build_outcome_vectors_v02.py --caid-repo <emilia-protocol> \
      --out /tmp/regen.json && diff /tmp/regen.json vectors/arp-outcome-vectors-v0.2.json

    python3 runners/build_typed_ref_vectors.py --cpb-repo <cpb> \
      --caid-repo <emilia-protocol> --out /tmp/regen-tr.json && \
      diff /tmp/regen-tr.json vectors/arp-typed-ref-cpb01-v0.1.json

`build_typed_ref_vectors.py` refuses to run at all unless a known-bad action
object -- a plaintext `beneficiary_account`, which is a `digest`-typed field --
raises when put through the builder's OWN guard, not merely when handed to the
CAID issuer. The distinction matters: a guard that is present but inert is
indistinguishable from a working one. To confirm the check is live, break
`issue_or_die` and re-run; the build must stop.


## 3a. Packaging this tree for off-list review

The conformance tree is a subdirectory of the draft repository and the runners
read one file from the level above it. A zip of `conformance/` alone is
therefore not a runnable artefact, and was sent as one on 11 August. Both
reviewers who ran it hit the same wall.

A package for someone outside the repository MUST contain, at the top level:

    runners/  reference/  vectors/  harness/  REPRODUCE.md  README.md
    draft-hillier-scitt-arp.md          <-- the source the run record pins

with the draft source at the same level as `conformance/` would sit relative to
it, or the recipient told to pass `--spec-source`. State the source digest in
the covering message so the recipient can tell before running whether they have
the revision the run record was generated against.

    draft-hillier-scitt-arp.md
        sha256 9a086e8832489f456ae5066848c208ceccbab9e00adadd29bc003c3a142c86c9

## 4. Non-corpus fixtures

    vectors/arp-aeb-adapter-v0.1.json      EMILIA's boundary vector, as
                                           received, unmodified
    vectors/arp-outcome-vectors-v0.2.json  the shipped vector set
    vectors/arp-typed-ref-cpb01-v0.1.json  the CPB-01 typed-reference
                                           contribution: five vectors,
                                           two-sided

`runs/arp-outcome-vectors-v0.1-superseded.json` is REGENERATED by the adapter,
not an input. It exists so the supersession by v0.2 is checkable rather than
asserted.

No other fixture is used. Everything else is read from the pinned corpora.

## 5. Expected outputs

    runs/arp_run_v21.json
      sha256 a9af97909b6ef330563b706555dc66aaeca83e9a38fa4ff0896147e7bc19f23b
    runs/arp_outcome_vectors_v02_run.json   5 passed, 0 failed
      sha256 a2ad66d4f7acb573f3b63dd5874fae127261984348413d5c1a03e98d6f55aa28
    runs/cpb_run.json                       SELF-CHECK PASS, 0 unattributed
      sha256 ddf063bb23ade16a729bc6ba8baada5c30a4f4ef3ec0f5b52a103f45fbe0208e
    runs/aac_run.json                       SELF-CHECK PASS, 0 unattributed
      sha256 421a8bef08d33a47ad302b281a66c0773fd025ab55d7996c2964f335294982d4
    runs/arp_adapter_run.json               5 of 5
      sha256 a25629f0e1ccdee444d1f86a4a61476780e32d7132df4b5cc67251befc28280e
    runs/typed_ref_cpb01_run.json           TYPED-REF RUN: PASS, 4/4
                                            predictions held, 1 not applicable
      sha256 16cf2f0628c7ac6c68e73f8d2de49aa76b796400ea7c7eefd2c9bb68156c1ed9
    runs/eatf_run_noanchor.json
      sha256 37c3921fb1ff16a455bb4f2fed0b76dac17433750c18f331cea1ac27cdae4ece
    runs/eatf_run_anchor.json
      sha256 3f81214a0131c48e63d6b585952ce842ab4675aca6dff7ece918929cd83d32d7
    runs/deterministic_encoding_run.json    PASS_WITH_DECLARED_GAPS
                                            13 encoding + 10 normalisation
                                            rows, 5 of 5 controls,
                                            4 declared non-coverage items
      sha256 a1948642ae666a9c7c99661b04e4e98b93e17c2b784a17c82e6b2cf558bcddc9
    runs/existence_oracle_run.json  PASS_WITH_DECLARED_GAPS, 7 of 7
                                    controls exercised, 6 declared gaps
      sha256 74df0c9aae6a6d230c1ecc1a9fc92be2ace571be411c50666e7cf8bfb5199869

Two files in `runs/` are deliberately absent from this section and
`verify_manifest.py` says so on every run rather than passing over them in
silence:

  - `runs/existence_oracle_timing.json` is environment-dependent by design. It
    records the interpreter, the platform, the invocation and the loopback
    medians. Pinning it would make a reproduction on a different machine fail
    for a reason that is not about the artefact. It is reported, not
    adjudicated, and it is not evidence about a deployed network path.
  - `runs/arp-outcome-vectors-v0.1-superseded.json` is regenerated by the
    adapter and exists so that the supersession by v0.2 is checkable.

`runs/existence_oracle_run.json` carries no environment field at all, which is
why it can be pinned: it is byte-identical on Linux/CPython 3.11 and on
Windows/CPython 3.13, at any `--timing-samples` value. Verified both ways on
2026-08-12. Until that date the file did carry `platform` and `python`, so the
digest recorded here could only ever match one machine, and the first
independent reproduction failed on it.

`runs/arp_run_v21.json` is unchanged from the v2.1 package Songbo reproduced
on 29 July. `runs/arp_outcome_vectors_v02_run.json` DID change, by exactly the
one field named in the defect list above; every verdict in it is identical.

For reference, the v2 run this supersedes had `arp_run_v2.json` sha256
04fa5fb12185029df4c159982cdb3d541a8e701a1fb9d44fb549a5288561a38b, which Songbo
reproduced independently from fresh checkouts. v2.1 differs from it in exactly
two rows; see CHANGES-v2.1.md.

## 6. Script hashes

    00b10162e7bba48b9fc300cf07be124e9b454d86a8b9453aa716ce4a2b6e03bf  harness/arp_reconcile.py
    6e7313642c623df3b6ed227cdacd52e42f6c70d309500171e212a76aa456f6fc  harness/arp_eatf.py
    c54bd187a9abe9b55103a9faff8b31bd01f049856b35bef2575095b83febdf44  harness/arp_adapter.py
    0ee49465873bb9f9c18330517a9830aa3ad9e100886c76e9ec3c61db234eec3c  runners/run_outcome_vectors.py
    f924e69ccfc7d91e9295415b6aaa455976601f967fc7b337c0aa246c801a484d  runners/build_outcome_vectors_v02.py
    ecaee0cc29127d61abb27ebbf190a07226abff48c2b910d55c8bf1ec3655d774  runners/run_cpb_vectors.py
    583dc806ee49b50f27ef27c5270a5330657c63155e580cfb312b1c4d455db19d  runners/run_aac_vectors.py
    cb964d52a7c30cf00d4527766916773772ac3eb0d2524ec00b3d6b44d6ec9f65  runners/aac_go_shim/main.go
    dbed0ea02d38336a6ed7342797b9905aca6db206f462dfa08e10908073cec7b4  runners/verify_manifest.py
    2ce3ff85fbf7c10c8905c4392e56a6b33191704996911cc88bc3dc8887e634d7  runners/build_typed_ref_vectors.py
    b1056fa365900b196ad186e4a07fac2939d4c75843d0280629f21c0828e3b621  runners/run_typed_ref_vectors.py
    8726e9f178ea94bb2b255af808bd0761e3f2f46473fcd403413fce5ab1db1b35  vectors/arp-outcome-vectors-v0.2.json
    88153dd1c4b62cfd313cd890ae84fc65de1f67bcd6db7556fce00b7893ce673d  vectors/arp-typed-ref-cpb01-v0.1.json
    24698fdd0ed5f69a7b5a3d035ffec8aed625df1bb93ad76f9ec4c669d1062804  reference/arp_read_ref.py
    e6813a46496ac119532264a72c1ee7bd7d6fe5953355e59008a245cfd4bae48a  reference/arp_cbor.py
    59382d0e3ee3a98e6e393afe7b2cee19cbdebe5b81761c22a0dae548f68d1dfe  reference/arp_uri.py
    5b9527cd05d407fba59a809a890fec428d8315ebe84a1e28ae5f0a8c83973f0b  runners/de_codec.py
    554cceb33b95ca7027300d600be108437c346b82ab732774d33de6c415006b6d  runners/build_deterministic_encoding_vectors.py
    9313e91e3066ce09a353d977a5a580004646556fa7610bdf04f3503193117d8e  runners/run_deterministic_encoding_vectors.py
    366b3868c60758468e40f83de61a74389a2639cd720ac5df7674f0286617c294  runners/merkle_equiv.py
    7ad2973b237a8446b1797b704b4f04c5749dada78c5579e550d15d3b7f1537f5  runners/ecdsa_malleability_probe.py
    b5cf28d058beb6d235a6f1a168658c66bc4da4c53aa994027ae7afcc1b34045b  vectors/arp-deterministic-encoding-v0.2.json
    8ce61405fc02755c4950c44bdacada84e3379356e20cd552ffd2d43d41393a36  reference/fixture-eo-v0.1.json
    6e50ea9014fc348d8ddd632fb8b36a0103c44a965d26af4be1607b5107651af7  runners/run_existence_oracle_vectors.py
    e75e9e594c589aa449ed8b816a9e42c75ded2e4107789d44dbf45fc5a8ee7d66  vectors/arp-existence-oracle-v0.1.json
    1e5d6a6b156f956e846ef3f4a5df6fa35efbe8197b5556106d2e060c70f59f2e  vectors/arp-aeb-adapter-v0.1.json   (EMILIA's, as received)

The v1 harness that produced the first posted run remains byte-identical and
is not in this tree; its md5 is 99240731f9947355de11006f91904d4d and it has
not been touched since it was posted.

Third-party code this tree calls but does not vendor:

    caid/impl/python/caid.py         d5edfdef62093eadffba06d7846f31f20691f7b658f14035bd95250280b24651
    caid/registry/action-types.json  8352b1d5e33d608999d6e285cf67fa3bdd7ac5b818d54700193b09ad49daf9d6

both read from YOUR checkout of emilia-protocol at the pinned commit, never
from mine, and the CPB reference library from the CPB pin above.
