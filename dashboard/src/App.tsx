import { useEffect, useRef, useState } from 'react';
import { Brackets, Check, Download, Info, Upload, X } from 'lucide-react';
import { DetailPanel } from './components/DetailPanel';
import { ProblemGrid } from './components/ProblemGrid';
import { ScoringGuide } from './components/ScoringGuide';
import { SummaryCards } from './components/SummaryCards';
import { TeamActivity } from './components/TeamActivity';
import { ProofResearch } from './components/ProofResearch';
import { parseSnapshot, valueOf } from './lib/model';
import type { Metric, Problem, Snapshot } from './lib/model';

export default function App() {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [snapshotId, setSnapshotId] = useState('');
  const [error, setError] = useState('');
  const [loaded, setLoaded] = useState(false);
  const [notice, setNotice] = useState('');
  const [metric, setMetric] = useState<Metric>('improvement');
  const [selectedId, setSelectedId] = useState(1);
  const [query, setQuery] = useState('');
  const [source, setSource] = useState('all');
  const [sort, setSort] = useState('number');
  const [scope, setScope] = useState<'all' | 'released'>('all');
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    const get = async (url: string) => { const response = await fetch(url, { signal: controller.signal }); if (!response.ok) throw new Error(`데이터 요청 실패 (${response.status})`); return response.json(); };
    (async () => {
      const files: unknown = await get('/data/index.json');
      if (!Array.isArray(files) || files.some(f => typeof f !== 'string' || !/^[a-z0-9-]+\.json$/.test(f))) throw new Error('데이터 목록 형식이 올바르지 않습니다.');
      const data = await Promise.all(files.map(async f => parseSnapshot(await get(`/data/${f}`))));
      setSnapshots(data);
      setLoaded(true);
    })().catch(e => { if (e.name !== 'AbortError') setError(`스냅샷을 불러오지 못했습니다. ${e.message}`); });
    return () => controller.abort();
  }, []);

  const snapshot = snapshots.find(s => s.id === snapshotId) ?? snapshots[0];
  function chooseSnapshot(id: string) { setSnapshotId(id); setSelectedId(1); setQuery(''); setSource('all'); setSort('number'); }
  function chooseProblem(p: Problem) {
    setSelectedId(p.id);
    if (window.matchMedia('(max-width: 959px)').matches) requestAnimationFrame(() => document.getElementById('problem-detail')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' }));
  }
  async function importFile(file: File | undefined) {
    if (!file) return;
    setError(''); setNotice('');
    try {
      if (file.size > 2_000_000) throw new Error('파일은 2MB 이하여야 합니다.');
      const imported = parseSnapshot(JSON.parse(await file.text()));
      const local = { ...imported, id: `import-${Date.now()}`, label: `${imported.label} · 불러온 파일` };
      setSnapshots(prev => [local, ...prev]); chooseSnapshot(local.id);
      setNotice('JSON을 불러왔습니다. 이 화면에서만 미리 보며, 새로고침하면 기본 데이터로 돌아갑니다.');
    } catch (e) { setError(`불러오기 실패: ${e instanceof Error ? e.message : 'JSON 형식을 확인해주세요.'}`); }
    if (input.current) input.current.value = '';
  }
  function exportSnapshot() {
    if (!snapshot) return;
    const blob = new Blob([JSON.stringify(snapshot, null, 2) + '\n'], { type: 'application/json' });
    const url = URL.createObjectURL(blob); const anchor = document.createElement('a');
    anchor.href = url; anchor.download = `${snapshot.id.replace(/[^a-zA-Z0-9-]/g, '-')}.json`; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    setNotice('현재 스냅샷을 JSON으로 내보냈습니다. 저장된 결과를 다시 불러올 수 있습니다.');
  }

  const queryLower = query.trim().toLowerCase();
  const visible = snapshot?.problems.filter(p => (scope === 'all' || p.status !== 'unreleased') && (source === 'all' || p.source === source) && (!queryLower || `${p.id} P${String(p.id).padStart(2, '0')} ${p.name} ${p.source}`.toLowerCase().includes(queryLower))).sort((a, b) => {
    if (sort === 'number') return a.id - b.id;
    const va = valueOf(a, metric), vb = valueOf(b, metric);
    if (va === null) return vb === null ? a.id - b.id : 1;
    if (vb === null) return -1;
    return (sort === 'high' ? vb - va : va - vb) || a.id - b.id;
  }) ?? [];
  const selected = visible.find(p => p.id === selectedId) ?? visible[0] ?? null;

  return <>
    <a href="#main" className="skip-link">본문으로 바로가기</a>
    <header className="site-header"><div className="header-inner"><div className="brand"><Brackets size={29} strokeWidth={3}/><span>LeanArena</span><small>팀 스코어보드</small></div><span className="measurement-status"><i/>로컬 측정</span></div></header>
    <main id="main">
      <div className="page-heading"><div><h1>{snapshot?.dataset === 'warmup' ? '웜업 15문제 · 팀 실험 결과' : '더 짧은 증명, 더 나은 점수.'}</h1><p>팀원이 공유한 후보와 공통 환경에서 재검증한 결과를 확인하세요.</p></div><div className="file-actions"><input ref={input} type="file" accept=".json,application/json" className="sr-only" tabIndex={-1} aria-label="JSON 파일 선택" onChange={e => void importFile(e.target.files?.[0])}/><button className="button import-button" onClick={() => input.current?.click()}><Upload size={16}/>JSON 불러오기</button><button className="button icon-button" onClick={exportSnapshot} disabled={!snapshot} aria-label="현재 스냅샷 JSON 내보내기" title="현재 스냅샷 JSON 내보내기"><Download size={17}/></button></div></div>
      {error ? <div role="alert" className="notification error"><Info size={17}/><span>{error}</span><button aria-label="오류 닫기" onClick={() => setError('')}><X size={16}/></button></div> : null}
      {notice ? <div role="status" className="notification success"><Check size={17}/><span>{notice}</span><button aria-label="알림 닫기" onClick={() => setNotice('')}><X size={16}/></button></div> : null}
      {!snapshot ? <div className="loading-state">{error ? <button className="button" onClick={() => window.location.reload()}>다시 불러오기</button> : loaded ? '아직 등록된 결과가 없습니다.' : '결과를 불러오고 있습니다…'}</div> : <>
        <div className="dataset-bar">{snapshot.dataset === 'warmup' ? <span className="warmup-label">P01–P15 · 팀원 후보 재검증</span> : <><div className="dataset-tabs" role="group" aria-label="문제 보기"><button aria-pressed={scope === 'all'} className={scope === 'all' ? 'active' : ''} onClick={() => setScope('all')}>전체 <span>{snapshot.problems.length}</span></button><button aria-pressed={scope === 'released'} className={scope === 'released' ? 'active' : ''} onClick={() => setScope('released')}>현재 공개 <span>{snapshot.problems.filter(p => p.status !== 'unreleased').length}</span></button></div><span className="release-schedule">{snapshot.problems.some(p => p.status === 'unreleased') ? `${snapshot.problems.filter(p => p.status === 'unreleased').length}문제 · 공개 대기` : '전체 문제 공개'}</span></>}<label className="snapshot-picker"><span>실험 기록</span><select aria-label="실험 기록" value={snapshot.id} onChange={e => chooseSnapshot(e.target.value)}>{snapshots.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}</select></label></div>
        <nav className="section-nav" aria-label="대시보드 섹션"><a href="#results">문제별 점수</a><a href="#team-records">팀원 전체 PR · 30</a><a href="#p09-research">P04·P09 연구</a></nav>
        <div id="results"><SummaryCards snapshot={snapshot}/></div>
        <div className={`workbench ${scope === 'all' && snapshot.problems.length === 50 ? 'competition-layout' : ''}`}>
          <ProblemGrid {...{ snapshot, metric, query, source, sort, visible, selected }} compact={scope === 'all'} onMetric={setMetric} onQuery={setQuery} onSource={setSource} onSort={setSort} onSelect={chooseProblem}/>
          <DetailPanel problem={selected} metric={metric} snapshot={snapshot}/>
        </div>
        <TeamActivity/>
        <ProofResearch/>
        <ScoringGuide warmup={snapshot.dataset === 'warmup'}/>
        <footer><span>LeanArena <span className="dot-separator">/</span> 가짜연구소</span><span>데이터 기준 {new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium', timeZone: 'Asia/Seoul' }).format(new Date(snapshot.measuredAt))} · 저장된 실험 스냅샷</span></footer>
      </>}
    </main>
  </>;
}
