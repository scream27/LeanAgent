# 수집 데이터

수집 코퍼스는 출처와 commit별로 보관하고, 필요한 문제만 별도 작업 공간에 펼칩니다.
공식 Arena 문제는 `benchmarks/arena/`, 실험 코드와 분석 결과는 각각 `experiments/`, `runs/`에 둡니다.

```text
data/
├── catalog.json                    # 출처별 revision·레코드 수·manifest 해시
├── corpora/<source>/<revision>/
│   ├── manifest.json               # 출처·환경·파일 해시·기존 검증 범위
│   ├── inventory.jsonl.gz          # 원본 레코드 전체
│   ├── subsets/*.jsonl.gz          # 부분집합 ID와 추가/변경 필드
│   ├── context.tar.gz              # 원본 소스 문맥
│   ├── context-index.json          # 레코드가 참조하는 문맥 해시
│   ├── evidence.tar.gz             # 기존 문서·추출 감사·검증 기록
│   ├── environment/                # 고정 toolchain·의존성 명세
│   └── licenses/                   # 수집 당시 포함된 출처 라이선스
├── raw/
│   ├── manifests/                 # 수집 설정과 원출처 목록
│   └── legacy/<migration>/        # 재배치 전 원본 보관본·파일별 해시
└── migrations/<migration>/        # 변경·검증 기록
```

일부 코퍼스에는 `materialization_overrides.jsonl.gz`가 있습니다. 기존 문제별 파일과
inventory 사이의 차이를 그대로 보존하는 자료입니다. 이번 Strata의 615개 차이는 모두
`metadata.json`이며, 증명 내용의 변경이 아닙니다.

## 목록·무결성 확인

저장소 루트에서 Python 3.10 이상으로 실행합니다. 외부 Python 패키지는 필요하지 않습니다.
이 로컬 작업 환경에서는 먼저 공통 환경 설정을 불러옵니다.

```bash
source /Users/jwkweon/00_work/00_project/env/use.sh 05_pseudolab/LeanAgent-LeanRefactorArena
python3 scripts/corpus.py list
python3 scripts/corpus.py verify
```

`verify`는 압축 파일·레코드·문맥의 해시와 기존 문제별 파일의 복원 일치를 검사합니다.
Lean 컴파일, 공리, heartbeat의 재측정은 수행하지 않습니다.
부분집합 이름 `benchmark`는 추출 분류이며 공식 평가 통과를 뜻하지 않습니다.
Strata의 기존 `verified_benchmark` 598개와 `verified_equations` 3개는 별도 부분집합으로 유지합니다.
다른 출처까지 같은 검증이 완료된 것으로 간주하지 않습니다.

## 선택한 문제 펼치기

inventory의 `id`를 지정합니다. 출력은 새 디렉터리여야 하며 기존 경로를 덮어쓰지 않습니다.
다음 `<problem-id>`는 실제 ID로 바꿉니다.

```bash
python3 scripts/corpus.py materialize strata <problem-id> \
  --output "$PROJECT_CACHE_DIR/inputs/strata-trial-001"
python3 scripts/corpus.py export strata --subset verified_benchmark \
  --output "$PROJECT_CACHE_DIR/verified-strata.jsonl"
```

`materialize` 결과에는 선택한 문제의 `reference.lean`, `statement.lean`, `proof.lean`,
`metadata.json`, 그 문제가 속한 **원본 소스 파일 전체**, 환경 명세, 라이선스와
`selection.json`이 들어갑니다. `selection.json`은 입력 파일과 해시를 기록합니다.
원본 소스 파일에는 같은 파일의 다른 선언도 포함될 수 있으므로 실제 실행의 허용 문맥 정책을
별도로 적용해야 합니다. 의존성 전체를 설치하거나 OS 격리를 구성하는 기능은 아닙니다.
기존 개선 후보와 실행 로그는 복사하지 않습니다.

`export`는 inventory에 부분집합의 추가/변경 필드를 합친 JSONL을 만듭니다.
원래 부분집합 파일의 필드 배치·공백까지 필요한 경우 raw 보관본을 사용합니다.
`problem_dir` 등 레코드 안의 경로는 수집 당시의 논리 경로이며 현재 저장소의 실재 경로가 아닙니다.

## 과거 실험 코드

기존 수집·분석 및 Refactor90 코드는 첫 재구조화 커밋 `13e4072`에 보존한 뒤
현재 `experiments/`에서 제거했습니다. 해당 코드 전용 `legacy` 실행 명령도 제거했습니다.
과거 코드와 당시 실행 절차는 다음과 같이 확인할 수 있습니다.

```bash
git ls-tree -r --name-only 13e4072 -- experiments
git show 13e4072:data/README.md
```

과거 실행을 재현해야 한다면 해당 커밋의 코드·문서와 로컬 raw 보관본을 함께 사용합니다.
`runs/corpus-survey/`는 과거 결과이며 새 실행으로 덮어쓰지 않습니다.
Refactor90 결과는 현재 작업 트리에서 제거했습니다.
복원한 과거 작업 공간에는 전체 코퍼스와 개선 후보가 있으므로 에이전트 입력으로 제공하지 않습니다.

## 원본 보존과 공유

`data/raw/legacy/2026-10-21-layout-v1/`의 7개 tar.gz는 재배치 전 코퍼스,
스크립트, 결과, 수집 자료를 보존합니다. 각 archive에는 파일별 SHA-256 목록이 있으며
`catalog.json`에 archive와 목록의 해시를 고정했습니다. 과거 문서·결과 안의 경로와 검증 주장은
당시 상태 그대로입니다. 복원된 작업 공간에서 그 경로를 해석합니다.

압축 데이터·원본 보관본·대형 결과는 Git에서 제외합니다. Git에는 코드·설명·catalog·manifest와
환경 명세를 관리합니다. **Git clone만으로 데이터가 준비되지는 않습니다.** 현재 자료는 이 로컬
작업 공간에 있으며 외부 저장소에 업로드하지 않았습니다. 다른 팀원에게 전달할 때는 `catalog.json`이
가리키는 corpus bundle과 legacy archive를 같은 상대 경로로 함께 복사한 뒤 `verify`를 실행합니다.
외부 배포 위치와 자동 다운로드 방식은 PR 통합 후 별도로 확정합니다.

`sources/`의 원출처 Git checkout은 기존 Lean 환경과 경로 연결을 유지하기 위해 로컬에 남깁니다.
이는 Git 관리 대상이나 에이전트 기본 입력이 아닙니다. 원본 코퍼스와 실행 결과는 캐시가 아니며,
중앙 캐시에는 원본 보관본에서 다시 만들 수 있는 복원 작업 공간과 빌드 결과만 둡니다.
