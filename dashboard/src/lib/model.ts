export type Metric = 'improvement' | 'tokens' | 'heartbeats' | 'compatibility' | 'combined';
export type ProblemStatus = 'measured' | 'pending' | 'unreleased' | 'failed' | 'unsubmitted' | 'missing' | 'blocked' | 'unsupported' | 'partial' | 'proof_failed';
export type VersionCheck = { version: string; revision: string; status: 'pass' | 'fail' | 'pending' };
export type Measurement = { tokens: number; heartbeats: number };
export type Problem = {
  id: number;
  name: string;
  source: string;
  status: ProblemStatus;
  baseline: Measurement | null;
  candidate: Measurement | null;
  baselineCompatibility: number | null;
  versions: VersionCheck[];
  environment: string;
  candidateHash: string;
  evidence: string[];
  note: string;
  selectedCandidateId?: string;
  selectionReason?: string;
  teamResults?: TeamResult[];
};
export type TeamResult = {
  id: string; author: string; proof: string; sourcePath: string; sourceCommit: string; sourceState: string;
  status: ProblemStatus; candidateHash: string; note: string; environment: string;
  baseline: Measurement | null; candidate: Measurement | null; versions: VersionCheck[];
};
export type Snapshot = {
  schemaVersion: 1;
  id: string;
  label: string;
  dataset: 'competition' | 'warmup';
  measuredAt: string;
  releaseDate: string | null;
  provenance: string;
  problems: Problem[];
};

export const METRICS: { id: Metric; label: string; unit: string }[] = [
  { id: 'improvement', label: '개선 점수', unit: '점' },
  { id: 'tokens', label: '토큰', unit: '%' },
  { id: 'heartbeats', label: 'Heartbeat', unit: '%' },
  { id: 'compatibility', label: '호환성', unit: '%' },
  { id: 'combined', label: '대회식 종합', unit: '점' },
];
export const SOURCES: Record<string, string> = { strata: 'Strata', physlib: 'PhysLib', cslib: 'CSLib', arklib: 'ArkLib', putnambench: 'PutnamBench', leanpool: 'LeanPool', unknown: '공개 대기' };
export const sourceName = (source: string) => SOURCES[source] ?? source;
export const format = (n: number | null, digits = 2): string => n === null ? '—' : n.toLocaleString('ko-KR', { minimumFractionDigits: digits, maximumFractionDigits: digits });
export const signed = (n: number) => `${n > 0 ? '+' : ''}${format(n)}`;
export const shortName = (name: string) => name.split('.').at(-1) || name;

// A zero baseline has no defined percentage reduction. Never turn missing data into zero.
export function reduction(before: number, after: number): number | null {
  return before > 0 ? (1 - after / before) * 100 : null;
}
export function valueOf(problem: Problem, metric: Metric): number | null {
  if (metric === 'combined' && ['failed', 'unsubmitted'].includes(problem.status)) return 0;
  if (!['measured', 'partial'].includes(problem.status) || !problem.baseline || !problem.candidate) return null;
  const token = reduction(problem.baseline.tokens, problem.candidate.tokens);
  const hb = reduction(problem.baseline.heartbeats, problem.candidate.heartbeats);
  const complete = problem.versions.length > 0 && problem.versions.every(v => v.status !== 'pending');
  const compatibility = complete ? 100 * problem.versions.filter(v => v.status === 'pass').length / problem.versions.length : null;
  if (metric === 'tokens') return token;
  if (metric === 'heartbeats') return hb;
  if (metric === 'compatibility') return compatibility;
  if (token === null || hb === null) return null;
  if (metric === 'improvement') return (token + hb) / 2;
  return compatibility === null ? null : (token + hb + compatibility) / 3;
}
export function deltaOf(problem: Problem, metric: Metric): number | null {
  const value = valueOf(problem, metric);
  if (value === null) return null;
  if (metric === 'compatibility') return problem.baselineCompatibility === null ? null : value - problem.baselineCompatibility;
  if (metric === 'combined') return problem.baselineCompatibility === null ? null : value - problem.baselineCompatibility / 3;
  return value;
}
export function aggregate(problems: Problem[], metric: Metric) {
  const values = problems.map(p => valueOf(p, metric)).filter((v): v is number => v !== null);
  const ready = metric !== 'combined' || values.length === problems.length;
  return { value: ready && values.length ? values.reduce((a, b) => a + b, 0) / values.length : null, count: values.length, total: problems.length };
}
export function waitingLabel(problem: Problem) {
  if (problem.status === 'missing') return '자료 미확보';
  if (problem.status === 'blocked') return '환경 준비 실패';
  if (problem.status === 'unsupported') return '검증기 지원 대기';
  if (problem.status === 'proof_failed') return '증명 검증 실패';
  if (problem.status === 'partial') return '일부 버전 검증';
  if (problem.status === 'unreleased') return '공개 대기';
  if (problem.status === 'failed') return '검증 실패';
  if (problem.status === 'unsubmitted') return '미제출';
  if (problem.status === 'measured') return '검증 완료';
  return '측정 대기';
}

