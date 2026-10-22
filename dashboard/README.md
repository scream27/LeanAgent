# 팀 대시보드

우리 팀이 선택한 제출 후보와 검증 결과를 보여줍니다.
현재 등록된 결과는 없습니다. 후보 저장 구조가 정해지면 15문제의 결과를 연결합니다.

## 실행

Node.js 24에서 이 폴더를 열고 실행합니다.

```sh
npm ci
npm run dev
```

주소: http://127.0.0.1:4173

## 데이터

결과 JSON은 `public/data/`에 두고 `index.json`에 파일 이름을 적습니다.
파일 형식은 `src/lib/model.ts`에 있습니다. 확인하지 않은 결과는 대기로 표시합니다.
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
