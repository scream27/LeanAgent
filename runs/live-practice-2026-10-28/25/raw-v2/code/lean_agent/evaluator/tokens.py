"""Statement-anchored source tokens, not model/BPE or proof-term tokens.

The lexical convention follows the public Lean Refactor proof_length algorithm
(05f1dad97199). We deliberately use the supplied statement boundary and a nested
comment scanner. This is a versioned local metric, not an official worker score.
"""
import re

TOKENIZER_ID = "lean-source-anchored-v1"
OPERATORS = (":=", "!=", "&&", "-.", "->", "←", "..", "...", "::", ":>",
             "<;>", ";;", "==", "||", "=>", "<=", ">=", "⁻¹", "?_")


def without_comments(text: str) -> str:
    """Remove nested comments, preserving strings, escaped names and newlines."""
    out = []
    i = 0
    while i < len(text):
        if text.startswith("--", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
        elif text.startswith("/-", i):
            depth = 1
            i += 2
            # Keep a separator: deleting a comment must not join identifiers.
            out.append(" ")
            while i < len(text) and depth:
                if text.startswith("/-", i):
                    depth += 1
                    i += 2
                elif text.startswith("-/", i):
                    depth -= 1
                    i += 2
                else:
                    if text[i] == "\n":
                        out.append("\n")
                    i += 1
            if depth:
                raise ValueError("Unclosed block comment")
        elif text[i] in ('"', '«'):
            closing = '"' if text[i] == '"' else '»'
            out.append(text[i])
            i += 1
            while i < len(text):
                char = text[i]
                out.append(char)
                i += 1
                if char == "\\" and closing == '"' and i < len(text):
                    out.append(text[i])
                    i += 1
                elif char == closing:
                    break
            else:
                raise ValueError("Unclosed string or escaped identifier")
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def proof_body(declaration: str, statement: str) -> str:
    if not declaration.startswith(statement):
        raise ValueError("The theorem statement must be preserved byte-for-byte")
    rest = declaration[len(statement):]
    match = re.match(r"\s*:=", rest)
    if not match:
        raise ValueError("Expected := immediately after the fixed statement")
    return rest[match.end():]


def proof_tokens(declaration: str, statement: str) -> int:
    body = without_comments(proof_body(declaration, statement))
    count = 0
    for line in body.splitlines():
        if not line.strip():
            continue
        tokens, word = [], ""
        for char in line:
            if char.isalnum() or char in "._'":
                word += char
            else:
                if word:
                    tokens.append(word)
                    word = ""
                if not char.isspace():
                    tokens.append(char)
        if word:
            tokens.append(word)
        spaced = " ".join(tokens)
        for op in OPERATORS:
            spaced = spaced.replace(" ".join(op), op)
        count += len(spaced.split())
    if count == 0:
        raise ValueError("Empty proof body")
    return count


def validate_declaration(declaration: str, statement: str) -> None:
    """Conservative gate for a single tactic proof. This is not a sandbox."""
    body = without_comments(proof_body(declaration, statement))
    if not re.match(r"\s*by\b", body):
        raise ValueError("v1 accepts tactic proofs (:= by ...) only")
    banned = (
        r"\b(sorry|sorryAx|admit|axiom|unsafe|native_decide|ofReduceBool|ofReduceNat|"
        r"run_tac|run_elab|run_cmd|initialize|builtin_initialize|implemented_by|"
        r"extern|set_option|macro|macro_rules|elab|elab_rules|syntax|notation|"
        r"attribute|import|namespace|section|end|def|abbrev|instance|structure|"
        r"inductive|class|opaque|theorem|lemma|example|variable|universe|export)\b|#|\bIO\."
    )
    if re.search(banned, body):
        raise ValueError("Forbidden command, axiom, option or executable construct in proof")
