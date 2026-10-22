import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { aggregate, deltaOf, parseSnapshot, reduction, valueOf } from '../src/lib/model.ts';
import type { Problem, Snapshot } from '../src/lib/model.ts';

const raw = JSON.parse(readFileSync(new URL('../public/data/warmup-2026-10-16.json', import.meta.url), 'utf8'));
const snapshot = parseSnapshot(raw);
const example: Problem = { ...snapshot.problems[0], baseline: { tokens: 100, heartbeats: 1000 }, candidate: { tokens: 50, heartbeats: 250 }, baselineCompatibility: 100, versions: [{ version: '4.26', revision: 'abc', status: 'pass' }] };

test('50 slots preserve 15 current problems and 35 unreleased slots', () => {
  assert.equal(snapshot.problems.length, 50);
  assert.equal(snapshot.problems.filter(p => p.status === 'unreleased').length, 35);
  assert.equal(snapshot.problems.filter(p => p.status === 'measured').length, 9);
});
test('measured scoring uses reductions and a three-axis arithmetic mean', () => {
  assert.equal(valueOf(example, 'tokens'), 50);
  assert.equal(valueOf(example, 'heartbeats'), 75);
  assert.equal(valueOf(example, 'improvement'), 62.5);
  assert.equal(valueOf(example, 'compatibility'), 100);
  assert.equal(valueOf(example, 'combined'), 75);
  assert.equal(deltaOf(example, 'combined'), 75 - 100 / 3);
});
test('negative reductions remain visible without clamping', () => {
  const regressed = { ...example, candidate: { tokens: 120, heartbeats: 1500 } };
  assert.ok(Math.abs(valueOf(regressed, 'tokens')! + 20) < 1e-10);
  assert.equal(reduction(100, 400), -300);
});
test('zero baselines are undefined percentages, not NaN or an invented zero', () => {
  assert.equal(reduction(0, 0), null);
  assert.equal(reduction(0, 10), null);
  assert.equal(valueOf({ ...example, baseline: { tokens: 0, heartbeats: 0 } }, 'combined'), null);
});
test('missing compatibility is pending, never silently 100%', () => {
  const partial = { ...example, versions: [...example.versions, { version: '4.27', revision: 'def', status: 'pending' as const }] };
  assert.equal(valueOf(partial, 'compatibility'), null);
  assert.equal(valueOf(partial, 'combined'), null);
  assert.equal(valueOf(partial, 'improvement'), 62.5);
  assert.equal(valueOf({ ...example, versions: [] }, 'compatibility'), null);
});
test('completed failed version checks count in the compatibility denominator', () => {
  const mixed = { ...example, versions: [...example.versions, { version: '4.27', revision: 'def', status: 'fail' as const }] };
  assert.equal(valueOf(mixed, 'compatibility'), 50);
  assert.equal(valueOf(mixed, 'combined'), 175 / 3);
});
test('pending and unreleased do not contribute zero to a local reduction average', () => {
  const result = aggregate(snapshot.problems, 'improvement');
  assert.equal(result.count, 9);
  assert.equal(result.total, 50);
  assert.ok(result.value! > 70 && result.value! < 71);
  assert.equal(aggregate(snapshot.problems, 'combined').value, null);
});
test('whole competition mean includes failed and unsubmitted problems as zero', () => {
  const all = Array.from({ length: 50 }, (_, i) => ({ ...example, id: i + 1, status: i < 40 ? 'measured' : i < 45 ? 'failed' : 'unsubmitted' } as Problem));
  assert.equal(aggregate(all, 'combined').value, 60);
  assert.equal(aggregate(all, 'combined').count, 50);
});
test('all pending yields no numeric average', () => {
  assert.equal(aggregate(snapshot.problems.slice(15), 'improvement').value, null);
});
test('historical results preserve all 15 checked problems without mixing runs', () => {
  const past = parseSnapshot(JSON.parse(readFileSync(new URL('../public/data/warmup-2026-10-10.json', import.meta.url), 'utf8')));
  assert.equal(aggregate(past.problems, 'combined').count, 15);
  assert.equal(past.problems[0].candidate?.tokens, 188);
  assert.equal(snapshot.problems[0].candidate?.tokens, 43);
});
test('import rejects missing, duplicate and out-of-range slots', () => {
  assert.throws(() => parseSnapshot({ ...raw, problems: raw.problems.slice(0, 49) }), /50/);
  const duplicate = structuredClone(raw); duplicate.problems[1].id = 1;
  assert.throws(() => parseSnapshot(duplicate), /중복/);
  const outside = structuredClone(raw); outside.problems[0].id = 51;
  assert.throws(() => parseSnapshot(outside), /중복/);
});
test('import rejects non-finite or negative metrics and malformed dates', () => {
  for (const value of [-1, Infinity, NaN]) {
    const data = structuredClone(raw); data.problems[0].candidate.heartbeats = value;
    assert.throws(() => parseSnapshot(data), /유한/);
  }
  assert.throws(() => parseSnapshot({ ...raw, measuredAt: 'not a date' }), /시각/);
});
test('import rejects measured records without measurements and duplicated pins', () => {
  const missing = structuredClone(raw); missing.problems[0].candidate = null;
  assert.throws(() => parseSnapshot(missing), /원본/);
  const duplicate = structuredClone(raw); duplicate.problems[0].versions.push(duplicate.problems[0].versions[0]);
  assert.throws(() => parseSnapshot(duplicate), /중복/);
});
test('exports only whitelisted fields from imported data', () => {
  const data = structuredClone(raw); data.extra = 'do not retain'; data.problems[0].secret = 'do not retain';
  const result = parseSnapshot(data);
  assert.equal('extra' in result, false);
  assert.equal('secret' in result.problems[0], false);
});
test('a completed 50-problem import can show a real whole-set mean', () => {
  const completed = { ...raw, problems: Array.from({ length: 50 }, (_, i) => ({ ...example, id: i + 1 })) } satisfies Snapshot;
  assert.equal(aggregate(parseSnapshot(completed).problems, 'combined').value, 75);
});
