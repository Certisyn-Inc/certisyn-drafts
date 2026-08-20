#!/usr/bin/env node
// Emit every conformance vector to disk so the second implementation can be run
// against the identical bytes. Node built-ins only.
import { writeFileSync, mkdirSync } from 'node:fs';
import { positives, negatives } from './vectors.mjs';
const dir = new URL('./vectors/', import.meta.url);
mkdirSync(dir, { recursive: true });
const man = [];
for (const v of positives) { writeFileSync(new URL(`./${v.id}.json`, dir), JSON.stringify(v.doc, null, 1)); man.push({ id: v.id, kind: 'positive', expect: 'conform', why: v.why }); }
for (const v of negatives) { writeFileSync(new URL(`./${v.id}.json`, dir), JSON.stringify(v.doc, null, 1)); man.push({ id: v.id, kind: 'negative', expect: 'refuse', rule: v.rule, why: v.why }); }
writeFileSync(new URL('./manifest.json', dir), JSON.stringify(man, null, 1));
console.log(`wrote ${man.length} vectors to vectors/`);
