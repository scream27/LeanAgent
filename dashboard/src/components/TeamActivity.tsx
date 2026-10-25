import { useState } from 'react';
import { ExternalLink, Search } from 'lucide-react';
import activity from '../data/team-activity.json';

const statusName: Record<string, string> = { open: '검토 중', merged: '병합됨', closed: '병합 없이 닫힘' };
const kindName: Record<string, string> = { refactoring: '증명 개선', measurement: '측정·재현', repair: '오류 수리', microbenchmark: '비용 분석' };
const metricNames: Record<string, string> = {
  tokens: '토큰', bestTokens: '최소 토큰', baselineTokens: '원본 토큰', heartbeats: 'HB', bestHeartbeats: '최소 HB',
  baselineHeartbeats: '원본 HB', rawHeartbeats: 'raw HB', heartbeatReductionPercent: 'HB 감소(%)',
  candidateCount: '후보 수', reportedPassCount: '보고된 통과 수', reportedVersionsPassed: '통과 버전', reportedVersionsTotal: '지정 버전',
  candidateId: '후보', condition: '조건', status: '보고 상태', lengthBestTokens: '길이 최소 토큰', lengthBestHeartbeats: '길이 최소 HB',
  heartbeatBestTokens: 'HB 최소 토큰', heartbeatBestHeartbeats: 'HB 최소 HB', runs: '실행', proposals: '생성 후보',
  validProposals: '유효 후보', finalPassRuns: '최종 통과 실행', finalTimeoutRuns: '최종 시간 초과',
  completed: '완료', planned: '계획', verified: '검증 통과', model_calls: '모델 호출', error_category: '오류 유형',
  measurementRecords: '측정 기록', inputRuns: '입력 실행', promptSlots: '프롬프트 슬롯', changedBodies: '변경 본문',
  reportedVersionChecks: '버전 검사', selectedImprovements: '선택된 개선', reportedMeanScore: '보고된 평균 점수',
  selected_generated: '생성 후보 선택', selected_original: '원본 유지', improved: '개선 수', mean_token_reduction: '평균 토큰 감소(%)',
  mean_heartbeat_reduction: '평균 HB 감소(%)', mean_compatibility: '평균 호환성(%)', mean_local_score: '보고된 로컬 점수',
  compatibility_measured: '호환성 측정 수', generated_candidates: '생성 후보', cases: '대조 사례', attempts: '시도',
  restored_original_exact: '원본 그대로 복원', verified_different_bytes: '다른 증명으로 통과',
  problem1MeanCostL: 'P01 L 평균 비용', problem1MeanCostS: 'P01 S 평균 비용',
  problem13MeanCostL: 'P13 L 평균 비용', problem13MeanCostS: 'P13 S 평균 비용',
};
function reportedMetrics(rows: Record<string, unknown>[]) {
  return rows.map((row, index) => {
    const entries = Object.entries(row).filter(([key, value]) => metricNames[key] && value !== null && ['number', 'string'].includes(typeof value));
    if (!entries.length) return null;
    return <li key={index}>
    {typeof row.problemId === 'number' ? <strong>P{String(row.problemId).padStart(2, '0')} </strong> : null}
    {entries.map(([key, value]) =>
      <span key={key}>{metricNames[key]} <b>{typeof value === 'number' ? value.toLocaleString('ko-KR', { maximumFractionDigits: 4 }) : String(value)}</b></span>)}
    {typeof row.proofUrl === 'string' ? <a href={row.proofUrl} target="_blank" rel="noreferrer">증명 보기 </a> : null}
    {typeof row.resultUrl === 'string' ? <a href={row.resultUrl} target="_blank" rel="noreferrer">결과 근거</a> : null}
  </li>;
  });
}

