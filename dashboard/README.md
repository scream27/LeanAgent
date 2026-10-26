# 팀 대시보드

웜업 P01–P15의 팀원 후보와 공통 환경에서 재검증한 결과를 보여줍니다.
공식 제출 성적이 아니며 자료 미확보·환경 준비 실패·검증기 지원 대기·증명 실패를 구분합니다.
일부 버전만 통과한 후보는 대표 환경의 측정값과 미완료 호환성을 구분해 표시합니다.


후보 출처와 검증 상태는 `../submissions/warmup/manifest.json`에 있습니다.
제출 후보·출처·재검증 실행법은 `../submissions/warmup/README.md`에 있습니다.
문제별 대표 표시는 담당자 최종본을 우선하며, 다른 후보도 상세 화면에서 확인할 수 있습니다.
동일한 15개 대표 후보는 `../submissions/warmup/best/`에 보관하며, 제출 준비 묶음의 `manifest.json`에서 파일 해시와 검증 상태를 확인할 수 있습니다.


## 실행

Node.js 24에서 이 폴더를 열고 실행합니다.

```sh
npm ci
npm run dev
```

주소: http://127.0.0.1:4173

## 데이터

결과 JSON은 `public/data/`에 두고 `index.json`에 파일 이름을 적습니다.
파일 형식은 `src/lib/model.ts`에 있습니다. `warmup`은 15문제, `competition`은 50문제를 받습니다.
P10·P11·P13·P14·P15의 웜업 JSON은 `scripts/publish_warmup_verification.py`로 검증 artifact에서 갱신하며 점수를 직접 편집하지 않습니다. 나머지 문제는 기존 측정 결과를 유지합니다. 확인하지 않은 결과는 대기로 표시합니다.
JSON 불러오기는 현재 화면에서만 적용됩니다.

## 팀 PR과 개선 조사

`src/data/team-activity.json`은 2026-10-26에 확인한 모든 상태의 팀 PR 30개와 작성자 7명, 주요 실험 36묶음의 출처 목록입니다. 병합 전 결과는 작성자 보고값으로 표시하며, 점수표의 공통 환경 측정과 합산하지 않습니다. 개별 시도 전체는 원문 기록으로 연결합니다. PR #24의 파일 목록 API는 3,000개 제한이 있어 하위 트리와 보고서도 확인했습니다.

P09의 호환성 보완 근거는 `public/research/p09/experiment.json`에 있습니다. 공개된 후보와 정확히 같은 바이트·해시의 증명 및 원본을 지정된 세 버전·커밋·의존성에서 각각 3회 전체 파일 검증했습니다. 이 근거로 P09의 상태와 호환성만 보완했으며, 기존 v4.32 성능 측정값과 스냅샷 측정일은 유지합니다. `submissions/warmup/`은 이전 제출 준비 시점의 기록이며 이번 호환성 보완이나 새 제출을 반영한 묶음이 아닙니다.

새 76토큰 대안과 기존 79토큰 후보의 성능 비교는 별도의 전체 문맥 측정입니다. 해당 HB를 기존 점수표의 계측값과 섞지 않습니다. 원문 논문과 적용 범위는 화면의 P04·P09 연구에서 확인할 수 있습니다.

## 확인

```sh
npm test
npm run data:check
npm run build
```

## 배포

운영 주소: https://lean-arena-dashboard.pages.dev

Cloudflare Pages의 Direct Upload 프로젝트 `lean-arena-dashboard`를 사용합니다. GitHub Actions 저장소 변수 `DASHBOARD_URL`에도 이 주소를 설정합니다.

`.github/workflows/dashboard-ci.yml`이 main의 `dashboard/**` 또는 해당 워크플로 변경을 처리합니다. PR에서는 테스트·데이터 검사·빌드만 실행하며, main에서는 검사 성공 후 **같은 실행에서 검증한 `dist/` artifact**를 Cloudflare Pages로 배포합니다. Actions의 수동 실행도 main에서만 운영 배포합니다. Cloudflare의 별도 Git 연결이나 팀원별 유료 좌석은 필요하지 않습니다.

### 최초 연결

1. Cloudflare **Workers & Pages → Create application → Pages → Direct Upload**에서 프로젝트를 만들고 운영 브랜치를 `main`으로 설정합니다.
2. 대상 계정으로 범위를 제한한 **Account → Cloudflare Pages → Edit** 권한의 API 토큰을 만듭니다.
3. 이 저장소의 **Settings → Secrets and variables → Actions**에 다음 항목을 등록합니다. 토큰은 코드·문서·채팅에 붙이지 않습니다.

| 종류 | 이름 | 값 |
| --- | --- | --- |
| Secret | `CLOUDFLARE_API_TOKEN` | 대상 계정의 Pages 배포 권한을 가진 API 토큰 |
| Variable | `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 계정 ID |
| Variable | `CLOUDFLARE_PAGES_PROJECT` | 생성한 Pages 프로젝트 이름 |
| Variable | `DASHBOARD_URL` | 해당 프로젝트의 실제 운영 URL (`https://…pages.dev`) |

Wrangler CLI는 `4.152.0`으로 고정합니다. 배포 토큰 `lean-arena-github-actions`의 만료일은 2027-10-26이며, 만료 전에 Secret을 갱신합니다. 필수 설정이 없으면 배포 단계가 명시적인 오류로 중단됩니다.

### 배포 확인과 재실행

`public/_headers`의 보안 헤더와 데이터 재검증 캐시 정책은 Vite 빌드 결과에도 포함됩니다. 배포 후 `npm run deploy:check`가 `DASHBOARD_URL`의 데이터 목록 및 모든 스냅샷 JSON을 해당 커밋과 비교합니다. 이전 데이터가 남아 있으면 배포 작업은 실패합니다.

로컬에서 운영 데이터를 확인하려면 다음과 같이 실제 주소를 지정합니다.

```sh
DASHBOARD_URL=https://lean-arena-dashboard.pages.dev npm run deploy:check
```

재배포는 GitHub Actions의 **Dashboard CI and Production → Run workflow → main**에서 실행합니다. `check` 성공만으로 운영 배포가 끝난 것은 아니며, `deploy`의 데이터 확인까지 성공했는지 확인합니다. PR·다른 브랜치에서 수동 실행하면 검증만 수행합니다.

Cloudflare에서 운영 확인을 마친 후 기존 Vercel 자동 배포용 Secret과 변수를 정리할 수 있습니다. 이전 Vercel 프로젝트는 전환 확인 전까지 복구용으로 유지합니다.
