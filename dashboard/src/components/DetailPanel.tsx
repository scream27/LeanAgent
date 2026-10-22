import { ArrowDownRight, ArrowUpRight, Check, Clock3, FileCheck2, LockKeyhole, Minus } from 'lucide-react';
import { METRICS, aggregate, deltaOf, format, signed, sourceName, valueOf, waitingLabel } from '../lib/model';
import type { Metric, Problem, Snapshot } from '../lib/model';

function ReductionBar({ label, value }: { label: string; value: number | null }) {
  return <div className="reduction-row"><span>{label}</span><div className="bar-track"><div className={value !== null && value < 0 ? 'bar-fill regression' : 'bar-fill'} style={{ width: `${Math.min(100, Math.abs(value ?? 0))}%` }}/></div><strong>{format(value)}{value === null ? '' : '%'}</strong></div>;
}

export function DetailPanel({ problem, metric, snapshot }: { problem: Problem | null; metric: Metric; snapshot: Snapshot }) {
  if (!problem) return <aside className="panel detail-panel empty-detail"><FileCheck2 size={28}/><p>문제를 선택하면 세부 점수가 표시됩니다.</p></aside>;
  const selectedValue = valueOf(problem, metric);
  const token = valueOf(problem, 'tokens');
  const hb = valueOf(problem, 'heartbeats');
  const compat = valueOf(problem, 'compatibility');
  const combined = valueOf(problem, 'combined');
  const total = aggregate(snapshot.problems, 'combined');
  const delta = deltaOf(problem, metric);
  const Arrow = delta !== null && delta < 0 ? ArrowDownRight : delta !== null && delta > 0 ? ArrowUpRight : Minus;
  const currentMetric = METRICS.find(m => m.id === metric)!;
  return <aside className="panel detail-panel" id="problem-detail" tabIndex={-1} aria-labelledby="detail-title">
    <div className="detail-heading"><span><strong>P{String(problem.id).padStart(2, '0')}</strong><span className="dot-separator">·</span>{sourceName(problem.source)}</span><span className="detail-tag">문제 상세</span></div>
    <h2 id="detail-title" className="theorem-name">{problem.name || '아직 공개되지 않은 문제'}</h2>
    {problem.status === 'unreleased' ? <div className="release-detail"><div className="lock-icon"><LockKeyhole size={26}/></div><h3>11월 1일, 새로운 문제가 열립니다.</h3><p>현재 15문제에 이어질 자리를 준비했어요.<br/>공개된 문제와 측정 결과를 연결하면<br/>같은 화면에서 점수와 개선을 확인할 수 있습니다.</p><span>공개 예정 · 2026.11.01</span></div> : <>
      <div className={`detail-score ${selectedValue !== null && selectedValue < 0 ? 'negative-score' : ''}`}><span>{currentMetric.label}{metric === 'combined' ? ' · 로컬 추정' : ''}</span><div><strong>{format(selectedValue)}</strong><small>{selectedValue === null ? waitingLabel(problem) : currentMetric.unit === '%' ? '%' : '/ 100'}</small>{delta !== null && metric !== 'compatibility' ? <span className="detail-delta"><Arrow size={16}/>{signed(delta)}{metric === 'combined' ? 'p' : '%'}</span> : null}</div></div>
      <table className="metrics-table"><caption className="sr-only">원본과 선택 후보의 평가 항목 비교</caption><thead><tr><th>평가 항목</th><th>원본</th><th>선택 후보</th><th>점수</th></tr></thead><tbody>
        <tr><th>토큰</th><td>{format(problem.baseline?.tokens ?? null, 0)}</td><td>{format(problem.candidate?.tokens ?? null, 0)}</td><td className={token !== null && token < 0 ? 'negative' : 'positive'}>{format(token)}</td></tr>
        <tr><th>Heartbeat</th><td>{format(problem.baseline?.heartbeats ?? null, 0)}</td><td>{format(problem.candidate?.heartbeats ?? null, 0)}</td><td className={hb !== null && hb < 0 ? 'negative' : 'positive'}>{format(hb)}</td></tr>
        <tr><th>호환성</th><td>{format(problem.baselineCompatibility, 0)}{problem.baselineCompatibility === null ? '' : '%'}</td><td>{problem.versions.filter(v => v.status === 'pass').length} / {problem.versions.length} 통과</td><td className="positive">{format(compat)}</td></tr>
      </tbody></table>
      <div className="reduction-bars"><h3>감소율 시각화</h3><ReductionBar label="토큰" value={token}/><ReductionBar label="Heartbeat" value={hb}/></div>
      <div className="contest-score"><span>대회식 종합 <small>세 항목 평균</small></span><strong>{format(combined)}<small> / 100</small></strong></div>
      <div className="version-list" aria-label="버전별 검증 결과">{problem.versions.map(v => <span key={`${v.version}-${v.revision}`} className={`version-${v.status}`} title={`${v.version} · ${v.revision} · ${v.status === 'pass' ? '통과' : v.status === 'fail' ? '실패' : '대기'}`}>{v.status === 'pass' ? <Check size={12}/> : <Clock3 size={12}/>} {v.version}</span>)}</div>
      <p className="detail-note">{problem.note || waitingLabel(problem)}</p>
      {problem.environment ? <div className="provenance"><span>측정 환경</span><code>{problem.environment}</code></div> : null}
      {problem.candidateHash ? <details className="evidence"><summary>측정 근거 · {problem.candidateHash.slice(0, 10)}</summary><p>후보 SHA-256: <code>{problem.candidateHash}</code></p>{problem.evidence.map(e => <code key={e}>{e}</code>)}</details> : null}
    </>}
    <div className="dataset-total"><span>전체 {snapshot.problems.length}문제 대회식 종합</span><strong>{format(total.value)}{total.value === null ? '' : '점'}</strong><small>{total.count} / {total.total}문제 산출 완료{total.value === null ? ' · 전체 점수 집계 대기' : ' · 공식 점수 아님'}</small></div>
  </aside>;
}