function isRecord(v: unknown): v is Record<string, unknown> { return typeof v === 'object' && v !== null && !Array.isArray(v); }
function requireText(v: unknown, label: string, max = 2000): asserts v is string {
  if (typeof v !== 'string' || v.length > max) throw new Error(`${label}: 올바른 문자열이 필요합니다.`);
}
function measurement(v: unknown, label: string) {
  if (v === null) return;
  if (!isRecord(v) || !['tokens', 'heartbeats'].every(k => typeof v[k] === 'number' && Number.isFinite(v[k]) && v[k] >= 0 && v[k] <= Number.MAX_SAFE_INTEGER) || !Number.isInteger(v.tokens)) throw new Error(`${label}: 토큰은 0 이상의 정수, heartbeat는 0 이상의 유한한 수여야 합니다.`);
}
function validateProblem(p: unknown, count: number, ids: Set<number>) {
    if (!isRecord(p) || typeof p.id !== 'number' || !Number.isInteger(p.id) || p.id < 1 || p.id > count || ids.has(p.id)) throw new Error(`문제 번호는 1–${count} 사이에서 중복 없이 지정하세요.`);
    ids.add(p.id);
    for (const k of ['name', 'source', 'environment', 'candidateHash', 'note']) requireText(p[k], `P${p.id} ${k}`);
    if (!['measured', 'pending', 'unreleased', 'failed', 'unsubmitted', 'missing', 'blocked', 'unsupported', 'partial', 'proof_failed'].includes(String(p.status))) throw new Error(`P${p.id}: 알 수 없는 상태입니다.`);
    measurement(p.baseline, `P${p.id} 원본`); measurement(p.candidate, `P${p.id} 후보`);
    if (['measured', 'partial'].includes(String(p.status)) && (!p.baseline || !p.candidate || !p.name || !p.environment)) throw new Error(`P${p.id}: 측정된 문제에는 원본·후보·이름·환경이 필요합니다.`);
    if (!['measured', 'partial'].includes(String(p.status)) && p.candidate !== null) throw new Error(`P${p.id}: 미측정·실패 문제의 후보 측정값은 null이어야 합니다.`);
    if (p.baselineCompatibility !== null && (typeof p.baselineCompatibility !== 'number' || !Number.isFinite(p.baselineCompatibility) || p.baselineCompatibility < 0 || p.baselineCompatibility > 100)) throw new Error(`P${p.id}: 원본 호환성은 0–100 또는 null이어야 합니다.`);
    if (!Array.isArray(p.versions) || p.versions.length > 100) throw new Error(`P${p.id}: 버전 목록이 올바르지 않습니다.`);
    const pins = new Set<string>();
    for (const v of p.versions) {
      if (!isRecord(v)) throw new Error(`P${p.id}: 버전 항목이 올바르지 않습니다.`);
      requireText(v.version, 'version'); requireText(v.revision, 'revision');
      const pin = `${v.version}@${v.revision}`;
      if (!v.version || pins.has(pin) || !['pass', 'fail', 'pending'].includes(String(v.status))) throw new Error(`P${p.id}: 중복되거나 잘못된 버전 검사입니다.`);
      pins.add(pin);
    }
    if (!Array.isArray(p.evidence) || p.evidence.length > 100 || p.evidence.some(e => typeof e !== 'string' || e.length > 2000)) throw new Error(`P${p.id}: 근거 목록이 올바르지 않습니다.`);
}

