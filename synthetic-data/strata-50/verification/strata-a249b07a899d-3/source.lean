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
  constructor
  · decide
  · unfold HAppend.hAppend Array.instHAppendList Array.appendList
    simp only [List.foldl, Array.push, List.concat]
    intro lf
    rw [← Array.mem_toList_iff]
    intro Hmem
    repeat (
      rcases Hmem with _ | ⟨a', Hmem⟩
      · constructor
        · decide
        · decide
        · simp (config := { ground := true })
          try (
            repeat first | unfold unOpCeval | unfold binOpCeval
              | unfold cevalIntDiv | unfold cevalIntMod | unfold bvUnaryOp
              | unfold bvBinaryOp | unfold bvShiftOp | unfold bvBinaryPred
            intros lf md args res
            repeat (rcases args with _ | ⟨args0, args⟩ <;> try grind)))
    contradiction

end Core
