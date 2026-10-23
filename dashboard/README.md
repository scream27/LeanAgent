# 팀 대시보드

웜업 P01–P15의 팀원 후보와 공통 환경에서 재검증한 결과를 보여줍니다.
공식 제출 성적이 아니며 자료 미확보·환경 준비 실패·검증기 지원 대기·증명 실패를 구분합니다.
일부 버전만 통과한 후보는 대표 환경의 측정값과 미완료 호환성을 구분해 표시합니다.


후보 출처와 검증 상태는 `../submissions/warmup/manifest.json`에 있습니다.
원본·출처·실행법은 `../experiments/warmup-team-results/README.md`에 있습니다.
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
웜업 JSON은 `experiments/warmup-team-results/export.py`로 생성하며 점수를 직접 편집하지 않습니다. 확인하지 않은 결과는 대기로 표시합니다.
JSON 불러오기는 현재 화면에서만 적용됩니다.

## 확인

```sh
npm test
npm run data:check
npm run build
```

## 배포

운영 주소: https://lean-arena-dashboard.vercel.app
자동 배포는 아직 연결하지 않았습니다.
대시보드나 확정된 선택 후보가 바뀔 때만 배포하도록 연결할 예정입니다.
