# CAP-1 — reproduction

Node 18 or later, and Python 3 for the second implementation.
**The verifiers have no dependencies, no installer, no network and no clock.**
Everything runs from a clean copy.

Part 4 additionally needs playwright and a chromium build, because it runs the
single-file HTML verifier in a real browser engine. If playwright is absent, part
4 declares itself not run and the rest of the class completes unaffected. A class
that reports green over a part it skipped is the defect this profile refuses.

```
./all.sh
```

That runs the whole class. The six parts, and what each establishes:

| # | Command | Establishes |
|---|---|---|
| 1 | `node run.mjs` | Five positive vectors conform; ten negative controls are refused, each **by the rule it targets**. Every control is the positive base with exactly one mutation. |
| 2 | `node mutate.mjs` | Silencing any one normative rule makes the class fail. **Eight rules, eight mutants, eight kills.** No rule is present without a control exercising it. |
| 3 | `python3 crosscheck.py` | Two implementations — JavaScript and Python, written from the specification text rather than ported — agree on every vector and every targeted rule. |
| 4 | `node browsercheck.mjs` | The **single-file HTML verifier**, executed in chromium with request interception on, agrees with the reference implementation on every vector and refuses each negative control by the rule it targets — and issues **no request beyond the local document**. Isolation is observed at the interception layer, not inferred from a substring search over the source. |
| 5 | `node selfattest.mjs` | The profile states **its own coverage in its own vocabulary**, and caps its own verdict because author independence is unaccounted. |
| 6 | `node demo-live.mjs` | Applied to a real Certisyn verdict document: refused from engine counts alone, conforming with per-unit accounting. |

## Verify one attestation

```
node verify.mjs <attestation.json>     # exit 0 conforms, 1 refused, 2 usage
python3 verify.py <attestation.json>   # the second implementation
```

Or open **`verify.html`** in any browser. Single file, no script loaded from
anywhere, and no network request of any kind — which part 4 establishes by
recording every request the page attempts, rather than by asserting it. Save it
to disk and it runs on a machine that has never had a package manager and will
never be allowed one.

## Emit from a Certisyn verdict document

```
node emit.mjs <verdict-document.json> [catalogue-map.json]
```

Without the map you get the refusal. With it you get the accounting.

## Files

| File | Role |
|---|---|
| `CAP-1.schema.json` | the vocabulary |
| `verify.mjs` | reference verifier, Node built-ins only |
| `verify.py` | second implementation, standard library only |
| `verify.html` | single-file offline verifier |
| `vectors.mjs`, `vectors/` | five positive vectors, ten negative controls, as source and as bytes |
| `run.mjs` | conformance runner |
| `mutate.mjs` | verifier mutation testing |
| `crosscheck.mjs`, `crosscheck.py` | cross-implementation agreement, Node and Python |
| `browsercheck.mjs` | the HTML verifier under a browser engine, with network observation |
| `selfattest.mjs` | the profile's coverage of itself |
| `emit.mjs` | reference emitter |
| `demo-live.mjs` | the two-run demonstration |
| `catalogue-map.json` | 227 catalogued identifiers and the module owning each namespace |
| `fixtures/`, `runs/` | committed inputs and machine-readable run records |

## What this establishes

That the eight normative rules are implementable, that each is load-bearing,
that three implementations agree on all of them — Node, Python, and the HTML
file in a browser engine — that the HTML file reaches nothing, and that a
producer holding only counts is refused where a producer holding a per-unit
ledger conforms.

## What it does not establish

**Author independence.** All three implementations, the vectors and the
specification originate with the same party, so a misreading shared between them is invisible
to every check here. The self-attestation says so in the vocabulary itself:
the `implementations` stratum records "any implementation not authored by
Certisyn" as `unavailable`, and `integrity.complete` is **false** with the
verdict capped to `implementation-independent-only`.

The class becomes genuinely two-sided the first time it refuses a document its
author did not write. The vectors, the fixtures and both verifiers are published
together specifically to make accepting that cheap. A disagreement between an
independent implementation and this text is either a defect in that
implementation or an ambiguity in this specification, and both are worth more
than agreement.
