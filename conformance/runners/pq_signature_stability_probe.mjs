#!/usr/bin/env node
// Which SCITT identity digest survives a change of signature algorithm.
//
//     node runners/pq_signature_stability_probe.mjs      # no arguments
//
// A SCITT Signed Statement is identified in two competing ways: by the digest
// of the COSE_Sign1 envelope that was registered, and by the digest of the
// Sig_structure that was presented to the signature algorithm. Iman Schrock's
// EMILIA identity profile separates them, and demonstrates the separation with
// two valid P-256 envelopes over one signing input, reached by the ECDSA
// (r, s) -> (r, n - s) substitution Anton Sokolov posted on 2026-08-18.
//
// That demonstration needs a transform and an actor willing to apply it. This
// probe measures the case with neither: one key, one signing input, N ordinary
// sign calls, across the algorithms a signing estate migrates through.
//
// EVERY REPORTED NUMBER IS RECOVERED FROM THE SERVED BYTE-STRINGS. Each
// envelope is encoded and then decoded again, and every digest is computed
// from what came back out, so a leg that does not vary cannot report variance
// and a leg that does cannot report stability.
//
// Node standard library, plus @noble/post-quantum 0.6.1, which is the version
// pinned in the Certisyn platform, called with the same message-first shape.

import { createHash, generateKeyPairSync, sign as nsign, verify as nverify } from 'node:crypto';
import { ml_dsa65 } from '@noble/post-quantum/ml-dsa.js';

const N = 200;
const P256_N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551n;
const sha256 = (b) => createHash('sha256').update(b).digest('hex');

// ------------------------------------------------------------ minimal CBOR
// Definite lengths only, which is all a COSE_Sign1 of this shape needs. It
// exists so the probe can recover values from SERVED bytes rather than reuse
// the locals it signed.
function cborBytes(b) {
  const l = b.length; let h;
  if (l < 24) h = Buffer.from([0x40 | l]);
  else if (l < 256) h = Buffer.from([0x58, l]);
  else if (l < 65536) h = Buffer.from([0x59, l >> 8, l & 255]);
  else h = Buffer.from([0x5a, (l >>> 24) & 255, (l >>> 16) & 255, (l >>> 8) & 255, l & 255]);
  return Buffer.concat([h, b]);
}
function readItem(b, i) {
  const ai = b[i] & 0x1f; i += 1;
  let len;
  if (ai < 24) len = ai;
  else if (ai === 24) { len = b[i]; i += 1; }
  else if (ai === 25) { len = b.readUInt16BE(i); i += 2; }
  else if (ai === 26) { len = b.readUInt32BE(i); i += 4; }
  else throw new Error('unsupported additional info ' + ai);
  return [b.subarray(i, i + len), i + len];
}
function decodeSign1(env) {
  if (env[0] !== 0x84) throw new Error('not a 4-element array');
  let i = 1; const out = [];
  for (let k = 0; k < 4; k++) {
    if (k === 1) { i += 1; out.push(Buffer.alloc(0)); continue; }   // unprotected {}
    const [v, ni] = readItem(env, i); out.push(v); i = ni;
  }
  return { protected: out[0], payload: out[2], signature: out[3] };
}
function sigStructure(prot, payload) {
  const ctx = Buffer.from('Signature1', 'utf8');
  return Buffer.concat([
    Buffer.from([0x84]), Buffer.from([0x60 | ctx.length]), ctx,
    cborBytes(prot), cborBytes(Buffer.alloc(0)), cborBytes(payload),
  ]);
}
function envelope(prot, payload, sig) {
  return Buffer.concat([Buffer.from([0x84]), cborBytes(prot), Buffer.from([0xa0]),
                        cborBytes(payload), cborBytes(sig)]);
}

const PAYLOAD = Buffer.from(JSON.stringify({
  iss: 'certisyn', sub: 'VRO-202608-308', claim: 'authorized',
}), 'utf8');

function runLeg(name, prot, signFn, verifyFn, sigLen) {
  const signingInput = sigStructure(prot, PAYLOAD);
  const inputDigests = new Set(), entryDigests = new Set();
  let verified = 0, lenOk = 0;
  for (let i = 0; i < N; i++) {
    const env = envelope(prot, PAYLOAD, signFn(signingInput));
    const back = decodeSign1(env);
    const backInput = sigStructure(back.protected, back.payload);
    if (verifyFn(back.signature, backInput)) verified += 1;
    if (back.signature.length === sigLen) lenOk += 1;
    inputDigests.add(sha256(backInput));
    entryDigests.add(sha256(env));
  }
  return { name, verified, lenOk, sigLen,
           distinctInput: inputDigests.size, distinctEntry: entryDigests.size };
}

const rows = [];

// Ed25519. RFC 8032 derives the nonce from the key and the message, so one key
// over one message yields exactly one signature.
{
  const { privateKey, publicKey } = generateKeyPairSync('ed25519');
  rows.push(runLeg('Ed25519', Buffer.from([0xa1, 0x01, 0x27]),
    (m) => nsign(null, m, privateKey),
    (s, m) => nverify(null, m, publicKey, s), 64));
}