export function TeamActivity() {
  const [author, setAuthor] = useState('all');
  const [status, setStatus] = useState('all');
  const [problem, setProblem] = useState('all');
  const [query, setQuery] = useState('');
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const groups = activity.candidateGroups;
  const filtered = activity.pullRequests.filter(pr => {
    const related = groups.filter(g => g.prNumbers.includes(pr.number));
    const research = activity.researchGroups.filter(g => g.prNumbers.includes(pr.number));
    return (author === 'all' || pr.author === author) && (status === 'all' || pr.status === status)
      && (problem === 'all' || related.some(g => g.problemIds.some(id => id === Number(problem))))
      && (!normalizedQuery || `${pr.number} ${pr.title} ${pr.author} ${pr.authorName} ${[...related, ...research].map(g => g.title).join(' ')}`.toLocaleLowerCase().includes(normalizedQuery));
  });
  return <section className="panel activity-panel" id="team-records" aria-labelledby="activity-title">
    <div className="panel-title"><h2 id="activity-title">팀원 전체 PR과 실험</h2><a href="https://github.com/Pseudo-Lab/LeanAgent/pulls" target="_blank" rel="noreferrer">GitHub에서 보기 <ExternalLink size={13}/></a></div>
    <p className="section-intro">7명 · PR 30개 · 실험 36묶음. 병합 전 자료와 실패·수리 기록도 출처별로 확인할 수 있습니다.</p>
    <p className="source-disclosure">추가 실험은 작성자가 보고한 결과입니다. 위 점수표의 공통 환경 재검증값과 구분하며, 원시·scaled HB를 합산하지 않습니다. 개별 시도 전체는 각 원문에 연결합니다.</p>
    <div className="people-filter" role="group" aria-label="팀원 선택">
      <button aria-pressed={author === 'all'} onClick={() => setAuthor('all')}>전체 <span>30</span></button>
      {activity.authors.map(person => <button key={person.login} aria-pressed={author === person.login} onClick={() => setAuthor(person.login)}>{person.name} <span>{person.prNumbers.length}</span></button>)}
    </div>
    <div className="activity-toolbar">
      <label className="search-field"><Search size={16}/><input aria-label="PR 검색" placeholder="PR 번호, 팀원, 실험 검색" value={query} onChange={e => setQuery(e.target.value)}/></label>
      <select aria-label="PR 상태" value={status} onChange={e => setStatus(e.target.value)}><option value="all">전체 상태</option><option value="open">검토 중 · 6</option><option value="merged">병합됨 · 21</option><option value="closed">병합 없이 닫힘 · 3</option></select>
      <select aria-label="실험 문제" value={problem} onChange={e => setProblem(e.target.value)}><option value="all">전체 문제</option>{Array.from({ length: 15 }, (_, i) => <option key={i + 1} value={i + 1}>P{String(i + 1).padStart(2, '0')}</option>)}</select>
    </div>
    <p className="activity-count" role="status">{filtered.length} / 30 PR · 조회 기준 {new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium', timeZone: 'Asia/Seoul' }).format(new Date(activity.retrievedAt))}</p>
    <div className="pr-list">{filtered.map(pr => {
      const related = groups.filter(g => g.prNumbers.includes(pr.number) && (problem === 'all' || g.problemIds.some(id => id === Number(problem))));
      return <article key={pr.number} className="pr-card">
        <div className="pr-meta"><span className={`pr-status pr-${pr.status}`}>{statusName[pr.status]}</span><strong>{pr.authorName}</strong><span>#{pr.number}</span><span>{pr.updatedAt.slice(0, 10)}</span></div>
        <h3><a href={pr.url} target="_blank" rel="noreferrer">{pr.title} <ExternalLink size={13}/></a></h3>
        {pr.status === 'closed' ? <p className="closed-pr-note">{pr.number === 21 ? '철회된 초안입니다.' : '이전 중복 PR입니다. 최신 #27과 실험을 중복 집계하지 않습니다.'}</p> : null}
        {related.length ? <details className="experiment-details"><summary>실험과 후보 {related.length}묶음 보기</summary>{related.map(group => <section key={group.id} className="experiment-group">
          <h4>{group.title} <small>{kindName[group.kind] ?? group.kind}</small></h4>
          <p className="problem-tags">{group.problemIds.length === 15 ? 'P01–P15 전체' : group.problemIds.map(id => `P${String(id).padStart(2, '0')}`).join(' · ') || '문제 외 비용 분석'}</p>
          <p>{group.verification.notes}</p>
          {group.metrics.length ? <ul className="reported-metrics">{reportedMetrics(group.metrics)}</ul> : null}
          <div className="evidence-links">{group.evidence.map((evidence, index) => <a key={`${evidence.url}-${index}`} href={evidence.url} target="_blank" rel="noreferrer">{evidence.label === '근거' ? `원문 근거 ${index + 1}` : evidence.label} <ExternalLink size={12}/></a>)}</div>
        </section>)}</details> : <p className="document-pr">문서·연구·일정 또는 자료 정리 · <a href={`${pr.url}/files`} target="_blank" rel="noreferrer">변경 자료 보기</a></p>}
        {activity.researchGroups.filter(g => g.prNumbers.includes(pr.number)).map(study => <section key={study.id} className="experiment-group">
          <h4>{study.title}</h4><p>추출한 선언 {study.metrics.extractedDeclarations.toLocaleString('ko-KR')}개 · 직접 sorry가 없는 by 증명 {study.metrics.byProofsWithoutDirectSorry.toLocaleString('ko-KR')}개</p><p>{study.verification.notes}</p>
          <div className="evidence-links">{study.evidence.map(e => <a key={e.url} href={e.url} target="_blank" rel="noreferrer">{e.label} <ExternalLink size={12}/></a>)}</div>
        </section>)}
      </article>;
    })}</div>
    {!filtered.length ? <p className="empty-search">조건에 맞는 PR이 없습니다. 검색어나 필터를 바꿔주세요.</p> : null}
    <details className="collection-note"><summary>수집 범위와 근거</summary><p>{activity.scope}</p><p>전체 PR 목록의 1페이지 30개와 다음 페이지 0개를 확인했습니다. #24의 변경 파일 API는 3,000개 제한이 있어 하위 트리와 보고서를 추가 확인했습니다. PR 전체 수집과 모든 후보 파일의 재검증은 구분합니다.</p><p>기존 점수표의 로컬 스냅샷 후보는 근거 없이 특정 PR에 귀속시키지 않았습니다. 논문·코퍼스 통계 자료도 해당 PR 링크로 확인할 수 있습니다.</p></details>
  </section>;
}
