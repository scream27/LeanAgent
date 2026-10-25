import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

const data = JSON.parse(readFileSync(new URL('../src/data/team-activity.json', import.meta.url), 'utf8'));

test('frozen collection retains every PR and every team member, including closed drafts', () => {
  assert.deepEqual(data.pullRequests.map((pr: { number: number }) => pr.number).sort((a: number, b: number) => a - b), Array.from({ length: 30 }, (_, i) => i + 1));
  assert.equal(new Set(data.authors.map((person: { login: string }) => person.login)).size, 7);
  for (const person of data.authors) {
    assert.deepEqual(data.pullRequests.filter((pr: { author: string }) => pr.author === person.login).map((pr: { number: number }) => pr.number).sort((a: number, b: number) => a - b), person.prNumbers);
  }
  for (const [status, expected] of [['open', 6], ['merged', 21], ['closed', 3]]) {
    assert.equal(data.pullRequests.filter((pr: { status: string }) => pr.status === status).length, expected);
  }
});

test('P09 compatibility supplement binds every pass to the published proof and exact pinned versions', () => {
  const supplement = JSON.parse(readFileSync(new URL('../public/research/p09/experiment.json', import.meta.url), 'utf8'));
  const snapshot = JSON.parse(readFileSync(new URL('../public/data/warmup-team-results.json', import.meta.url), 'utf8'));
  const p09 = snapshot.problems.find((p: { id: number }) => p.id === 9);
  assert.equal(createHash('sha256').update(supplement.proofs.baseline.proof).digest('hex'), p09.candidateHash);
  assert.deepEqual(p09.versions.map((v: { status: string }) => v.status), ['pass', 'pass', 'pass']);
  assert.equal(p09.status, 'measured');
  assert.deepEqual(p09.candidate, { tokens: 79, heartbeats: 512 });
  for (const version of p09.versions) {
    const key = version.version === 'v4.33.0-rc2' ? 'p9-4.33rc2' : `p9-${version.version.slice(1, -2)}`;
    assert.equal(supplement.pinnedEnvironments[key].verified, true);
    assert.equal(supplement.pinnedEnvironments[key].commit, version.revision);
  }
});

test('new experiment groups retain reported origin and immutable repository evidence', () => {
  assert.equal(data.candidateGroups.length, 36);
  assert.equal(new Set(data.candidateGroups.map((g: { id: string }) => g.id)).size, 36);
  for (const group of data.candidateGroups) {
    assert.equal(group.verification.origin, 'source_reported');
    assert.equal(group.verification.independentlyReverifiedInThisTask, false);
    assert.ok(group.prNumbers.every((n: number) => data.pullRequests.some((pr: { number: number }) => pr.number === n)));
    assert.ok(group.problemIds.every((n: number) => Number.isInteger(n) && n >= 1 && n <= 15));
    for (const evidence of group.evidence) {
      const url = new URL(evidence.url);
      assert.equal(url.protocol, 'https:');
      assert.equal(url.hostname, 'github.com');
    }
  }
  assert.ok(data.candidateGroups.some((g: { prNumbers: number[]; problemIds: number[] }) => g.prNumbers.includes(23) && g.problemIds.length === 15));
  assert.ok(data.candidateGroups.some((g: { prNumbers: number[]; kind: string }) => g.prNumbers.includes(27) && g.kind === 'repair'));
});
