import { ExternalLink } from 'lucide-react';

export function ScoringGuide({ warmup = false }: { warmup?: boolean }) {
  return <section className="panel scoring-guide" aria-labelledby="scoring-title">
    <div className="panel-title"><h2 id="scoring-title">점수 산출 기준</h2><a href="https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena" target="_blank" rel="noreferrer">Arena 원문<ExternalLink size={12}/></a></div>
    <div className="formula-grid">
      <div><h3><span>01</span> 토큰 감소 점수</h3><p>증명 본문의 토큰이 얼마나 줄었는지 계산합니다.</p><code>(1 − 후보 토큰 / 원본 토큰) × 100</code></div>
      <div><h3><span>02</span> Heartbeat 감소 점수</h3><p>같은 Lean 환경에서 측정한 컴파일 비용을 비교합니다.</p><code>(1 − 후보 HB / 원본 HB) × 100</code></div>
      <div><h3><span>03</span> 호환성 점수</h3><p>동일 후보가 지정된 버전에서 그대로 통과한 비율입니다.</p><code>통과 버전 수 / 전체 지정 버전 수 × 100</code></div>
    </div>
    <div className="scoring-footnote"><p><strong>개선 점수</strong>는 토큰·heartbeat 두 감소율의 평균입니다. <strong>대회식 종합</strong>은 위 세 항목의 평균이며, 전체 점수는 모든 문제 점수의 평균입니다. {warmup ? '팀 실험에서는 자료 미확보·환경 오류·증명 실패를 0점으로 합산하지 않습니다.' : '미제출·검증 실패는 0점으로 포함합니다.'}</p><p>음수 점수는 퇴보를 뜻합니다. 미공개·미측정·검증 진행은 0점으로 바꾸지 않고 대기 상태로 표시합니다. 원본이 0이면 감소율은 산출하지 않습니다. 현재 데이터는 로컬 측정이며 공식 worker 결과와 다를 수 있습니다. 산식 출처: 보관된 Arena 코드 56aa7b8.</p></div>
  </section>;
}
