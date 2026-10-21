# leanpool: warm-up 길이 후보

모집단 312,108개. 200토큰 이상 47,484개, 상위 5% 15,611개, 교집합 15,611개.

상위 5% 경계: 505 토큰. 경계 동률을 모두 포함한다. 기존 warm-up도 전체 목록에는 포함하고 번호로 표시한다.

- [200토큰 이상 전체 증명](ge200.jsonl.gz) · [탐색용 인덱스](ge200.index.jsonl)
- [상위 5% 전체 증명](top5pct.jsonl.gz) · [탐색용 인덱스](top5pct.index.jsonl)
- [교집합 인덱스](intersection.index.jsonl) · [먼저 볼 후보 25개 이하](review_first.jsonl)

## 먼저 볼 후보

기존 warm-up을 제외하고 두 조건을 모두 만족하는 후보를 먼저, 그 안에서는 warm-up 길이와의 로그 비율 차이가 작은 순서다. 같은 출처의 warm-up 길이를 사용하며 LeanPool만 전체 15개의 길이를 참고한다. 수학적 내용·tactic·heartbeat 유사도나 출제 확률 순위가 아니다.

| ID | 정리 | 토큰 | 선택 조건 | 가까운 warm-up 길이 | 원문 |
| --- | --- | ---: | --- | ---: | --- |
| leanpool_321204 | `RS.chainMul2_assoc_left` | 1,906 | 둘 다 | 1,906 | [파일](<../../../leanpool/context/LeanPool/RegtsSevenster/RS/Classical/Deligne/ChainStage2.lean>) · 578행 |
| leanpool_46151 | `CKN.Leray.exists_rieszPressure_component_memLp_bound_of_compact` | 1,906 | 둘 다 | 1,906 | [파일](<../../../leanpool/context/LeanPool/CaffarelliKohnNirenberg/Leray/RieszPressureSpaceTime.lean>) · 131행 |
| leanpool_54535 | `LeanEval.Topology.ClassificationOfSurfaces.Moise.LocallyFiniteTriangleComplex.dist_completePath_comparison_lt` | 1,906 | 둘 다 | 1,906 | [파일](<../../../leanpool/context/LeanPool/ClassificationOfSurfaces/Moise/FacewiseComparison.lean>) · 1016행 |
| leanpool_305072 | `weak_PFR_asymm_prelim` | 1,769 | 둘 다 | 1,769 | [파일](<../../../leanpool/context/LeanPool/PFR/WeakPFR.lean>) · 660행 |
| leanpool_306434 | `V7.belowTerminalGradient` | 1,754 | 둘 다 | 1,754 | [파일](<../../../leanpool/context/LeanPool/ParameterFreeGradient/V7/Proofs/Stage3BelowTwo/Dual.lean>) · 675행 |
| leanpool_33735 | `Utilities.Certificate.PseudocorePresentation.exists_merge` | 1,754 | 둘 다 | 1,754 | [파일](<../../../leanpool/context/LeanPool/BrillNoetherGraphs/Utilities/Pseudocore/PseudocorePresentation.lean>) · 289행 |
| leanpool_40587 | `CKN.Core.HeatPotential.prop_heat_morrey_hoelder` | 1,754 | 둘 다 | 1,754 | [파일](<../../../leanpool/context/LeanPool/CaffarelliKohnNirenberg/Core/HeatPotential/SubordinatedCampanato.lean>) · 344행 |
| leanpool_127491 | `LeanPool.Erdos81PaperIContrib.covering_packing_duality` | 1,463 | 둘 다 | 1,463 | [파일](<../../../leanpool/context/LeanPool/Erdos81PaperIContrib/FarkasLP.lean>) · 131행 |
| leanpool_33762 | `Utilities.Certificate.PseudocorePresentation.pseudocorePresentation_of_markedShapeAt` | 1,463 | 둘 다 | 1,463 | [파일](<../../../leanpool/context/LeanPool/BrillNoetherGraphs/Utilities/Pseudocore/PseudocorePresentation.lean>) · 1293행 |
| leanpool_42877 | `CKN.Foundation.Heat.rho_inv_six_integral_le` | 1,463 | 둘 다 | 1,463 | [파일](<../../../leanpool/context/LeanPool/CaffarelliKohnNirenberg/Foundation/Heat/Subordination.lean>) · 101행 |
| leanpool_07168 | `AVenhance.Infra.Section5.Contracts.tMaterial_of_thetaProfile_contract` | 1,372 | 둘 다 | 1,372 | [파일](<../../../leanpool/context/LeanPool/AnomalousDiffusion/AVenhance/Infra/Section5/Contracts/TMaterialFamily.lean>) · 27행 |
| leanpool_21226 | `Complexity.RAM.TMConfig.Sparse.marshalLoopOps_data_internal` | 1,372 | 둘 다 | 1,372 | [파일](<../../../leanpool/context/LeanPool/BeyondBethe/Complexitylib/Models/RandomAccessMachine/Simulation/TMConfig/Sparse/ABI/Internal/Loop.lean>) · 325행 |
| leanpool_202257 | `JordanCurve.step_A_case_high` | 1,353 | 둘 다 | 1,353 | [파일](<../../../leanpool/context/LeanPool/MovingSofa/Development/Geometry/Foundations/Development003.lean>) · 2979행 |
| leanpool_31493 | `AtanasovRanganathan.GenusFiveRow08ChamberTwo.rowDivisor_reaches_coreVertex` | 1,353 | 둘 다 | 1,353 | [파일](<../../../leanpool/context/LeanPool/BrillNoetherGraphs/LowGenus/GenusFiveRow08ChamberTwo.lean>) · 1200행 |
| leanpool_323143 | `RS.powSplit_cond_left` | 1,353 | 둘 다 | 1,353 | [파일](<../../../leanpool/context/LeanPool/RegtsSevenster/RS/Classical/Deligne/PowMerge.lean>) · 916행 |
| leanpool_324802 | `RS.braid_coord_odd` | 1,353 | 둘 다 | 1,353 | [파일](<../../../leanpool/context/LeanPool/RegtsSevenster/RS/Classical/Super/ColourConjTop.lean>) · 1579행 |
| leanpool_325638 | `RS.masterSummand_colouringOfFlip` | 1,353 | 둘 다 | 1,353 | [파일](<../../../leanpool/context/LeanPool/RegtsSevenster/RS/Novel/Coordinates/ReindexHeart.lean>) · 39행 |
| leanpool_40107 | `CKN.caccioppoli_I1_heat_cutoff_annulus_pointwise` | 1,353 | 둘 다 | 1,353 | [파일](<../../../leanpool/context/LeanPool/CaffarelliKohnNirenberg/Core/Caccioppoli/I1.lean>) · 452행 |
| leanpool_46930 | `CKN.pressure_residual_growth_hHbound_4` | 1,353 | 둘 다 | 1,353 | [파일](<../../../leanpool/context/LeanPool/CaffarelliKohnNirenberg/Pressure/IdentificationExtensionGrowthSWS.lean>) · 305행 |
| leanpool_75116 | `ConwaySoifer.Simplified.Certificates.Aown160000170000.excluded44_2` | 1,353 | 둘 다 | 1,353 | [파일](<../../../leanpool/context/LeanPool/ConwaySoifer/Simplified/Certificates/Steps/Aown1600001700005.lean>) · 954행 |
| leanpool_09243 | `AVenhance.Infra.Section5.chiTilde_material_transport_component` | 1,217 | 둘 다 | 1,217 | [파일](<../../../leanpool/context/LeanPool/AnomalousDiffusion/AVenhance/Infra/Section5/TransportIdentities.lean>) · 70행 |
| leanpool_115576 | `TauCeti.exists_selfAdjoint_contraction_extension_of_column_gram_le` | 1,217 | 둘 다 | 1,217 | [파일](<../../../leanpool/context/LeanPool/DavisKahan/ForTauCeti/Analysis/InnerProductSpace/Polar/SelfAdjointCompletion.lean>) · 418행 |
| leanpool_133775 | `ESS.gauss_vector_upper_integral_eq_sum` | 1,217 | 둘 다 | 1,217 | [파일](<../../../leanpool/context/LeanPool/EscauriazaSereginSverak/Linear/CarlemanGaussVectorIntegrable.lean>) · 196행 |
| leanpool_27933 | `Bananas.rankDelta_first_cross_witness_neg` | 1,217 | 둘 다 | 1,217 | [파일](<../../../leanpool/context/LeanPool/BrillNoetherGraphs/Bananas/SameStrand/NSMCrossWitness.lean>) · 228행 |
| leanpool_51014 | `Chudnovsky.hasSum_A` | 1,217 | 둘 다 | 1,217 | [파일](<../../../leanpool/context/LeanPool/Chudnovsky/SingularModuli/ModularPolynomialQ.lean>) · 1045행 |

원문 문맥·버전·검증 상태는 전체 증명 레코드에 유지된다. `context_file`은 `original_corpus_root` 기준 상대경로이며 `context_path_from_repository_root`는 저장소 루트 기준 경로다. 독립 컴파일 가능한 문제 파일이라고 가정하지 않는다.
