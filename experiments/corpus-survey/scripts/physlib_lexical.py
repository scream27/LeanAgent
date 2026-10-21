"""Independent keyword inventory for the pinned Physlib source tree.

This is an audit of declaration starts, never a proof-boundary parser. Comments,
strings, and syntax quotations are masked; declarations can have inline balanced
attributes and modifiers. Native Lean parsing remains authoritative for spans.
"""
from __future__ import annotations

import re

from survey import mask_noncode

MODIFIERS = {"private", "protected", "public", "noncomputable", "unsafe", "nonrec"}


def mask_syntax_quotations(text: str) -> str:
    """Mask Lean `(category| ...) quotations, preserving character offsets."""
    chars = list(mask_noncode(text))
    index = 0
    while index < len(chars) - 1:
        if chars[index] != "`" or chars[index + 1] != "(":
            index += 1
            continue
        end, depth = index + 2, 1
        while end < len(chars) and depth:
            if chars[end] == "(":
                depth += 1
            elif chars[end] == ")":
                depth -= 1
            end += 1
        for offset in range(index, end):
            if chars[offset] not in "\r\n":
                chars[offset] = " "
        index = end
    return "".join(chars)


def declaration_positions(text: str) -> list[int]:
    """Return theorem/lemma keyword offsets, including malformed declarations.

    The pinned corpus uses declaration keywords at line starts, optionally after
    attributes/modifiers. A broad all-keyword audit independently established
    that the only other non-comment/string occurrences are four constructor
    references in scripts/MetaPrograms/informal.lean.
    """
    masked = mask_syntax_quotations(text)
    positions = []
    for line in re.finditer(r"(?m)^[ \t]*", masked):
        offset = line.end()
        while offset < len(masked):
            if masked.startswith("@[", offset):
                offset += 2
                depth = 1
                while offset < len(masked) and depth:
                    if masked[offset] == "[":
                        depth += 1
                    elif masked[offset] == "]":
                        depth -= 1
                    offset += 1
                while offset < len(masked) and masked[offset].isspace():
                    offset += 1
                continue
            word = re.match(r"[A-Za-z_][A-Za-z_0-9']*", masked[offset:])
            if word is None:
                break
            if word[0] in {"theorem", "lemma"}:
                positions.append(offset)
                break
            if word[0] not in MODIFIERS:
                break
            offset += word.end()
            while offset < len(masked) and masked[offset].isspace():
                offset += 1
    return sorted(set(positions))
