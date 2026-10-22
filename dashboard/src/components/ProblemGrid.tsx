import { ArrowDownRight, ArrowUpRight, Check, LockKeyhole, Minus, Search, SlidersHorizontal } from 'lucide-react';
import { METRICS, deltaOf, format, shortName, signed, sourceName, valueOf, waitingLabel } from '../lib/model';
import { scoreColors, scoreGradient } from '../lib/heatmap';
import type { Metric, Problem, Snapshot } from '../lib/model';

type Props = {
  snapshot: Snapshot; metric: Metric; onMetric: (metric: Metric) => void;
  query: string; onQuery: (query: string) => void; source: string; onSource: (source: string) => void;
  sort: string; onSort: (sort: string) => void; visible: Problem[]; selected: Problem | null;
  onSelect: (problem: Problem) => void; compact: boolean;
};

function ProblemTile({ problem, metric, selected, onSelect }: { problem: Problem; metric: Metric; selected: boolean; onSelect: () => void }) {
  const value = valueOf(problem, metric);
  const delta = deltaOf(problem, metric);
  const warning = (value !== null && value <= 60) || ['failed', 'unsubmitted'].includes(problem.status);
  const Arrow = delta !== null && delta < 0 ? ArrowDownRight : delta !== null && delta > 0 ? ArrowUpRight : Minus;
  const unit = METRICS.find(m => m.id === metric)!.unit;
  const measured = problem.status === 'measured' ? problem.candidate : null;
  const tokens = measured ? measured.tokens.toLocaleString('ko-KR') : '—';
  const heartbeats = measured ? measured.heartbeats.toLocaleString('ko-KR', { maximumFractionDigits: 20 }) : '—';
  return <button className={`problem-tile ${warning ? 'tone-warning' : value === null ? 'tone-unknown' : ''} ${selected ? 'is-selected' : ''} ${problem.status === 'unreleased' ? 'is-locked' : ''}`}
    style={scoreColors(value)}
    aria-pressed={selected} aria-label={`P${String(problem.id).padStart(2, '0')} ${problem.name || '공개 대기'} ${value === null ? waitingLabel(problem) : `${format(value)}${unit}`}${warning ? ', 경고' : ''}${measured ? `, 선택 후보 토큰 ${tokens}, heartbeat ${heartbeats}` : ''}`}
    onClick={onSelect} title={problem.name || '11월 1일 공개 예정'}>
    <span className="tile-top"><strong>P{String(problem.id).padStart(2, '0')}</strong>{problem.status === 'unreleased' ? <LockKeyhole size={13}/> : <span>{sourceName(problem.source)}</span>}</span>
    <span className="tile-value">{format(value)}{value !== null && unit === '%' ? <small>%</small> : null}</span>
    <span className="tile-delta">{value === null ? <>{waitingLabel(problem)}</> : metric === 'compatibility' ? <><Check size={13}/>{problem.versions.filter(v => v.status === 'pass').length} / {problem.versions.length} 버전</> : delta !== null ? <><Arrow size={14}/>{signed(delta)}{metric === 'combined' ? 'p' : '%'}</> : <>{waitingLabel(problem)}</>}</span>
    {problem.status !== 'unreleased' ? <span className="tile-measurements">
      <span title={`선택 후보의 증명 토큰 수${problem.baseline ? ` · 원본 ${problem.baseline.tokens.toLocaleString('ko-KR')}` : ''}`}><span>토큰</span><strong>{tokens}</strong></span>
      <span title={`선택 후보의 heartbeat${problem.environment ? ` · ${problem.environment}` : ''}`}><abbr title="Heartbeat">HB</abbr><strong>{heartbeats}</strong></span>
    </span> : null}
    <span className="tile-name">{problem.status === 'unreleased' ? '11.01 공개 예정' : shortName(problem.name)}</span>
  </button>;
}

export function ProblemGrid(props: Props) {
  const { snapshot, metric, onMetric, query, onQuery, source, onSource, sort, onSort, visible, selected, onSelect } = props;
  const sources = [...new Set(snapshot.problems.filter(p => p.source !== 'unknown').map(p => p.source))];
  const measuredProblems = snapshot.problems.filter(p => p.status === 'measured');
  const heartbeatUnit = measuredProblems.length && measuredProblems.every(p => p.environment.includes('raw heartbeat')) ? 'raw' : measuredProblems.length && measuredProblems.every(p => p.environment.includes('scaled heartbeat')) ? 'scaled' : null;
  return <section className="panel grid-panel" aria-labelledby="grid-title">
    <div className="panel-title"><h2 id="grid-title">문제별 개선 현황</h2><span>{visible.length} / {snapshot.problems.length}문제</span></div>
    <div className="metric-tabs" role="group" aria-label="점수 지표">{METRICS.map(m => <button key={m.id} aria-pressed={metric === m.id} className={metric === m.id ? 'active' : ''} onClick={() => onMetric(m.id)}>{m.label}</button>)}</div>
    <div className="grid-toolbar">
      <div className="search-field"><Search size={16}/><input aria-label="문제 검색" placeholder="번호, 문제명 검색" value={query} onChange={e => onQuery(e.target.value)}/></div>
      <select aria-label="출처 필터" value={source} onChange={e => onSource(e.target.value)}><option value="all">전체 출처</option>{sources.map(s => <option key={s} value={s}>{sourceName(s)}</option>)}</select>
      <select aria-label="정렬" value={sort} onChange={e => onSort(e.target.value)}><option value="number">번호순</option><option value="high">점수 높은순</option><option value="low">점수 낮은순</option></select>
    </div>
    <p className="metric-context">{metric === 'combined' ? '세 평가 항목의 평균' : metric === 'compatibility' ? '지정 버전 통과율' : '원본 대비 개선율'} · 60 이하 빨간 경고 · 60 초과부터 100까지 연속 색상</p>
    <p className="measurement-key">타일 하단은 선택 후보의 실제 수치 <span>토큰 길이 / HB{heartbeatUnit ? ` (${heartbeatUnit})` : ' (heartbeat)'}</span></p>
    {visible.length ? <div className={`problem-grid ${props.compact && snapshot.problems.length === 50 ? 'fifty-grid' : ''}`}>
      {visible.map(p => <ProblemTile key={p.id} problem={p} metric={metric} selected={selected?.id === p.id} onSelect={() => onSelect(p)}/>)}
    </div> : <div className="empty-search"><SlidersHorizontal size={26}/><strong>일치하는 문제가 없습니다</strong><span>검색어나 출처 필터를 바꿔보세요.</span><button className="text-button" onClick={() => { onQuery(''); onSource('all'); }}>필터 초기화</button></div>}
    <div className="legend" aria-label="색상 범례">
      <span><i className="tone-warning"/>60 이하 · 경고</span>
      <div className="legend-scale" aria-label="60 초과부터 100까지 연한 초록에서 진한 초록으로 연속 변화">
        <div className="legend-gradient" style={{ background: scoreGradient }}/>
        <div className="legend-ticks"><span>60</span><span>70</span><span>80</span><span>90</span><span>100</span></div>
      </div>
      <span><i className="tone-unknown"/>{metric === 'compatibility' ? '검증 대기' : '미측정'}</span>
    </div>
  </section>;
}
