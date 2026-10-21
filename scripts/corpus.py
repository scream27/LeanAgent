#!/usr/bin/env python3
"""Read, verify and materialize versioned corpus bundles without running Lean."""
from __future__ import annotations
import argparse, base64, gzip, hashlib, json, re, shutil, tarfile, tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def read_rows(path):
    with (gzip.open(path,'rt',encoding='utf-8') if path.suffix=='.gz' else path.open(encoding='utf-8')) as f:
        for line in f:
            if line.strip():yield json.loads(line)


def safe_relative(value):
    p=PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or not p.parts or '\\' in value:
        raise ValueError(f'Unsafe relative path: {value}')
    return p


def resolve(root,value):
    safe_relative(value)
    target=(root/value).resolve()
    if not target.is_relative_to(root.resolve()):raise ValueError(f'Path escapes root: {value}')
    return target


def load(source, root=ROOT):
    catalog=json.loads((root/'data/catalog.json').read_text())
    entry=catalog['corpora'][source]
    folder=resolve(root,entry['path'])
    if sha(folder/'manifest.json')!=entry['manifest_sha256']:raise ValueError('Manifest hash mismatch')
    return folder,json.loads((folder/'manifest.json').read_text())


def expected_files(row):
    return {'reference.lean':row['src'].encode(),'statement.lean':row['statement'].encode(),'proof.lean':row['proof'].encode(),
            'metadata.json':(json.dumps({k:v for k,v in row.items() if k not in {'src','statement','proof'}},ensure_ascii=False,indent=2)+'\n').encode()}


def overrides(folder,manifest):
    path=folder/'materialization_overrides.jsonl.gz'
    if not path.exists():return {}
    if sha(path)!=manifest['artifact_hashes'][path.name]:raise ValueError('Override hash mismatch')
    out={}
    for row in read_rows(path):
        b=base64.b64decode(row['bytes_b64'],validate=True)
        if hashlib.sha256(b).hexdigest()!=row['sha256']:raise ValueError('Override content hash mismatch')
        if row['file'] not in {'reference.lean','statement.lean','proof.lean','metadata.json'}:raise ValueError('Unexpected override')
        out.setdefault(row['id'],{})[row['file']]=b
    return out


def selected_rows(folder,manifest,ids,subset=None):
    wanted=set(ids)
    if len(wanted)!=len(ids):raise ValueError('Duplicate requested IDs')
    annotations={}
    if subset:
        info=manifest['subsets'][subset]
        p=resolve(folder,info['path'])
        if sha(p)!=info['sha256']:raise ValueError('Subset hash mismatch')
        annotations={r['id']:r.get('annotations',{}) for r in read_rows(p)}
        if wanted and not wanted.issubset(annotations):raise ValueError('Requested ID is not in the selected subset')
        if not wanted:wanted=set(annotations)
    if not wanted:
        if subset:return
        raise ValueError('Select at least one ID or a subset')
    path=resolve(folder,manifest['inventory']['path'])
    if sha(path)!=manifest['inventory']['sha256']:raise ValueError('Inventory hash mismatch')
    found=set()
    for row in read_rows(path):
        if row['id'] not in wanted:continue
        if row['id'] in found:raise ValueError('Duplicate inventory ID')
        for key in ['src','proof']:
            if hashlib.sha256(row[key].encode()).hexdigest()!=row[key+'_sha256']:raise ValueError('Record hash mismatch')
        found.add(row['id'])
        yield row,annotations.get(row['id'],{})
    missing=wanted-found
    if missing:raise ValueError('Unknown IDs: '+', '.join(sorted(missing)[:10]))


