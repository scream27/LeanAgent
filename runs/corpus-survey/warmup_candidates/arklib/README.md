# arklib: warm-up 길이 후보

모집단 2,121개. 200토큰 이상 359개, 상위 5% 107개, 교집합 107개.

상위 5% 경계: 580 토큰. 경계 동률을 모두 포함한다. 기존 warm-up도 전체 목록에는 포함하고 번호로 표시한다.

- [200토큰 이상 전체 증명](ge200.jsonl.gz) · [탐색용 인덱스](ge200.index.jsonl)
- [상위 5% 전체 증명](top5pct.jsonl.gz) · [탐색용 인덱스](top5pct.index.jsonl)
- [교집합 인덱스](intersection.index.jsonl) · [먼저 볼 후보 25개 이하](review_first.jsonl)

## 먼저 볼 후보

기존 warm-up을 제외하고 두 조건을 모두 만족하는 후보를 먼저, 그 안에서는 warm-up 길이와의 로그 비율 차이가 작은 순서다. 같은 출처의 warm-up 길이를 사용하며 LeanPool만 전체 15개의 길이를 참고한다. 수학적 내용·tactic·heartbeat 유사도나 출제 확률 순위가 아니다.

| ID | 정리 | 토큰 | 선택 조건 | 가까운 warm-up 길이 | 원문 |
| --- | --- | ---: | --- | ---: | --- |
| arklib_00656 | `ProximityGap.BW_homMatrix_det_updateCol_natDegree_le_of_ge` | 1,367 | 둘 다 | 1,353 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/BCIKS20/AffineLines/BWMatrix.lean>) · 297행 |
| arklib_01585 | `ArkLib.Lattices.CyclotomicModulus.traceH_kernel` | 1,374 | 둘 다 | 1,353 | [파일](<../../../arklib/context/ArkLib/Data/Lattices/CyclotomicRing/Subfield/TraceInnerProduct.lean>) · 107행 |
| arklib_00423 | `DivergenceOfSets.concentration_bounds` | 1,939 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/DivergenceOfSets.lean>) · 800행 |
| arklib_00679 | `ProximityGap.RS_exists_kernelVec_BW_homMatrix_eval_of_mem_goodCoeffs` | 1,328 | 둘 다 | 1,353 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/BCIKS20/AffineLines/GoodCoeffs.lean>) · 66행 |
| arklib_01427 | `ArkLib.Lattices.CyclotomicModulus.Hexp_generator_smul` | 1,870 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Data/Lattices/CyclotomicRing/Galois/Group.lean>) · 181행 |
| arklib_02605 | `Sumcheck.Spec.SingleRound.Simple.reduction_perfectCompleteness` | 1,426 | 둘 다 | 1,463 | [파일](<../../../arklib/context/ArkLib/ProofSystem/Sumcheck/Spec/SingleRound.lean>) · 543행 |
| arklib_00639 | `exists_common_support_of_wt_le` | 1,401 | 둘 다 | 1,353 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/AHIV22Support.lean>) · 76행 |
| arklib_00754 | `ProximityGap.proximity_gap_RSCodes` | 1,818 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/BCIKS20/ReedSolomonGap.lean>) · 34행 |
| arklib_00717 | `ProximityGap.correlatedAgreement_affine_spaces` | 2,004 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/BCIKS20/AffineSpaces.lean>) · 2096행 |
| arklib_02573 | `Combine.combine_theorem` | 1,278 | 둘 다 | 1,353 | [파일](<../../../arklib/context/ArkLib/ProofSystem/Stir/Combine.lean>) · 552행 |
| arklib_00759 | `ProximityGap.WeightedAgreement.list_agreement_on_curve_implies_correlated_agreement_bound` | 1,557 | 둘 다 | 1,463 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/BCIKS20/WeightedAgreement.lean>) · 179행 |
| arklib_00151 | `KZG.CommitmentScheme.binding_cond_le_t_sdh_cond` | 1,784 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Commitments/Functional/KZG/Binding.lean>) · 466행 |
| arklib_00607 | `ps_resultant_dvd_pow_eval_x` | 1,266 | 둘 다 | 1,353 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/PolishchukSpielman/Resultant.lean>) · 141행 |
| arklib_00780 | `prob_R_star_gt_threshold` | 1,253 | 둘 다 | 1,353 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/DG25/MainResults.lean>) · 1048행 |
| arklib_00511 | `JohnsonBound.johnson_condition_weak_implies_strong` | 1,591 | 둘 다 | 1,463 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/JohnsonBound/Basic.lean>) · 101행 |
| arklib_00640 | `dist_interleaved_code_to_code_lb` | 2,074 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/AHIV22Support.lean>) · 222행 |
| arklib_00685 | `ProximityGap.RS_exists_bivariate_AB_of_goodCoeffs_card_gt` | 1,744 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/BCIKS20/AffineLines/JointAgreement.lean>) · 29행 |
| arklib_01896 | `RationalFunctions.HenselNumerators.henselClearedTerm_regular` | 1,730 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Data/Polynomial/RationalFunctions/HenselNumerators/Hensel.lean>) · 891행 |
| arklib_01480 | `ArkLib.Lattices.CyclotomicModulus.q_dvd_l2NormSq_of_not_isUnit` | 1,727 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Data/Lattices/CyclotomicRing/NormBounds/LyubashevskySeiler.lean>) · 148행 |
| arklib_01922 | `RationalFunctions.HenselNumerators.cofactor_top_reduction_weight_le` | 1,618 | 둘 다 | 1,463 | [파일](<../../../arklib/context/ArkLib/Data/Polynomial/RationalFunctions/HenselNumerators/Setup.lean>) · 304행 |
| arklib_01595 | `ArkLib.Lattices.CyclotomicModulus.traceH_Xpow_eq_zero` | 1,220 | 둘 다 | 1,353 | [파일](<../../../arklib/context/ArkLib/Data/Lattices/CyclotomicRing/Subfield/TraceVanishing.lean>) · 174행 |
| arklib_00598 | `ps_exists_p_nonzero` | 1,219 | 둘 다 | 1,353 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/PolishchukSpielman/Existence.lean>) · 170행 |
| arklib_00676 | `ProximityGap.RS_exists_nonzero_kernelVec_of_det_eq_zero_natDegree_le_one` | 2,122 | 둘 다 | 1,906 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/BCIKS20/AffineLines/BWMatrix.lean>) · 952행 |
| arklib_00778 | `affine_gaps_lifted_to_interleaved_codes` | 1,642 | 둘 다 | 1,463 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/ProximityGap/DG25/MainResults.lean>) · 875행 |
| arklib_00418 | `DivergenceOfSets.errorBound_ge_const` | 1,648 | 둘 다 | 1,463 | [파일](<../../../arklib/context/ArkLib/Data/CodingTheory/DivergenceOfSets.lean>) · 436행 |

원문 문맥·버전·검증 상태는 전체 증명 레코드에 유지된다. `context_file`은 `original_corpus_root` 기준 상대경로이며 `context_path_from_repository_root`는 저장소 루트 기준 경로다. 독립 컴파일 가능한 문제 파일이라고 가정하지 않는다.
