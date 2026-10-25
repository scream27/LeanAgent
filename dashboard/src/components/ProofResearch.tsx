import { ExternalLink } from 'lucide-react';

const papers = [
  { title: 'LeanPolish: Verified Supervision for Lean Proof Compression', id: '2609.38384', page: 3,
    method: '작은 tactic·블록 교체, 사용하지 않는 사실과 도달하지 않는 분기 제거, 변경 후 전체 파일 재검증을 반복합니다.',
    application: 'P09의 repeat\' first와 <;> 분기를 작은 편집 단위로 삼았습니다. 첫 성공에서 멈추지 않고 정해진 후보 목록의 성공·실패를 모두 기록했습니다.' },
  { title: 'Lean Refactor: Multi-Objective Controllable Proof Optimization via Agentic Strategy Search', id: '2605.20244', page: 5,
    method: '길이·컴파일 비용·버전 호환성을 별도 목표로 두고, 목표에 맞는 전략을 선택합니다.',
    application: 'P09에서는 토큰만 줄인 후보를 바로 채택하지 않습니다. 같은 환경의 토큰·HB 평균으로 선택하고 버전 검사 결과도 별도로 남깁니다.' },
  { title: 'ProofOptimizer: Training Language Models to Simplify Proofs without Human Demonstrations', id: '2510.15700', page: 6,
    method: '검증된 후보를 반복적으로 줄이며, 무효 후보는 원본 비용으로 되돌리는 min@k·red@k로 평가합니다.',
    application: '이번에는 모델 학습을 재현하지 않았습니다. 검증된 기존 증명을 보존하고, 실패 후보도 22개 시도 목록에 남기는 평가 원칙만 적용했습니다.' },
  { title: 'ImProver: Agent-Based Automated Proof Optimization', id: '2410.04753', page: 5,
    method: '정확성을 먼저 확인하고 목표 점수로 후보를 고릅니다. 중간 proof state와 컴파일 오류를 후속 수정에 전달합니다.',
    application: 'P09의 choice/bisim 관계와 전이 분기를 확인하며 국소 수정을 시험했습니다. 검증에 실패한 짧은 코드는 개선으로 세지 않습니다.' },
  { title: 'LEVER: Adaptive Cost-Aware Proof Search Over AND/OR Graphs', id: '2610.11862', page: 2,
    method: '완성된 증명을 고친 뒤 평가하는 대신, 부분 증명을 탐색할 때부터 비용과 품질 목표를 반영합니다.',
    application: '후속 구조 탐색의 참고입니다. 이미 79토큰인 이번 증명에는 새 그래프 검색기를 구현하지 않았으며, LEVER의 성능을 재현했다고 주장하지 않습니다.' },
];

