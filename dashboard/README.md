# LeanArena 팀 스코어보드

현재 공개된 15문제를 포함해 총 50문제를 표시하는 React + Vite 대시보드입니다. P16–P50은 2026-11-01 공개 대기 상태이며, 현재 번호는 내부 관리용입니다. 공개 시 공식 ID(정리의 완전한 이름)를 기준으로 기존 15문제와 매칭해야 합니다. 날짜가 지났다고 자동으로 문제를 생성하거나 측정 완료 처리하지 않습니다.

## 실행

Node.js 22.18 이상(개발 환경: 24)을 사용합니다.

```sh
npm ci
npm run dev
```

미리보기 주소는 `http://127.0.0.1:4173/`입니다. `npm run build`로 `dist/`를 만들고 `npm run preview`로 빌드를 확인합니다. 순수 프런트엔드이며 로그인·DB·자동 수집 기능은 포함하지 않습니다.

## 화면과 지표

- 전체 50문제 / 현재 공개된 문제 보기, 문제명·번호 검색, 출처 필터, 점수 정렬.
- 각 타일에 점수·개선율과 **선택 후보의 실제 토큰 길이·heartbeat**를 함께 표시합니다. 지표 탭을 바꿔도 두 실측값은 유지하며, 소수 중앙값과 전체 자릿수를 보존합니다. 원본 비교와 버전별 검증 상태는 상세 패널에서 확인합니다.
- 개선 점수: `(토큰 감소율 + heartbeat 감소율) / 2`. 기존 로컬 평가기의 두 축과 동일한 50:50 비중입니다.
- 대회식 종합: `(토큰 감소율 + heartbeat 감소율 + 호환성) / 3`. 공식 worker에서 산출한 점수가 아닌 로컬 추정입니다.
- 색상은 선택한 탭에 표시된 점수를 기준으로 합니다. 60 이하(60 포함)는 빨간 경고색이며, 60 초과부터 100까지 연한 초록에서 기존 진한 초록(#0c825c)으로 연속 보간합니다. 미측정은 회색입니다. 대회식 종합의 화살표는 원본 대비 변화량(p)을 별도로 표시하고, 음수 점수는 그대로 유지합니다.
- 위 요약 카드의 평균은 **측정된 문제만** 사용하고 분모를 표시합니다. 필터를 바꿔도 전체 스냅샷 요약은 유지합니다.
- 전체 대회식 종합은 50개 상태가 모두 확정될 때만 산출합니다. 미제출·검증 실패는 0점으로 포함하지만, 미공개·미측정·호환성 대기는 0점으로 바꾸지 않습니다. 기준값 0의 감소율은 정의되지 않으므로 산출 대기입니다.

점수 산식은 `LEArN/week3-experiments/corpus/data/arena/56aa7b8f738d1d6a0a24a55e03cdea1a84007b6c/app.py`의 `_scoring_html()`에 보관된 Arena 공개 구현을 근거로 합니다. 이후 공식 규칙 변경 시 함께 검토해야 합니다.

## 실제 데이터

현재 포함된 두 스냅샷은 과거 실험의 보관본입니다. 앱은 포함된 정적 JSON만 읽으며 LEArN 저장소나 로컬 `best.json`을 직접 참조하지 않습니다. 우리 저장소의 제출 후보 구조가 확정되면 기존 15문제를 그 구조에 맞춰 옮기고, 선택 결과를 대시보드 JSON으로 내보내는 단계와 해당 경로의 배포 트리거를 함께 추가합니다.

기본값은 2026-10-16 추가 실험(9개 측정, 6개 측정 대기)입니다. 2026-10-10 전체 검증 실험(15개 측정)을 별도로 선택할 수 있습니다. 서로 다른 실험과 raw/scaled heartbeat를 섞지 않습니다. 10월 10일 기록은 완료일만 알려져 있어 날짜만 표시합니다.

아래 명령은 과거 스냅샷을 재현하는 수동 도구이며 CI에서는 실행하지 않습니다.

```sh
npm run data:sync
# 다른 위치의 원본 사용
python3 scripts/sync_data.py --learn-root /absolute/path/to/LEArN
```

스크립트는 로컬 증거를 읽기만 하며 Lean을 재실행하지 않습니다. 최신 후보의 SHA-256, 두 번 이상의 유효한 검증, 원본과 후보의 환경, 토큰·heartbeat 중앙값, 무효화 목록을 확인합니다. 증명 원문·사용자 홈 경로는 내보내지 않습니다. 원본 변경 후 동기화하고 다시 빌드·배포해야 팀원에게 갱신됩니다.

`public/data/index.json`은 스냅샷 파일 목록이며, 각 파일은 `schemaVersion: 1` 계약을 따릅니다. `src/lib/model.ts`에 타입과 검증기가 있습니다. 50개 문제를 모두 포함해야 하며 `id`는 1–50에서 중복되지 않아야 합니다. 새 문제를 연결할 때 `name`, `source`, `status`, `baseline`, `candidate`, `versions`, `environment`, `candidateHash`, `evidence`를 채웁니다. `measured`는 같은 후보·환경의 유효한 결과일 때만 사용합니다. `versions`의 `pending`을 검증 없이 `pass`로 바꾸면 안 됩니다.

화면의 JSON 내보내기로 양식을 얻고, JSON 불러오기로 새 데이터를 미리 볼 수 있습니다. 불러오기는 현재 브라우저 메모리에만 적용되고 새로고침 시 초기화됩니다. 팀 공용 데이터로 저장하려면 검토한 파일을 `public/data/`에 추가하고 `index.json`에 등록해 다시 배포합니다. 잘못된 JSON은 현재 결과를 교체하지 않습니다.

## Vercel 배포

운영 주소: https://lean-arena-dashboard.vercel.app

현재 CLI로 배포되어 있으며 GitHub 자동 배포는 아직 연결하지 않았습니다. 앱 자체에는 환경 변수나 백엔드가 필요하지 않습니다.

```sh
# 이 dashboard 폴더에서 실행
vercel link --project lean-arena-dashboard --scope jwkweons-projects
vercel deploy --prod
```

현재 CLI 방식의 프로젝트 Root Directory는 `.`입니다. 설정은 `vercel.json`에 있으며, Vite / `npm run build` / `dist`를 사용합니다. Vercel Git 연동을 별도로 도입한다면 저장소 기준 Root Directory는 `dashboard`입니다.

대시보드를 `main`에 병합한 뒤 자동 배포를 별도 PR로 연결할 예정입니다.

- 운영 배포 브랜치: `main`.
- 자동 배포 조건: `dashboard/**` 변경. 현재 게시 데이터인 `dashboard/public/data/*.json`도 포함합니다.
- 우리 제출 후보 구조가 확정되면 선택 결과를 JSON으로 내보내는 단계와 해당 경로의 트리거를 함께 추가합니다.
- LEArN 원본을 감시하거나 CI에서 `data:sync`를 실행하지 않습니다.
- 점수 테스트와 `npm run data:check`를 통과한 산출물만 배포합니다.

자동 배포 연결에는 GitHub 인증의 `workflow` 수정 권한과 Actions secret `VERCEL_TOKEN`이 필요합니다. 토큰은 Vercel 계정의 [Tokens](https://vercel.com/account/tokens)에서 발급하고 저장소의 [Actions secrets](https://github.com/Pseudo-Lab/LeanAgent-LeanRefactorArena/settings/secrets/actions)에 등록합니다. 토큰 값을 코드·문서에 넣지 않습니다.

현재 운영 주소는 공개 접근이 가능합니다. 게시 JSON에 비밀값이나 공개하면 안 되는 원본 증명·기록을 넣지 않습니다.

## 검증

```sh
npm test
npm run data:check
npm run build
```

테스트는 50칸 구성, 35개 미공개 상태, 계산 산식, 음수·0 기준값·미측정·호환성 대기, 실패/미제출 포함 전체 평균, 입력 스키마와 데이터 분리를 검증합니다.