// Imported JSON is data only. Reject inconsistent records before replacing the visible snapshot.
export function parseSnapshot(input: unknown): Snapshot {
  if (!isRecord(input) || input.schemaVersion !== 1) throw new Error('schemaVersion: 1 형식의 스냅샷이 필요합니다.');
  if (!['competition', 'warmup'].includes(String(input.dataset))) throw new Error('dataset은 competition 또는 warmup이어야 합니다.');
  for (const k of ['id', 'label', 'measuredAt', 'provenance']) requireText(input[k], k);
  if (!input.id || !input.label || !Number.isFinite(Date.parse(String(input.measuredAt)))) throw new Error('ID, 이름 또는 측정 시각이 올바르지 않습니다.');
  if (input.releaseDate !== null && (typeof input.releaseDate !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(input.releaseDate))) throw new Error('releaseDate는 YYYY-MM-DD 또는 null이어야 합니다.');
  const count = input.dataset === 'warmup' ? 15 : 50;
  if (!Array.isArray(input.problems) || input.problems.length !== count) throw new Error(`${input.dataset} 스냅샷에는 정확히 ${count}문제가 필요합니다.`);
  const ids = new Set<number>();
  for (const p of input.problems) validateProblem(p, count, ids);
  if (input.dataset === 'warmup') {
    for (const p of input.problems) {
      if (['unreleased', 'unsubmitted', 'failed'].includes(p.status)) throw new Error('웜업 실험에서는 미확보·증명 실패를 제출 점수 0으로 처리하지 않습니다.');
      requireText(p.selectedCandidateId, 'selectedCandidateId');
      requireText(p.selectionReason, 'selectionReason');
      if (!Array.isArray(p.teamResults) || p.teamResults.length > 100) throw new Error('팀 후보 목록이 필요합니다.');
      const candidateIds = new Set<string>();
      for (const c of p.teamResults) {
        if (!isRecord(c)) throw new Error('팀 후보 형식 오류');
        for (const k of ['id','author','sourcePath','sourceCommit','sourceState','candidateHash','note','environment']) requireText(c[k], k);
        requireText(c.proof, 'proof', 200000);
        if (!c.author || !c.proof || !['committed', 'working-tree-snapshot'].includes(String(c.sourceState)) || !/^[a-f0-9]{40}$/.test(String(c.sourceCommit))) throw new Error('팀 후보 출처가 올바르지 않습니다.');
        if (!['measured','partial','pending','blocked','unsupported','proof_failed'].includes(String(c.status))) throw new Error('팀 후보 검증 상태가 올바르지 않습니다.');
        if (!c.id || candidateIds.has(c.id as string) || !/^[a-f0-9]{64}$/.test(String(c.candidateHash))) throw new Error('팀 후보 ID 또는 해시 오류');
        candidateIds.add(c.id as string);
        // Reuse the result contract, without accepting recursively nested candidates.
        validateProblem({ id:p.id, name:p.name, source:p.source, status:c.status,
          baseline:c.baseline, candidate:c.candidate, baselineCompatibility:null, versions:c.versions,
          environment:c.environment, candidateHash:c.candidateHash, evidence:[], note:c.note }, count, new Set());
        const checks = c.versions as VersionCheck[];
        if (c.status === 'measured' && (!checks.length || checks.some(v => v.status !== 'pass'))) throw new Error('검증 완료 후보는 모든 지정 버전에서 통과해야 합니다.');
        if (c.status === 'partial' && (!checks.some(v => v.status === 'pass') || !checks.some(v => v.status === 'pending') || checks.some(v => v.status === 'fail'))) throw new Error('일부 버전 검증 상태와 검사 결과가 다릅니다.');
      }
      if (p.selectedCandidateId && !candidateIds.has(p.selectedCandidateId)) throw new Error('대표 후보가 목록에 없습니다.');
      if (!p.selectedCandidateId && p.teamResults.length) throw new Error('대표 후보를 명시하세요.');
      const selected = p.teamResults.find((c: TeamResult) => c.id === p.selectedCandidateId);
      if (selected) {
        for (const k of ['status', 'candidateHash', 'baseline', 'candidate', 'versions', 'environment']) {
          if (JSON.stringify(p[k]) !== JSON.stringify(selected[k])) throw new Error(`대표 후보와 문제의 ${k}가 다릅니다.`);
        }
      } else if (p.status !== 'missing' || p.candidateHash || p.baseline !== null || p.candidate !== null) {
        throw new Error('후보가 없는 문제는 자료 미확보 상태여야 합니다.');
      }
    }
  }
  // Copy only known fields, keeping credentials/extra fields out of subsequent exports.
  return {
    schemaVersion: 1, id: input.id as string, label: input.label as string, dataset: input.dataset as Snapshot['dataset'],
    measuredAt: input.measuredAt as string, releaseDate: input.releaseDate as string | null, provenance: input.provenance as string,
    problems: input.problems.map(p => ({ id: p.id, name: p.name, source: p.source, status: p.status,
      baseline: p.baseline && { tokens: p.baseline.tokens, heartbeats: p.baseline.heartbeats },
      candidate: p.candidate && { tokens: p.candidate.tokens, heartbeats: p.candidate.heartbeats },
      baselineCompatibility: p.baselineCompatibility,
      versions: p.versions.map((v: VersionCheck) => ({ version: v.version, revision: v.revision, status: v.status })),
      environment: p.environment, candidateHash: p.candidateHash, evidence: [...p.evidence], note: p.note,
      ...(input.dataset === 'warmup' ? { selectedCandidateId:p.selectedCandidateId, selectionReason:p.selectionReason,
        teamResults:p.teamResults.map((c: TeamResult) => ({id:c.id,author:c.author,proof:c.proof,sourcePath:c.sourcePath,
          sourceCommit:c.sourceCommit,sourceState:c.sourceState,status:c.status,candidateHash:c.candidateHash,note:c.note,
          environment:c.environment,baseline:c.baseline && {tokens:c.baseline.tokens,heartbeats:c.baseline.heartbeats},
          candidate:c.candidate && {tokens:c.candidate.tokens,heartbeats:c.candidate.heartbeats},
          versions:c.versions.map(v => ({version:v.version,revision:v.revision,status:v.status}))}))} : {}),
    })),
  };
}