export function ProofResearch() {
  return <section className="panel research-panel" id="p09-research" aria-labelledby="research-title">
    <div className="panel-title"><h2 id="research-title">P04·P09 · 논문과 개선 실험</h2><span>2026. 10. 26. 조사</span></div>
    <p className="section-intro">P09는 더 짧게 만들 수 있었지만, 이번 탐색에서 두 지표를 함께 크게 개선한 후보는 찾지 못했습니다.</p>
    <div className="research-verdict"><strong>현재 권고: 79토큰 대표 후보 유지</strong><p>76토큰 후보는 길이 우선의 대안입니다. HB까지 같은 비중으로 평가하면 기존 79토큰 후보가 낫습니다. 100점까지 남은 점수는 추가 개선의 존재를 보장하지 않습니다.</p></div>
    <div className="research-table-wrap"><table className="research-table"><caption>P09 · Lean v4.32.0 · 같은 전체 문맥 검증 도구에서 각 3회 측정</caption><thead><tr><th>후보</th><th>토큰</th><th>HB</th><th>개선 점수</th><th>판단</th></tr></thead><tbody>
      <tr><th>원본 증명</th><td>251</td><td>3,856</td><td>0.00</td><td>비교 기준</td></tr>
      <tr><th>기존 최종본</th><td>79</td><td>516</td><td>77.57</td><td>현재 유지</td></tr>
      <tr><th>국소 자동화 교체</th><td>76</td><td>642</td><td>76.54</td><td>길이 우선 대안</td></tr>
      <tr><th>명시적 생성자 변형</th><td>79</td><td>515</td><td>77.59</td><td>+0.013점의 미세 차이</td></tr>
    </tbody></table></div>
    <p className="source-disclosure">표의 HB는 이번 전체 문맥 검증 도구의 결과입니다. 기존 점수표의 원본·후보 HB와는 계측 경로가 달라 섞지 않았습니다. 토큰은 LLM 사용량이 아닌 증명 본문의 구문 토큰입니다.</p>
    <div className="research-columns"><div><h3>9번에서 무엇을 바꿨나</h3><ol>
      <li><code>And.imp (by first | exact id | exact Tr.choiceL)</code>의 국소 자동화를 <code>solve_by_elim [Tr.choiceL]</code>로 바꿔 3토큰을 줄였습니다. HB는 늘었습니다.</li>
      <li>명시적 생성자 추론, 분기 순서, 직접 적용과 큰 자동화를 포함해 22개 변형을 시험했습니다. 통과 12개·실패 10개를 모두 기록했습니다.</li>
      <li>원본·기존 최종본·두 비교 후보를 각각 새 프로세스에서 3번 검증했습니다. 명제 보존과 허용 공리도 확인했습니다.</li>
    </ol><p>다음 구조 실험은 <code>ChoiceBisim.choice</code>와 <code>ChoiceBisim.bisim</code>의 전이 의무를 분리해, 탐색으로 처리하던 분기를 직접 닫는 것입니다. 아직 개선이 검증된 방법은 아닙니다.</p></div>
      <div><h3>9번의 호환성 대기 해소</h3><p>기존 79토큰 증명은 v4.31.0·v4.32.0·v4.33.0-rc2의 정확한 지정 커밋과 의존성에서 각각 3/3 통과했습니다. 원본 증명도 같은 세 환경에서 각각 3/3 통과했습니다. 대기였던 v4.33.0-rc2를 보완해 호환성은 100%로 확인했습니다.</p><p>호환성 100%가 증명 길이·HB 개선 점수를 100점으로 바꾸지는 않습니다. 기존 성능 측정값은 유지하고 호환성 결과만 보완했습니다. P04의 이 국소 실험 기준 최종본은 123토큰이며, 진행 중인 전체 15문제 탐색과 구분합니다.</p><a href="/research/p09/experiment.json" target="_blank" rel="noreferrer">이번 실험의 후보·검증 근거 <ExternalLink size={13}/></a><p className="small-print">같은 컴퓨터에서 수행한 한 정리의 제한된 탐색입니다. 모든 가능한 증명 중 최단이라는 주장이나, 모델 생성 성공률의 추정으로 해석하지 않습니다.</p></div></div>
    <figure className="paper-figure"><img src="/research/p09/leanpolish-figure1.png" alt="LeanPolish 원문 그림 1. 국소 교체와 정리 후 새 Lean 프로세스에서 재검증하고 변화가 없을 때까지 반복하는 흐름." loading="lazy"/><figcaption>LeanPolish 원문 Figure 1, p. 3. 국소 변경 후 전체 파일 검증을 반복하는 흐름이 이번 P09 실험과 가장 직접적으로 연결됩니다. <a href="https://www.alphaxiv.org/pdf/2609.38384?page=3" target="_blank" rel="noreferrer">원문</a></figcaption></figure>
    <h3 className="reading-heading">원문에서 가져온 방법과 이번 적용</h3>
    <div className="paper-list">{papers.map(paper => <article key={paper.id}><h4><a href={`https://www.alphaxiv.org/pdf/${paper.id}?page=${paper.page}`} target="_blank" rel="noreferrer">{paper.title} <ExternalLink size={13}/></a></h4><p>{paper.method}</p><p className="paper-application">{paper.application}</p></article>)}</div>
    <details className="collection-note"><summary>검색·평가와 paperthin 라우팅</summary><p>alphaXiv 의미 검색과 OpenAlex에서 Lean proof refactoring·token·heartbeat를 검색하고, 기존 보고서에서 발견한 ProofOptimizer·ImProver를 표제어로 보완했습니다. 관련성으로 5편을 골라 원문을 확인했습니다. 체계적 문헌고찰이나 전 분야의 완전한 목록은 아닙니다.</p><p><a href="https://github.com/LilMGenius/paperthin" target="_blank" rel="noreferrer">paperthin</a>의 readchk로 작업 범위를 확인하고 ponytail로 기존 대시보드를 확장했습니다. mandela로 점수·실패 집계의 독립성을 점검하고, sip으로 출처·화면·문서의 일관성을 재검토했습니다. 증명 채택은 에이전트의 동의가 아니라 Lean 검증과 고정된 측정 기준에 따릅니다.</p></details>
  </section>;
}