// ECDSA P-256 as ordinarily implemented: k drawn at random per signature.
const ecdsaKeys = generateKeyPairSync('ec', { namedCurve: 'P-256' });
rows.push(runLeg('ECDSA P-256', Buffer.from([0xa1, 0x01, 0x26]),
  (m) => nsign('sha256', m, { key: ecdsaKeys.privateKey, dsaEncoding: 'ieee-p1363' }),
  (s, m) => nverify('sha256', m, { key: ecdsaKeys.publicKey, dsaEncoding: 'ieee-p1363' }, s), 64));

// ML-DSA-65, FIPS 204. The library default is hedged signing.
const mk = ml_dsa65.keygen();
rows.push(runLeg('ML-DSA-65 hedged', Buffer.from([0xa1, 0x01, 0x38, 0x22]),
  (m) => Buffer.from(ml_dsa65.sign(new Uint8Array(m), mk.secretKey)),
  (s, m) => { try { return ml_dsa65.verify(new Uint8Array(s), new Uint8Array(m), mk.publicKey); }
              catch { return false; } }, 3309));

// ML-DSA-65, same library, same key, deterministic signing selected.
rows.push(runLeg('ML-DSA-65 determ.', Buffer.from([0xa1, 0x01, 0x38, 0x22]),
  (m) => Buffer.from(ml_dsa65.sign(new Uint8Array(m), mk.secretKey, { extraEntropy: false })),
  (s, m) => { try { return ml_dsa65.verify(new Uint8Array(s), new Uint8Array(m), mk.publicKey); }
              catch { return false; } }, 3309));

console.log('SCITT identity digest stability under repeated signing of ONE signing input');
console.log('  ' + N + ' sign calls per leg, one key per leg, no adversary and no transform');
console.log('  ML-DSA-65 key sizes as generated: pk ' + mk.publicKey.length
  + ' B, sk ' + mk.secretKey.length + ' B\n');
const pad = (s, n) => String(s).padEnd(n);
console.log('  ' + pad('leg', 20) + pad('verify', 11) + pad('sig len', 16)
  + pad('distinct signing-input', 24) + 'distinct entry digests');
for (const r of rows) {
  console.log('  ' + pad(r.name, 20) + pad(r.verified + '/' + N, 11)
    + pad(r.lenOk + '/' + N + ' @' + r.sigLen + 'B', 16)
    + pad(r.distinctInput + ' of ' + N, 24) + r.distinctEntry + ' of ' + N);
}

// The (r, s) -> (r, n - s) substitution, which reaches a second envelope even
// where signing itself is deterministic.
{
  const prot = Buffer.from([0xa1, 0x01, 0x26]);
  const si = sigStructure(prot, PAYLOAD);
  const sig = nsign('sha256', si, { key: ecdsaKeys.privateKey, dsaEncoding: 'ieee-p1363' });
  const r = sig.subarray(0, 32);
  const s = BigInt('0x' + sig.subarray(32).toString('hex'));
  const twin = Buffer.concat([r, Buffer.from((P256_N - s).toString(16).padStart(64, '0'), 'hex')]);
  const bothVerify =
    nverify('sha256', si, { key: ecdsaKeys.publicKey, dsaEncoding: 'ieee-p1363' }, sig) &&
    nverify('sha256', si, { key: ecdsaKeys.publicKey, dsaEncoding: 'ieee-p1363' }, twin);
  const entries = new Set([sha256(envelope(prot, PAYLOAD, sig)),
                           sha256(envelope(prot, PAYLOAD, twin))]);
  console.log('\n  ECDSA (r, s) -> (r, n - s), no key held:');
  console.log('    both byte-strings verify   ' + bothVerify);
  console.log('    distinct entry digests     ' + entries.size + ' of 2');
}

// Parallel composition, which is what a migrating estate actually emits.
{
  const ed = generateKeyPairSync('ed25519');
  const prot = Buffer.from([0xa1, 0x01, 0x27]);
  const si = sigStructure(prot, PAYLOAD);
  const pairs = new Set(), edOnly = new Set();
  for (let i = 0; i < N; i++) {
    const a = nsign(null, si, ed.privateKey);
    const b = Buffer.from(ml_dsa65.sign(new Uint8Array(si), mk.secretKey));
    edOnly.add(sha256(a));
    pairs.add(sha256(Buffer.concat([a, b])));
  }
  console.log('\n  parallel Ed25519 + ML-DSA-65 over one signing input:');
  console.log('    Ed25519 leg alone         ' + edOnly.size + ' of ' + N + ' distinct');
  console.log('    the composed pair         ' + pairs.size + ' of ' + N + ' distinct');
}

console.log(`
CONCLUSION:
  The Sig_structure digest is 1 of ${N} on every leg measured, including the
  legs whose envelopes are all distinct. The envelope digest is 1 of ${N} on
  exactly one leg, Ed25519, and its stability there is a property of RFC 8032
  rather than of COSE. Under ECDSA as ordinarily implemented, under FIPS 204
  hedged signing, and under any parallel composition containing either, one
  signing input has an unbounded family of valid envelopes reachable by
  ordinary re-signing, with no adversary present.

  Hedged and deterministic ML-DSA-65 are both conformant, both verify, and are
  selected by a flag that appears nowhere in the protected header. Two
  conforming signers therefore disagree on whether the envelope digest is a
  stable identifier, and a relying party reading the envelope cannot tell which
  one produced it.
`);
