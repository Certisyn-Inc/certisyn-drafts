#!/usr/bin/env node
// Does draft-ietf-scitt-receipts-ccf-profile-04 admit a one-transaction tree?
//
// Section 2.1 defines the Merkle Tree Hash of a one-entry list:
//     MTH({d[0]}) = HASH(d[0])
// Section 3.2's compute_root iterates over proof.path, so an empty path is
// zero iterations and the leaf hash IS the root.
// Section 3's CDDL writes the path as [+ ccf-proof-element], and RFC 8610
// Section 3.2 defines `+` as one or more.
//
// Executed rather than argued: build the one-transaction proof, run the
// Section 3.2 algorithm over it verbatim, and print what it returns.

import { createHash } from 'node:crypto';
const H = (...b) => createHash('sha256').update(Buffer.concat(b)).digest();

// A CCF leaf, per the Section 3 CDDL.
const leaf = {
  internal_transaction_hash: H(Buffer.from('tx:2.42', 'utf8')),
  internal_evidence: 'ccf-single-transaction-ledger',
  data_hash: H(Buffer.from('the signed statement', 'utf8')),
};

// Section 3.2, transcribed. The loop body is unreachable for an empty path.
function compute_root(proof) {
  let h = H(
    proof.leaf.internal_transaction_hash,
    H(Buffer.from(proof.leaf.internal_evidence, 'utf8')),
    proof.leaf.data_hash,
  );
  let iterations = 0;
  for (const [left, hash] of proof.path) {
    h = left ? H(hash, h) : H(h, hash);
    iterations += 1;
  }
  return { h, iterations };
}

// The one-transaction case: a valid inclusion proof with an empty path.
const single = { leaf, path: [] };
const r1 = compute_root(single);

// Section 2.1: MTH of a one-entry list is HASH of that entry. The entry here
// is the CCF leaf, so the two must agree.
const mth = H(
  leaf.internal_transaction_hash,
  H(Buffer.from(leaf.internal_evidence, 'utf8')),
  leaf.data_hash,
);

// A two-transaction tree, for contrast: path has one element, loop runs once.
const sibling = H(Buffer.from('tx:2.43', 'utf8'));
const r2 = compute_root({ leaf, path: [[false, sibling]] });

const pad = (s, n) => String(s).padEnd(n);
console.log('CCF one-transaction inclusion proof, Section 3.2 executed verbatim\n');
console.log('  ' + pad('case', 22) + pad('path len', 10) + pad('loop iterations', 18) + 'root');
console.log('  ' + pad('one transaction', 22) + pad(single.path.length, 10)
  + pad(r1.iterations, 18) + r1.h.toString('hex').slice(0, 32) + '...');
console.log('  ' + pad('two transactions', 22) + pad('1', 10)
  + pad(r2.iterations, 18) + r2.h.toString('hex').slice(0, 32) + '...');
console.log('\n  Section 2.1  MTH({d[0]}) = HASH(d[0])   ' + mth.toString('hex').slice(0, 32) + '...');
console.log('  agrees with compute_root(empty path):  ' + (r1.h.equals(mth) ? 'YES' : 'NO'));
console.log('\n  full root, one-transaction case:');
console.log('    ' + r1.h.toString('hex'));
console.log(`
CONCLUSION
  The Section 3.2 algorithm returns a well-formed root for a path of length
  zero, in zero iterations, and that root is exactly the value Section 2.1
  defines for a one-entry list. Both sections admit the one-transaction tree.
  The Section 3 CDDL writes the path as [+ ccf-proof-element]; RFC 8610
  Section 3.2 defines + as one or more, so the proof that both other sections
  describe cannot be encoded. The disagreement is internal to the document.
`);
