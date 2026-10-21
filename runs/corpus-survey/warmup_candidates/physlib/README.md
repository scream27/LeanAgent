# physlib: warm-up 길이 후보

모집단 7,210개. 200토큰 이상 612개, 상위 5% 361개, 교집합 361개.

상위 5% 경계: 300 토큰. 경계 동률을 모두 포함한다. 기존 warm-up도 전체 목록에는 포함하고 번호로 표시한다.

- [200토큰 이상 전체 증명](ge200.jsonl.gz) · [탐색용 인덱스](ge200.index.jsonl)
- [상위 5% 전체 증명](top5pct.jsonl.gz) · [탐색용 인덱스](top5pct.index.jsonl)
- [교집합 인덱스](intersection.index.jsonl) · [먼저 볼 후보 25개 이하](review_first.jsonl)

## 먼저 볼 후보

기존 warm-up을 제외하고 두 조건을 모두 만족하는 후보를 먼저, 그 안에서는 warm-up 길이와의 로그 비율 차이가 작은 순서다. 같은 출처의 warm-up 길이를 사용하며 LeanPool만 전체 15개의 길이를 참고한다. 수학적 내용·tactic·heartbeat 유사도나 출제 확률 순위가 아니다.

| ID | 정리 | 토큰 | 선택 조건 | 가까운 warm-up 길이 | 원문 |
| --- | --- | ---: | --- | ---: | --- |
| physlib_4568 | `IdealGas.partitionZ_eq` | 1,214 | 둘 다 | 1,217 | [파일](<../../../physlib/context/Physlib/StatisticalMechanics/MicroCanonicalEnsemble/IdealGas.lean>) · 55행 |
| physlib_8877 | `Matrix.spectrum_prod_complex` | 1,222 | 둘 다 | 1,217 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/Matrix.lean>) · 935행 |
| physlib_8958 | `SteinsLemma.GeneralizedQSteinsLemma` | 855 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/ResourceTheory/SteinsLemma.lean>) · 1978행 |
| physlib_5724 | `JensenOperatorInequality.theorem_2_5_2_i_ici_all_imp_v` | 1,208 | 둘 다 | 1,217 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/HayataGroup/TraceInequality/JensenOperatorInequality.lean>) · 310행 |
| physlib_7756 | `QuantumMechanics.SpaceDHilbertSpace.PolyBddSchwartzSubmodule.dense_top` | 1,206 | 둘 다 | 1,217 | [파일](<../../../physlib/context/Physlib/QuantumMechanics/HilbertSpaces/SpaceD/PolyBddSchwartzSubmodule.lean>) · 196행 |
| physlib_5990 | `HermitianMat.spectrum_subset_of_isOpen` | 840 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/HermitianMat/CFC.lean>) · 636행 |
| physlib_7662 | `WickContraction.signFinset_insertAndContract_some` | 840 | 둘 다 | 851 | [파일](<../../../physlib/context/Physlib/QFT/PerturbationTheory/WickContraction/Sign/InsertSome.lean>) · 55행 |
| physlib_6373 | `cauchyBinet` | 1,200 | 둘 다 | 1,217 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/Majorization.lean>) · 149행 |
| physlib_5786 | `LiebAndoTrace.liebExtensionTrace_jointlyConcaveOn_pdSet` | 1,241 | 둘 다 | 1,217 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/HayataGroup/TraceInequality/LiebAndoTrace.lean>) · 1182행 |
| physlib_8864 | `exists_liminf_zero_of_forall_liminf_limsup_le_with_UB` | 1,246 | 둘 다 | 1,217 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/LimSupInf.lean>) · 377행 |
| physlib_8464 | `Space.integrable_fderiv_space` | 874 | 둘 다 | 851 | [파일](<../../../physlib/context/Physlib/SpaceAndTime/TimeAndSpace/ConstantTimeDist.lean>) · 296행 |
| physlib_7868 | `QuantumMechanics.radiusPowLM_apply_memHS` | 876 | 둘 다 | 851 | [파일](<../../../physlib/context/Physlib/QuantumMechanics/Operators/Position.lean>) · 183행 |
| physlib_6742 | `Ket.IsProd_iff_mul_eq_mul` | 878 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/States/Pure/Braket.lean>) · 274행 |
| physlib_6536 | `sion_exists_min_fin` | 824 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/SionMinimax.lean>) · 564행 |
| physlib_7218 | `TwoHiggsDoublet.stabilityCounterExample_not_potentialIsStable` | 822 | 둘 다 | 851 | [파일](<../../../physlib/context/Physlib/Particles/BeyondTheStandardModel/TwoHDM/Potential.lean>) · 446행 |
| physlib_5817 | `LownerHeinzCore.square_convexity_diff_hL` | 819 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/HayataGroup/TraceInequality/LownerHeinzCore.lean>) · 1593행 |
| physlib_5794 | `LownerHeinzCore.one_div_operatorConvexOn_Ioi` | 1,267 | 둘 다 | 1,217 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/HayataGroup/TraceInequality/LownerHeinzCore.lean>) · 330행 |
| physlib_5098 | `TwoHiggsDoublet.EffectivePotential.monomial_mem_adjoin_neutralBilinear` | 1,167 | 둘 다 | 1,217 | [파일](<../../../physlib/context/PhyslibAlpha/Particles/BeyondTheStandardModel/TwoHDM/Invariants.lean>) · 356행 |
| physlib_5991 | `HermitianMat.continuousWithinAt_cfc_of_continuousOn` | 1,167 | 둘 다 | 1,217 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/HermitianMat/CFC.lean>) · 734행 |
| physlib_6394 | `sum_mul_log_nonneg_of_weak_log_maj` | 888 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/Majorization.lean>) · 845행 |
| physlib_8666 | `qRelativeEnt_joint_convexity` | 815 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/Entropy/DPI.lean>) · 1522행 |
| physlib_5782 | `LiebAndoTrace.liebTraceMap_antitone_right` | 892 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/HayataGroup/TraceInequality/LiebAndoTrace.lean>) · 950행 |
| physlib_5781 | `LiebAndoTrace.liebTraceMap_mono_right` | 810 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/HayataGroup/TraceInequality/LiebAndoTrace.lean>) · 879행 |
| physlib_8365 | `Space.IsDistBounded.integrable_time_space` | 810 | 둘 다 | 851 | [파일](<../../../physlib/context/Physlib/SpaceAndTime/Space/IsDistBounded.lean>) · 265행 |
| physlib_5811 | `LownerHeinzCore.convexOn_nnrpow_Ioo_one_add` | 897 | 둘 다 | 851 | [파일](<../../../physlib/context/QuantumInfo/ForMathlib/HayataGroup/TraceInequality/LownerHeinzCore.lean>) · 1427행 |

원문 문맥·버전·검증 상태는 전체 증명 레코드에 유지된다. `context_file`은 `original_corpus_root` 기준 상대경로이며 `context_path_from_repository_root`는 저장소 루트 기준 경로다. 독립 컴파일 가능한 문제 파일이라고 가정하지 않는다.
