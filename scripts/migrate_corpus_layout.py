#!/usr/bin/env python3
"""One-time, lossless migration of the collected Arena corpus (no Lean execution)."""
from __future__ import annotations
import argparse, base64, gzip, hashlib, json, os, shutil, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('strata', 'physlib', 'cslib', 'arklib', 'putnambench', 'leanpool')
SUBSETS = ('benchmark', 'equations', 'structures', 'excluded', 'verified_benchmark', 'verified_equations', 'axiom_excluded')
STAMP = '2026-10-21-layout-v1'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def rows(path):
    with (gzip.open(path, 'rt', encoding='utf-8') if path.suffix == '.gz' else path.open(encoding='utf-8')) as f:
        for line in f:
            if line.strip(): yield json.loads(line)


def archive(root, names, target):
    """Archive regular files and verify every original byte before reporting success."""
    target.parent.mkdir(parents=True, exist_ok=True)
    ledger = {}
    for name in names:
        p = root / name
        paths = sorted(p.rglob('*')) if p.is_dir() else [p]
        for q in paths:
            if q.is_symlink(): raise ValueError(f'Unexpected symlink in archival input: {q}')
            if q.is_file(): ledger[q.relative_to(root).as_posix()] = {'sha256': digest(q), 'bytes': q.stat().st_size}
    pending = target.with_suffix(target.suffix + '.partial')
    with tarfile.open(pending, 'w:gz', compresslevel=3) as tar:
        for name in ledger: tar.add(root / name, arcname=name, recursive=False)
    checked = set()
    with tarfile.open(pending, 'r|gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in ledger
            h = hashlib.sha256()
            with tar.extractfile(member) as stream:
                for b in iter(lambda: stream.read(1024 * 1024), b''): h.update(b)
            assert h.hexdigest() == ledger[member.name]['sha256'], member.name
            checked.add(member.name)
    assert checked == set(ledger)
    pending.replace(target)
    checksum_file = target.with_name(target.name + '.files.json.gz')
    with gzip.open(checksum_file, 'wt', encoding='utf-8') as f: json.dump(ledger, f, ensure_ascii=False)
    return {'path': str(target.relative_to(ROOT)), 'sha256': digest(target), 'files': len(ledger),
            'original_bytes': sum(v['bytes'] for v in ledger.values()),
            'file_ledger': str(checksum_file.relative_to(ROOT)), 'file_ledger_sha256': digest(checksum_file)}


def convert(source, backups):
    old = ROOT / source
    original_manifest = json.loads((old / 'manifest.json').read_text())
    rev = original_manifest['revision']
    out = ROOT / 'data/corpora' / source / rev
    out.mkdir(parents=True, exist_ok=False)
    inventory = old / ('inventory.jsonl.gz' if (old / 'inventory.jsonl.gz').exists() else 'inventory.jsonl')
    compressed = out / 'inventory.jsonl.gz'
    if inventory.suffix == '.gz': shutil.copy2(inventory, compressed)
    else:
        with inventory.open('rb') as inp, compressed.open('wb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0, compresslevel=6) as dst:
                shutil.copyfileobj(inp, dst)
    with gzip.open(compressed, 'rb') as f:
        h = hashlib.sha256()
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    plain_sha = h.hexdigest()
    if inventory.suffix != '.gz': assert plain_sha == digest(inventory)
    lookup = {} if source != 'leanpool' else None
    known_ids = set(); context_hashes = {}; overrides = []; problem_files = 0
    for row in rows(compressed):
        ident = row['id']; assert ident not in known_ids; known_ids.add(ident)
        if lookup is not None: lookup[ident] = row
        for field in ['src', 'proof']:
            assert hashlib.sha256(row[field].encode()).hexdigest() == row[field+'_sha256'], (source, ident, field)
        ctx = row['context_file']
        assert ctx.startswith('context/') and '..' not in Path(ctx).parts
        if ctx not in context_hashes:
            context_hashes[ctx] = digest(old / ctx)
        assert context_hashes[ctx] == row['file_sha256'], (source, ident)
        directory = old / row['problem_dir']
        if directory.exists():
            expected = {'reference.lean': row['src'].encode(), 'statement.lean': row['statement'].encode(), 'proof.lean': row['proof'].encode(),
                        'metadata.json': (json.dumps({k:v for k,v in row.items() if k not in {'src','statement','proof'}},ensure_ascii=False,indent=2)+'\n').encode()}
            for path in directory.iterdir():
                assert path.name in expected and path.is_file(), path
                actual = path.read_bytes(); problem_files += 1
                if actual != expected[path.name]:
                    # Preserve historical materializations exactly, including stale metadata.
                    overrides.append({'id':ident,'file':path.name,'bytes_b64':base64.b64encode(actual).decode(),
                                      'sha256':hashlib.sha256(actual).hexdigest()})
    assert len(known_ids) == original_manifest['total_declarations']
    print(f'{source}: {len(known_ids)} records, {problem_files} expanded files checked; {len(overrides)} exact-byte overrides', flush=True)
    if overrides:
        with gzip.open(out/'materialization_overrides.jsonl.gz','wt',encoding='utf-8') as f:
            for row in overrides: f.write(json.dumps(row,ensure_ascii=False)+'\n')
    subsets = {}
    for name in SUBSETS:
        p = old / (name+'.jsonl')
        if not p.exists(): continue
        target = out/'subsets'/(name+'.jsonl.gz');target.parent.mkdir(exist_ok=True)
        count=0
        with gzip.open(target,'wt',encoding='utf-8') as f:
            for row in rows(p):
                ident=row['id'];assert ident in known_ids
                if lookup is not None:
                    base=lookup[ident]
                    annotation={k:v for k,v in row.items() if k!='id' and (k not in base or v!=base[k])}
                else: annotation={k:v for k,v in row.items() if k not in {'id','inventory_line','row_reference'}}
                item={'id':ident}
                if annotation:item['annotations']=annotation
                f.write(json.dumps(item,ensure_ascii=False)+'\n');count+=1
        subsets[name]={'path':str(target.relative_to(out)),'count':count,'sha256':digest(target),
                       'original_sha256':digest(p),'semantics':'inventory row plus annotations; original bytes in legacy archive'}
    context = archive(old, ['context'], out/'context.tar.gz')
    remaining=[p.name for p in old.iterdir() if p.name not in {'problems','context',inventory.name,'environment'} and p.name not in {s+'.jsonl' for s in SUBSETS} and not p.name.startswith(('LICENSE','NOTICE'))]
    evidence = archive(old,remaining,out/'evidence.tar.gz')
    for name in ['environment']:
        if (old/name).exists():shutil.copytree(old/name,out/name)
    for p in old.iterdir():
        if p.name.startswith(('LICENSE','NOTICE')):
            (out/'licenses').mkdir(exist_ok=True);shutil.copy2(p,out/'licenses'/p.name)
    dump(out/'context-index.json',context_hashes)
    manifest={'schema_version':1,'source':source,'revision':rev,'toolchain':original_manifest['toolchain'],
              'url':original_manifest.get('url',original_manifest.get('source')),'records':len(known_ids),
              'inventory':{'path':'inventory.jsonl.gz','sha256':digest(compressed),'uncompressed_sha256':plain_sha},
              'subsets':subsets,'context':context,'evidence':evidence,'legacy':backups[source],
              'original_manifest':original_manifest,'verified_expanded_files':problem_files,'materialization_overrides':len(overrides),
              'verification_scope':'Storage hashes and lossless record migration only. Existing Lean validation remains unchanged.',
              'artifact_hashes':{p.relative_to(out).as_posix():digest(p) for p in sorted(out.rglob('*')) if p.is_file()}}
    dump(out/'manifest.json',manifest)
    (out/'README.md').write_text(f'# {source} corpus\n\nRevision: `{rev}` · {len(known_ids):,} records.\n\n'
        '전체 레코드는 `inventory.jsonl.gz`, 부분집합은 `subsets/`의 ID와 차이 필드로 관리합니다.\n'
        '`context.tar.gz`는 원본 문맥, `evidence.tar.gz`는 변경하지 않은 과거 문서·검증 근거입니다.\n'
        '과거 문서의 경로는 당시 기준이며 현재 사용법은 저장소의 `data/README.md`를 따릅니다.\n'
        '보관 형식 변경은 Lean 컴파일·공리·heartbeat의 추가 검증을 뜻하지 않습니다.\n')
    return {'path':str(out.relative_to(ROOT)),'revision':rev,'records':len(known_ids),'manifest_sha256':digest(out/'manifest.json'),
            'subsets':{k:v['count'] for k,v in subsets.items()}}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    if not args.apply: ap.error('Use --apply after reviewing the migration; originals are retained until verification.')
    report_path=ROOT/'data/migrations'/STAMP/'report.json'
    if report_path.exists():raise SystemExit('Migration already has a report; inspect it before retrying.')
    raw=ROOT/'data/raw/legacy'/STAMP
    backups={}
    for source in SOURCES:
        print('Archiving and verifying',source,flush=True)
        backups[source]=archive(ROOT,[source],raw/(source+'.tar.gz'))
        dump(raw/'backups.json',backups)
    extra=['scripts','tests','refactor90','results','artifacts','data/arena','data/arena_snapshot.json','data/remaining_sources.json','data/proof_length_reference','.gitignore']
    extra=[x for x in extra if (ROOT/x).exists()]
    backups['workspace']=archive(ROOT,extra,raw/'workspace.tar.gz')
    dump(raw/'backups.json',backups)
    catalog={'schema_version':1,'migration':STAMP,'corpora':{},'legacy_archives':backups}
    for source in SOURCES:
        catalog['corpora'][source]=convert(source,backups)
        dump(ROOT/'data/catalog.json',catalog)
    dump(report_path,{'state':'converted_originals_retained','catalog_sha256':digest(ROOT/'data/catalog.json'),
                      'backups':backups,'corpora':catalog['corpora']})
    print('Conversion complete. Original folders retained pending independent verification.',flush=True)

if __name__=='__main__':main()
