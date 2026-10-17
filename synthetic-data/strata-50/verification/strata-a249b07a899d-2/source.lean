/-
  Copyright Strata Contributors

  SPDX-License-Identifier: Apache-2.0 OR MIT
-/

import Strata.Languages.Core.Factory
import Strata.DL.Lambda.Factory
import Strata.DL.Lambda.IntBoolFactory

/-! # Factory Wellformedness Proof

  This file contains the proof that the Strata Core Factory is well-formed.
-/

namespace Core
open Lambda

set_option maxRecDepth 32768 in
set_option maxHeartbeats 4000000 in
/--
Wellformedness of Factory
-/
theorem Factory_wf :
    FactoryWF Factory := by
  unfold Factory
  refine ⟨by decide, ?_⟩
  unfold HAppend.hAppend Array.instHAppendList Array.appendList
  simp only [List.foldl, Array.push, List.concat]
  intro lf
  rw [← Array.mem_toList_iff]
  intro Hmem
  repeat (
    rcases Hmem with _ | ⟨a', Hmem⟩
    · refine ⟨by decide, by decide, ?_⟩
      simp (config := { ground := true })
      try (
        simp only [unOpCeval, binOpCeval, cevalIntDiv, cevalIntMod,
          bvUnaryOp, bvBinaryOp, bvShiftOp, bvBinaryPred]
        intros lf md args res
        repeat (rcases args with _ | ⟨args0, args⟩ <;> try grind)))
  contradiction

end Core
