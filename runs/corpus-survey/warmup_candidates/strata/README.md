# strata: warm-up 길이 후보

모집단 580개. 200토큰 이상 29개, 상위 5% 29개, 교집합 29개.

상위 5% 경계: 202 토큰. 경계 동률을 모두 포함한다. 기존 warm-up도 전체 목록에는 포함하고 번호로 표시한다.

- [200토큰 이상 전체 증명](ge200.jsonl.gz) · [탐색용 인덱스](ge200.index.jsonl)
- [상위 5% 전체 증명](top5pct.jsonl.gz) · [탐색용 인덱스](top5pct.index.jsonl)
- [교집합 인덱스](intersection.index.jsonl) · [먼저 볼 후보 25개 이하](review_first.jsonl)

## 먼저 볼 후보

기존 warm-up을 제외하고 두 조건을 모두 만족하는 후보를 먼저, 그 안에서는 warm-up 길이와의 로그 비율 차이가 작은 순서다. 같은 출처의 warm-up 길이를 사용하며 LeanPool만 전체 15개의 길이를 참고한다. 수학적 내용·tactic·heartbeat 유사도나 출제 확률 순위가 아니다.

| ID | 정리 | 토큰 | 선택 조건 | 가까운 warm-up 길이 | 원문 |
| --- | --- | ---: | --- | ---: | --- |
| strata_0326 | `Core.OldExpressions.normalizeOldExprSound` | 217 | 둘 다 | 222 | [파일](<../../../strata/context/Strata/Languages/Core/OldExpressions.lean>) · 523행 |
| strata_0160 | `Lambda.Constraint.unify_termination_goal_1` | 230 | 둘 다 | 224 | [파일](<../../../strata/context/Strata/DL/Lambda/LTyUnify.lean>) · 855행 |
| strata_0162 | `Lambda.Constraint.unify_termination_goal_3` | 234 | 둘 다 | 224 | [파일](<../../../strata/context/Strata/DL/Lambda/LTyUnify.lean>) · 927행 |
| strata_0187 | `List.length_dedup_of_removeAll` | 298 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/DL/Util/List.lean>) · 192행 |
| strata_0554 | `CallElimCorrect.UpdateStatesUpdatedId` | 211 | 둘 다 | 222 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 1843행 |
| strata_0555 | `CallElimCorrect.InitVarsRemoveAll` | 236 | 둘 다 | 224 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 1903행 |
| strata_0609 | `CallElimCorrect.substOldExprPostSubset` | 331 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 3204행 |
| strata_0130 | `Lambda.LMonoTy.freeVars_of_subst_subset` | 239 | 둘 다 | 224 | [파일](<../../../strata/context/Strata/DL/Lambda/LTyUnify.lean>) · 279행 |
| strata_0314 | `Nat_eq_of_StringGen_suffix` | 338 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/DL/Util/StringGen.lean>) · 237행 |
| strata_0604 | `CallElimCorrect.normalizeOldExprInVars` | 204 | 둘 다 | 222 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 3008행 |
| strata_0311 | `Nat_eq_of_toDigitsCore_eq` | 202 | 둘 다 | 222 | [파일](<../../../strata/context/Strata/DL/Util/StringGen.lean>) · 204행 |
| strata_0188 | `List.length_dedup_append_le_left` | 280 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/DL/Util/List.lean>) · 248행 |
| strata_0551 | `CallElimCorrect.Lambda.LExpr.substFvarsCorrect` | 251 | 둘 다 | 224 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 1510행 |
| strata_0557 | `CallElimCorrect.substOld_create_replace` | 278 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 2021행 |
| strata_0556 | `CallElimCorrect.updatedStateOldWellFormedCoreEvalTwoState` | 272 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 1964행 |
| strata_0537 | `CallElimCorrect.Lambda.LExpr.substFvarsCorrectZero` | 364 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 1220행 |
| strata_0102 | `Lambda.LExpr.varOpen_varClose_when_lcAt` | 265 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/DL/Lambda/LExprWF.lean>) · 185행 |
| strata_0310 | `Nat_toDigitsCore_list_head_eq` | 392 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/DL/Util/StringGen.lean>) · 172행 |
| strata_0325 | `Core.OldExpressions.normalizedOldExprTrueSound` | 406 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Languages/Core/OldExpressions.lean>) · 428행 |
| strata_0483 | `Core.WF.Statement.typeCheckAux_go_WF` | 413 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Languages/Core/StatementWF.lean>) · 58행 |
| strata_0612 | `StmtToNondetCorrect` | 423 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Transform/DetToNondetCorrect.lean>) · 31행 |
| strata_0558 | `CallElimCorrect.substOldExpr_cons` | 430 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 2077행 |
| strata_0536 | `CallElimCorrect.Lambda.LExpr.substFvarCorrect` | 433 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 1120행 |
| strata_0553 | `CallElimCorrect.substOldCorrect` | 442 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Transform/CallElimCorrect.lean>) · 1729행 |
| strata_0345 | `Core.WF.Program.typeCheckFunctionNoDup` | 611 | 둘 다 | 313 | [파일](<../../../strata/context/Strata/Languages/Core/ProgramWF.lean>) · 426행 |

원문 문맥·버전·검증 상태는 전체 증명 레코드에 유지된다. `context_file`은 `original_corpus_root` 기준 상대경로이며 `context_path_from_repository_root`는 저장소 루트 기준 경로다. 독립 컴파일 가능한 문제 파일이라고 가정하지 않는다.