def materialize(source,ids,output,root=ROOT):
    """Create an input-only bundle in a new directory, atomically. No existing results."""
    output=Path(output).absolute()
    if output.exists() or output.is_symlink():raise FileExistsError(f'Output must be new: {output}')
    # Do not accidentally place generated problems inside the canonical store.
    if output.resolve().is_relative_to((root/'data').resolve()):raise ValueError('Do not materialize inside data/')
    folder,manifest=load(source,root)
    records=list(selected_rows(folder,manifest,ids))
    original_overrides=overrides(folder,manifest)
    context_file=folder/'context.tar.gz'
    if sha(context_file)!=manifest['context']['sha256']:raise ValueError('Context archive hash mismatch')
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix='.corpus-',dir=output.parent))
    try:
        needed={r['context_file']:r['file_sha256'] for r,_ in records}
        with tarfile.open(context_file,'r:gz') as tar:
            seen=set()
            for m in tar:
                if m.name not in needed:continue
                if not m.isfile() or m.name in seen:raise ValueError('Invalid context archive member')
                target=resolve(temp,m.name);target.parent.mkdir(parents=True,exist_ok=True)
                with tar.extractfile(m) as inp,target.open('wb') as dst:shutil.copyfileobj(inp,dst)
                if sha(target)!=needed[m.name]:raise ValueError('Context content mismatch')
                seen.add(m.name)
        if seen!=set(needed):raise ValueError('Missing context files')
        for row,_ in records:
            if not re.fullmatch(r'[A-Za-z0-9_-]+',row['id']):raise ValueError('Unsafe ID')
            p=temp/'problems'/row['id'];p.mkdir(parents=True)
            for name,content in (expected_files(row)|original_overrides.get(row['id'],{})).items():(p/name).write_bytes(content)
        for group in ['environment', 'licenses']:
            for rel, digest in manifest['artifact_hashes'].items():
                if not rel.startswith(group + '/'):
                    continue
                source_file = resolve(folder, rel)
                if sha(source_file) != digest:
                    raise ValueError(f'{group} hash mismatch')
                target = resolve(temp, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target)
        info={'source':source,'revision':manifest['revision'],'ids':ids,'manifest_sha256':sha(folder/'manifest.json'),
              'scope':'Original problem inputs and source context only. Not an OS sandbox or a standalone Lean installation.',
              'files':{p.relative_to(temp).as_posix():sha(p) for p in sorted(temp.rglob('*')) if p.is_file()}}
        (temp/'selection.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
        if output.exists() or output.is_symlink():raise FileExistsError(output)
        temp.rename(output)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return info


def verify(source,root=ROOT):
    folder,m=load(source,root)
    for relative,expected in m['artifact_hashes'].items():
        if sha(resolve(folder,relative))!=expected:raise ValueError(f'Artifact mismatch: {source}/{relative}')
    inventory=folder/m['inventory']['path'];h=hashlib.sha256()
    with gzip.open(inventory,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    if h.hexdigest()!=m['inventory']['uncompressed_sha256']:raise ValueError('Decoded inventory mismatch')
    old=m['legacy'];ledger_path=resolve(root,old['file_ledger'])
    if sha(ledger_path)!=old['file_ledger_sha256']:raise ValueError('Legacy ledger mismatch')
    with gzip.open(ledger_path,'rt',encoding='utf-8') as f:ledger=json.load(f)
    altered=overrides(folder,m);ids=set();count=0;ctx=json.loads((folder/'context-index.json').read_text())
    for row in read_rows(inventory):
        if row['id'] in ids:raise ValueError('Duplicate ID')
        ids.add(row['id'])
        for key in ['src','proof']:
            if hashlib.sha256(row[key].encode()).hexdigest()!=row[key+'_sha256']:raise ValueError('Proof/source mismatch')
        if ctx[row['context_file']]!=row['file_sha256']:raise ValueError('Context index mismatch')
        for name,data in (expected_files(row)|altered.get(row['id'],{})).items():
            previous=f"{source}/{row['problem_dir']}/{name}"
            if previous in ledger:
                if hashlib.sha256(data).hexdigest()!=ledger[previous]['sha256']:raise ValueError(f'Materialization mismatch: {previous}')
                count+=1
    if len(ids)!=m['records'] or count!=m['verified_expanded_files']:raise ValueError('Count mismatch')
    with tarfile.open(folder/'context.tar.gz','r|gz') as tar:
        seen=set()
        for member in tar:
            if not member.isfile():raise ValueError('Unexpected context member')
            if member.name not in ctx:continue
            with tar.extractfile(member) as f:
                h=hashlib.sha256()
                for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
            if h.hexdigest()!=ctx[member.name]:raise ValueError('Context bytes mismatch')
            seen.add(member.name)
        if seen!=set(ctx):raise ValueError('Context missing')
    for name,info in m['subsets'].items():
        items=list(read_rows(folder/info['path']))
        if len(items)!=info['count'] or any(r['id'] not in ids for r in items):raise ValueError('Subset references invalid')
        if len({r['id'] for r in items})!=len(items):raise ValueError('Duplicate subset ID')
    return {'source':source,'records':len(ids),'historical_problem_files_reproduced':count,'status':'passed'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    p=sub.add_parser('verify');p.add_argument('sources',nargs='*')
    p=sub.add_parser('materialize');p.add_argument('source');p.add_argument('ids',nargs='+');p.add_argument('--output',required=True,type=Path)
    p=sub.add_parser('export');p.add_argument('source');p.add_argument('--subset',required=True);p.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    try:
        if args.command=='list':print(json.dumps(json.loads((ROOT/'data/catalog.json').read_text())['corpora'],ensure_ascii=False,indent=2))
        elif args.command=='verify':
            names=args.sources or json.loads((ROOT/'data/catalog.json').read_text())['corpora']
            for source in names:print(json.dumps(verify(source),ensure_ascii=False),flush=True)
        elif args.command=='materialize':
            result=materialize(args.source,args.ids,args.output);print(json.dumps({'output':str(args.output),'source':args.source,'ids':result['ids']},ensure_ascii=False))
        elif args.command=='export':
            folder,m=load(args.source)
            if args.output.exists():raise FileExistsError(args.output)
            if args.output.resolve().is_relative_to((ROOT/'data').resolve()):raise ValueError('Output must be outside data/')
            args.output.parent.mkdir(parents=True,exist_ok=True)
            pending=args.output.with_name(args.output.name+'.partial')
            if pending.exists():raise FileExistsError(pending)
            try:
                with pending.open('x',encoding='utf-8') as f:
                    for row,annotation in selected_rows(folder,m,[],args.subset):f.write(json.dumps(row|annotation,ensure_ascii=False)+'\n')
                pending.rename(args.output)
            finally:
                if pending.exists():pending.unlink()
            print(args.output)
    except (ValueError,KeyError,OSError) as e:ap.exit(1,f'Error: {e}\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
