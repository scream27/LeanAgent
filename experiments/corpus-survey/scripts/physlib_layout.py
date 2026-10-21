"""Low-memory source layout extraction. This is NOT Lean elaboration or a full AST.

Uses native declaration-start anchors, independently balances header delimiters,
and finds the next outer command by Lean layout. All offsets are character offsets.
Every supported boundary is calibrated against the existing native corpus.
"""
import bisect
import re
from physlib_lexical import mask_syntax_quotations


def code_mask(text):
    """Hide nested comments; retain opaque string/character spans as x tokens."""
    chars = list(text)
    i, depth = 0, 0
    while i < len(text):
        if depth:
            if text.startswith('/-', i):
                chars[i:i+2] = '  '; depth += 1; i += 2
            elif text.startswith('-/', i):
                chars[i:i+2] = '  '; depth -= 1; i += 2
            else:
                if text[i] != '\n': chars[i] = ' '
                i += 1
        elif text.startswith('/-', i):
            chars[i:i+2] = '  '; depth = 1; i += 2
        elif text.startswith('--', i):
            while i < len(text) and text[i] != '\n': chars[i] = ' '; i += 1
        elif text[i] == '"':
            chars[i] = 'x'; i += 1
            while i < len(text):
                c = text[i]
                if c != '\n': chars[i] = 'x'
                i += 1
                if c == '\\' and i < len(text): chars[i] = 'x'; i += 1
                elif c == '"': break
        elif text[i] == '«':
            while i < len(text):
                c = text[i]; chars[i] = 'x'; i += 1
                if c == '»': break
        else: i += 1
    return ''.join(chars)


COMMAND = re.compile(r'(?m)^([ \t]*)(?:(?:private|protected|public|noncomputable|unsafe|nonrec|meta|partial)\s+)*(?:'
                     r'lemma|theorem|def|abbrev|instance|opaque|axiom|constant|structure|inductive|class|'
                     r'namespace|section|end|variable|variables|include|omit|open|export|set_option|attribute|'
                     r'local|scoped|notation|infix|infixl|infixr|prefix|postfix|syntax|macro|macro_rules|'
                     r'elab|elab_rules|initialize|builtin_initialize|example|mutual|declare_syntax_cat|'
                     r'informal_lemma|informal_definition|note|TODO|todo|remark|alias|add_aesop_rules|'
                     r'initialize_simps_projections|register_simp_attr|register_label_attr|universe|universes|'
                     r'declare_aesop_rule_sets)\b|(?m:^([ \t]*)(?:@\[|#))')
# Ket/operator notation shapes declared by Physlib TightBindingChain.
TOKEN = re.compile(r'⟨[^|\n⟨⟩:=<>,]+\|[^|\n⟨⟩:=<>,]+⟩|(?<![<|])\|[^|\n⟨⟩:=<>]+⟩⟨[^|\n⟨⟩:=<>]+\||(?<![<|])\|[^|\n⟨⟩:=<>]+⟩|:=|=>|[()\[\]{}⟨⟩]|[^\W\d][\w\'.]*|\||\S')


class Layout:
    def __init__(self, text):
        self.text = text
        self.code = code_mask(text)
        self.command_code = mask_syntax_quotations(self.code)
        self.commands = [(m.start(), len(m[1] if m[1] is not None else m[2]))
                         for m in COMMAND.finditer(self.command_code)]
        self.starts = [x[0] for x in self.commands]

    def extract(self, node):
        text, code = self.text, self.code
        char = lambda byte: len(text.encode()[:byte].decode())
        keyword = char(node['declaration_range']['start_byte'])
        root = char(node['root_command_range']['start_byte'])
        first = re.search(r'\S', code[root:keyword+7])
        start = root + first.start() if first else keyword
        line_start = text.rfind('\n', 0, start) + 1
        indent = len(text[line_start:start])
        # Commands inside a proof occur to the right of its enclosing declaration.
        boundary = len(text)
        for offset, col in self.commands[bisect.bisect_right(self.starts, keyword):]:
            if col <= indent:
                boundary = offset
                break
        meaningful = code[start:boundary].rstrip()
        end = start + len(meaningful)
        stack, delimiter, style = [], None, None
        pending_bindings, header_match_indent = 0, None
        equation_start = None
        pairs = {')':'(', ']':'[', '}':'{', '⟩':'⟨'}
        for token in TOKEN.finditer(code, keyword, end):
            value = token[0]
            if not stack and value in {'let', 'letI', 'have', 'haveI', 'suffices'}:
                pending_bindings += 1
            if not stack and value in {'match', 'fun'}:
                begin = text.rfind('\n', 0, token.start()) + 1
                header_match_indent = len(code[begin:token.start()]) - len(code[begin:token.start()].lstrip())
            if value in {'(', '[', '{', '⟨'}: stack.append(value)
            elif value in pairs:
                if not stack or stack.pop() != pairs[value]:
                    raise ValueError(f'unbalanced header delimiter at {token.start()}')
            elif not stack and value == '=>' and equation_start is not None:
                delimiter = proof_start = equation_start
                style = 'equations'
                break
            elif not stack and value in {':=', 'where', '|'}:
                if value == ':=' and pending_bindings:
                    pending_bindings -= 1
                    continue
                pipe_prefix = code[text.rfind('\n', 0, token.start())+1:token.start()]
                if value == '|' and ((header_match_indent is not None and len(pipe_prefix) >= header_match_indent) or pipe_prefix.strip()):
                    equation_start = None
                    continue
                if value == '|':
                    if equation_start is None: equation_start = token.start()
                    continue
                delimiter = token.start()
                style = 'assignment' if value == ':=' else 'structure' if value == 'where' else 'equations'
                proof_start = token.end() if value == ':=' else token.start()
                break
        if delimiter is None: raise ValueError('no outer declaration value delimiter')
        if end <= proof_start: raise ValueError('empty source proof')
        return {'start_char':start, 'end_char':end, 'proof_start_char':proof_start,
                'delimiter_start_char':delimiter, 'value_style':style,
                'src':text[start:end], 'statement':text[start:delimiter].rstrip(),
                'proof':text[proof_start:end]}


def recovered_node(text, node, span):
    """Provide source spans to the shared serializer, explicitly NOT a native AST."""
    byte = lambda char: len(text[:char].encode())
    rg = lambda a, b: {'start_byte': byte(a), 'end_byte': byte(b)}
    assignment = span['value_style'] == 'assignment'
    value_kind = ('Lean.Parser.Command.declValSimple' if assignment else
                  'Lean.Parser.Command.whereStructInst' if span['value_style'] == 'structure' else
                  'Lean.Parser.Command.declValEqns')
    return dict(node, layout_recovered=True, has_missing_syntax=True,
                root_command_range=rg(span['start_char'], span['end_char']),
                command_range=rg(span['start_char'], span['end_char']),
                value_range=rg(span['delimiter_start_char'], span['end_char']),
                assignment_range=rg(span['delimiter_start_char'], span['proof_start_char']) if assignment else None,
                value_kind=value_kind,
                proof_kind='Lean.Parser.Term.byTactic' if code_mask(span['proof']).lstrip().startswith('by') else 'layout.term',
                proof_range=None, proof_with_suffix_range=None,
                termination_suffix_range=None, where_declarations_range=None)
