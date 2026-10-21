# cslib: warm-up 길이 후보

모집단 1,188개. 200토큰 이상 35개, 상위 5% 60개, 교집합 35개.

상위 5% 경계: 151 토큰. 경계 동률을 모두 포함한다. 기존 warm-up도 전체 목록에는 포함하고 번호로 표시한다.

- [200토큰 이상 전체 증명](ge200.jsonl.gz) · [탐색용 인덱스](ge200.index.jsonl)
- [상위 5% 전체 증명](top5pct.jsonl.gz) · [탐색용 인덱스](top5pct.index.jsonl)
- [교집합 인덱스](intersection.index.jsonl) · [먼저 볼 후보 25개 이하](review_first.jsonl)

## 먼저 볼 후보

기존 warm-up을 제외하고 두 조건을 모두 만족하는 후보를 먼저, 그 안에서는 warm-up 길이와의 로그 비율 차이가 작은 순서다. 같은 출처의 warm-up 길이를 사용하며 LeanPool만 전체 15개의 길이를 참고한다. 수학적 내용·tactic·heartbeat 유사도나 출제 확률 순위가 아니다.

| ID | 정리 | 토큰 | 선택 조건 | 가까운 warm-up 길이 | 원문 |
| --- | --- | ---: | --- | ---: | --- |
| cslib_01317 | `Cslib.LambdaCalculus.LocallyNameless.Untyped.Term.stronglyCommute_eta_beta` | 410 | 둘 다 | 408 | [파일](<../../../cslib/context/Cslib/Languages/LambdaCalculus/LocallyNameless/Untyped/FullBetaEtaConfluence.lean>) · 38행 |
| cslib_01451 | `Cslib.Logic.CLL.Proposition.Proposition.equiv_with₁` | 248 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Logics/LinearLogic/CLL/Basic.lean>) · 537행 |
| cslib_01452 | `Cslib.Logic.CLL.Proposition.Proposition.equiv_with₂` | 248 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Logics/LinearLogic/CLL/Basic.lean>) · 567행 |
| cslib_00897 | `Cslib.LTS.IsBisimulation.traceEq_not_bisim` | 416 | 둘 다 | 408 | [파일](<../../../cslib/context/Cslib/Foundations/Semantics/LTS/Bisimulation.lean>) · 343행 |
| cslib_00091 | `Cslib.Automata.NA.FinAcc.loop_language_eq` | 397 | 둘 다 | 407 | [파일](<../../../cslib/context/Cslib/Computability/Automata/NA/Loop.lean>) · 186행 |
| cslib_01688 | `CslibTests.runEff_eval_correct` | 423 | 둘 다 | 408 | [파일](<../../../cslib/context/CslibTests/FreeMonad.lean>) · 306행 |
| cslib_01203 | `Cslib.LambdaCalculus.LocallyNameless.Fsub.Typing.preservation` | 391 | 둘 다 | 407 | [파일](<../../../cslib/context/Cslib/Languages/LambdaCalculus/LocallyNameless/Fsub/Safety.lean>) · 37행 |
| cslib_00157 | `Cslib.Automata.NA.Buchi.buchiFamily_cover` | 264 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Computability/Languages/Congruences/BuchiCongruence.lean>) · 118행 |
| cslib_01414 | `Cslib.LambdaCalculus.LocallyNameless.Untyped.Term.sn_abs_app_multiApp` | 237 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Languages/LambdaCalculus/LocallyNameless/Untyped/StrongNorm.lean>) · 123행 |
| cslib_01008 | `Cslib.CCS.bisimilarity_congr_par` | 229 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Languages/CCS/BehaviouralTheory.lean>) · 379행 |
| cslib_01000 | `Cslib.CCS.bisimilarity_par_assoc` | 276 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Languages/CCS/BehaviouralTheory.lean>) · 86행 |
| cslib_01210 | `Cslib.LambdaCalculus.LocallyNameless.Fsub.Sub.trans` | 226 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Languages/LambdaCalculus/LocallyNameless/Fsub/Subtype.lean>) · 105행 |
| cslib_00101 | `Cslib.Automata.NA.Buchi.language_eq_fin_iSup_hmul_omegaPow` | 364 | 둘 다 | 407 | [파일](<../../../cslib/context/Cslib/Computability/Automata/NA/Pair.lean>) · 105행 |
| cslib_00123 | `Cslib.FLP.CanReachVia.subset_inp` | 364 | 둘 다 | 407 | [파일](<../../../cslib/context/Cslib/Computability/Distributed/FLP/CanReachVia.lean>) · 101행 |
| cslib_01428 | `Cslib.Logic.HML.theoryEq_isBisimulation` | 222 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Logics/HML/Basic.lean>) · 202행 |
| cslib_00078 | `Cslib.Automata.NA.FinAcc.finConcat_language_eq` | 354 | 둘 다 | 407 | [파일](<../../../cslib/context/Cslib/Computability/Automata/NA/Concat.lean>) · 160행 |
| cslib_01066 | `Cslib.SKI.RedexFree.normal_red` | 217 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Languages/CombinatoryLogic/Evaluation.lean>) · 139행 |
| cslib_00371 | `Cslib.Crypto.Protocols.SecretSharing.Shamir.view_indist_of_tailSampler` | 216 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Crypto/Protocols/SecretSharing/Shamir.lean>) · 216행 |
| cslib_01447 | `Cslib.Logic.CLL.Proposition.Proposition.equiv_parr₁` | 212 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Logics/LinearLogic/CLL/Basic.lean>) · 429행 |
| cslib_01448 | `Cslib.Logic.CLL.Proposition.Proposition.equiv_parr₂` | 212 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Logics/LinearLogic/CLL/Basic.lean>) · 455행 |
| cslib_01082 | `Cslib.SKI.rice` | 301 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Languages/CombinatoryLogic/Evaluation.lean>) · 272행 |
| cslib_01010 | `Cslib.SKI.Polynomial.elimVar_correct` | 209 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Languages/CombinatoryLogic/Basic.lean>) · 91행 |
| cslib_00070 | `Cslib.Automata.NA.Buchi.inter_language_eq` | 207 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Computability/Automata/NA/BuchiInter.lean>) · 100행 |
| cslib_00497 | `Nat.segment_range_val` | 206 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/Foundations/Data/Nat/Segment.lean>) · 153행 |
| cslib_01679 | `Cslib.MachineLearning.PACLearning.ae_mem_versionSpace_of_realizable` | 205 | 둘 다 | 251 | [파일](<../../../cslib/context/Cslib/MachineLearning/PACLearning/VersionSpace.lean>) · 287행 |

원문 문맥·버전·검증 상태는 전체 증명 레코드에 유지된다. `context_file`은 `original_corpus_root` 기준 상대경로이며 `context_path_from_repository_root`는 저장소 루트 기준 경로다. 독립 컴파일 가능한 문제 파일이라고 가정하지 않는다.
