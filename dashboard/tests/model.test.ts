import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { aggregate, deltaOf, parseSnapshot, reduction, valueOf } from '../src/lib/model.ts';
import type { Problem, Snapshot } from '../src/lib/model.ts';

// Synthetic test inputs; these are not published team results.
const example: Problem = {
  id: 1, name: 'test.theorem', source: 'test', status: 'measured',
  baseline: { tokens: 100, heartbeats: 1000 }, candidate: { tokens: 50, heartbeats: 250 },
  baselineCompatibility: 100, versions: [{ version: '4.26', revision: 'abc', status: 'pass' }],
  environment: 'test environment', candidateHash: '', evidence: [], note: '',
};
const raw: Snapshot = {
  schemaVersion: 1, id: 'test', label: 'Test fixture', dataset: 'competition',
  measuredAt: '2000-01-01T00:00:00Z', releaseDate: null, provenance: 'synthetic test',
  problems: Array.from({ length: 50 }, (_, i) => ({ ...structuredClone(example), id: i + 1,
    status: i < 9 ? 'measured' : i < 15 ? 'pending' : 'unreleased',
    baseline: i < 9 ? { ...example.baseline! } : null,
    candidate: i < 9 ? { ...example.candidate! } : null,
  })),
};
const snapshot = parseSnapshot(raw);

test('published entries reference valid team result files', () => {
  const files = JSON.parse(readFileSync(new URL('../public/data/index.json', import.meta.url), 'utf8'));
  assert.ok(Array.isArray(files));
  for (const file of files) {
    parseSnapshot(JSON.parse(readFileSync(new URL(`../public/data/${file}`, import.meta.url), 'utf8')));
  }
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
  assert.equal(result.value, 62.5);
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
test('import rejects missing, duplicate and out-of-range slots', () => {
  assert.throws(() => parseSnapshot({ ...raw, problems: raw.problems.slice(0, 49) }), /50/);
  const duplicate = structuredClone(raw); duplicate.problems[1].id = 1;
  assert.throws(() => parseSnapshot(duplicate), /중복/);
  const outside = structuredClone(raw); outside.problems[0].id = 51;
  assert.throws(() => parseSnapshot(outside), /중복/);
});
test('import rejects non-finite or negative metrics and malformed dates', () => {
  for (const value of [-1, Infinity, NaN]) {
    const data = structuredClone(raw); data.problems[0].candidate!.heartbeats = value;
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
  const data = { ...structuredClone(raw), extra: 'do not retain' };
  Object.assign(data.problems[0], { secret: 'do not retain' });
  const result = parseSnapshot(data);
  assert.equal('extra' in result, false);
  assert.equal('secret' in result.problems[0], false);
});
test('a completed 50-problem import can show a real whole-set mean', () => {
  const completed = { ...raw, problems: Array.from({ length: 50 }, (_, i) => ({ ...example, id: i + 1 })) } satisfies Snapshot;
  assert.equal(aggregate(parseSnapshot(completed).problems, 'combined').value, 75);
});

function warmupFixture(): Snapshot {
  const candidate = { id:'author-final',author:'팀원',proof:'theorem test : True := by trivial',
    sourcePath:'docs/report.md',sourceCommit:'a'.repeat(40),sourceState:'committed',candidateHash:'b'.repeat(64),
    status:'measured' as const, baseline:example.baseline,candidate:example.candidate,versions:example.versions,
    environment:example.environment,note:'재검증' };
  return { ...raw, dataset:'warmup', problems:Array.from({length:15},(_,i)=>({
    ...structuredClone(example), id:i+1,candidateHash:candidate.candidateHash,
    selectedCandidateId:candidate.id,selectionReason:'담당자 최종본',teamResults:[structuredClone(candidate)],
  })) };
}
test('warmup accepts exactly fifteen slots and preserves proof provenance', () => {
  const result=parseSnapshot(warmupFixture());
  assert.equal(result.problems.length,15);
  assert.equal(result.problems[0].teamResults?.[0].author,'팀원');
  assert.equal(result.problems[0].teamResults?.[0].proof,'theorem test : True := by trivial');
  assert.throws(()=>parseSnapshot({...warmupFixture(),problems:warmupFixture().problems.slice(1)}),/15/);
});
test('warmup refuses a representative whose metrics differ from its candidate', () => {
  const data=warmupFixture();data.problems[0].candidate={tokens:1,heartbeats:1};
  assert.throws(()=>parseSnapshot(data),/대표 후보/);
});
test('warmup blocks legacy zero-score failure states and duplicate candidate ids', () => {
  const legacy=warmupFixture();legacy.problems[0].status='failed';legacy.problems[0].candidate=null;
  assert.throws(()=>parseSnapshot(legacy),/0/);
  const duplicate=warmupFixture();duplicate.problems[0].teamResults!.push(duplicate.problems[0].teamResults![0]);
  assert.throws(()=>parseSnapshot(duplicate),/ID/);
});
test('unavailable or unsupported team results never count as zero scores', () => {
  for (const status of ['missing','blocked','unsupported','proof_failed'] as const) {
    const p={...example,status,candidate:null};
    assert.equal(valueOf(p,'combined'),null);
    assert.equal(aggregate([p],'improvement').count,0);
  }
});
test('partial checks expose paired measurements but not invented compatibility', () => {
  const p={...example,status:'partial' as const,versions:[...example.versions,{version:'other',revision:'def',status:'pending' as const}]};
  assert.equal(valueOf(p,'improvement'),62.5);
  assert.equal(valueOf(p,'compatibility'),null);
  assert.equal(valueOf(p,'combined'),null);
});
