import { ArrowDownRight, ChartNoAxesCombined, Info } from 'lucide-react';
import { aggregate, format } from '../lib/model';
import type { Snapshot } from '../lib/model';

export function SummaryCards({ snapshot }: { snapshot: Snapshot }) {
  const scores = aggregate(snapshot.problems, 'improvement');
  const tokens = aggregate(snapshot.problems, 'tokens');
  const hb = aggregate(snapshot.problems, 'heartbeats');
  return <>
    <div className="summary-grid">
      <article className="summary-card primary-summary"><div className="summary-label">평균 개선 점수<ChartNoAxesCombined size={18}/></div>
        <div className="big-number">{format(scores.value)}<span>/ 100</span></div>
        <p>토큰 · heartbeat 감소율 평균 <span className="dot-separator">·</span> 로컬 지표</p>
      </article>
      <article className="summary-card"><div className="summary-label">토큰 감소<ArrowDownRight size={18}/></div>
        <div className="big-number">{format(tokens.value)}<span>%</span></div><p>문제별 감소율 평균 <span className="dot-separator">·</span> {tokens.count}문제 측정</p>
      </article>
      <article className="summary-card"><div className="summary-label">Heartbeat 감소<ArrowDownRight size={18}/></div>
        <div className="big-number">{format(hb.value)}<span>%</span></div><p>동일 환경의 원본과 비교 <span className="dot-separator">·</span> {hb.count}문제 측정</p>
      </article>
    </div>
    <div className="measurement-note"><Info size={14}/><span><strong>{scores.count} / {scores.total}</strong> 문제 측정 · 미측정은 위 평균에서 제외 · 검색·필터와 무관한 전체 데이터 기준</span><span className="local-only">공식 제출 점수 아님</span></div>
  </>;
}
