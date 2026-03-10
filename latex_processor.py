import re

convertt = "MATLAB"
single_variable = True

# ---------- small helpers ----------
def find_matching_brace(s, start):
    """Given index `start` pointing to a '{', return index of matching '}' or -1 if none."""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1

# ---------- fraction replacement (balanced) ----------
def replace_frac_balanced(s: str, frac_div: str = '/') -> str:
    """
    Find each occurrence of \frac{...}{...} (with balanced braces) and replace with
    (numerator){frac_div}(denominator)
    This handles nested braces inside numerator/denominator.
    """
    out = s
    i = 0
    while True:
        idx = out.find(r'\frac', i)
        if idx == -1:
            break
        pos = idx + 5  # position of the char immediately after '\frac'
        # require a '{' for numerator
        if pos >= len(out) or out[pos] != '{':
            i = idx + 5
            continue
        num_start = pos
        num_end = find_matching_brace(out, num_start)
        if num_end == -1:
            break
        den_start = num_end + 1
        if den_start >= len(out) or out[den_start] != '{':
            i = idx + 5
            continue
        den_end = find_matching_brace(out, den_start)
        if den_end == -1:
            break
        numerator = out[num_start + 1:num_end]
        denominator = out[den_start + 1:den_end]
        # Use single parentheses around numerator/denominator: (num)/(den)
        replacement = f"({numerator}){frac_div}({denominator})"
        out = out[:idx] + replacement + out[den_end + 1:]
        i = 0  # restart scanning (we replaced text; restart to handle nested cases)
    return out

# ---------- caret (exponent) replacement (balanced) ----------
def replace_caret_balanced(s: str, caret_symbol='^') -> str:
    """
    Replace occurrences like base^{...} where base is [A-Za-z0-9]+ with base^(...).
    Uses balanced-brace parsing so nested braces inside exponent are handled.
    """
    out = s
    i = 0
    base_pattern = re.compile(r'([A-Za-z0-9\)]+)\^\{')
    while True:
        m = base_pattern.search(out, i)
        if not m:
            break
        base = m.group(1)
        brace_start = m.end() - 1  # index of the '{'
        brace_end = find_matching_brace(out, brace_start)
        if brace_end == -1:
            i = m.end()
            continue
        content = out[brace_start + 1:brace_end]
        replacement = f"{base}{caret_symbol}({content})"
        out = out[:m.start()] + replacement + out[brace_end + 1:]
        i = m.start() + len(replacement)
    return out

# ---------- main transformer ----------
def transform_latex(s: str,
                    convert_to: str = convertt,
                    single_var: bool = single_variable,
                    plus_symbol: str = '+',
                    minus_symbol: str = '-',
                             # symbol to use for exponent
                    insert_mult_before_paren: bool = True,  # whether to insert mult between number and '('
                    space_around_mult: bool = False,           # whether to add spaces around inserted multipliers
                    

                   ) -> str:
    """
    Pipeline implementing the rules you requested. Returns the transformed string.
    """

    out = s[:]  # copy input

    if convert_to == "MATLAB":
        cdot_replacement = '.*'
        mult_symbol = '.*'
        frac_div = './'
        caret_symbol = '.^'
    
    elif convert_to == 'PYTHON':
        cdot_replacement = '*'
        mult_symbol = '*'
        frac_div = '/'
        caret_symbol = '**'
    
    elif convert_to == 'JUSTMATH':
        cdot_replacement = '*'
        mult_symbol = '*'
        frac_div = '/'
        caret_symbol = '^'
        convert_to = "MATLAB"

    # 1) remove \left and \right
    out = re.sub(r'\\left', '', out)
    out = re.sub(r'\\right', '', out)

    # 2) replace \cdot with chosen token
    out = re.sub(r'\\cdot', cdot_replacement, out)
    out = re.sub(r'\)\(',")"+cdot_replacement+"(", out)
    # 3) replace nested \frac by repeatedly applying the balanced replacer until none left
    prev = None
    while prev != out:
        prev = out
        out = replace_frac_balanced(out, frac_div=frac_div)

    if single_var:
    # convert e^letter
        out = re.sub(r"e\^([a-zA-Z0-9])", r"e^{\1}", out)
        
        # convert standalone e
        out = re.sub(r"e(?!\^)", r"e^{1}", out)

    print(out)
    # 4) convert a^{...} -> a^(...) using balanced parser
    #out = replace_caret_balanced(out, caret_symbol=caret_symbol)
    out = re.sub(r"\^", caret_symbol, out)
    
    # 5) mild cleanup: convert any leftover { } to ( ) (keeps things tidy)
    out = out.replace('{', '(').replace('}', ')')
    
    out = re.sub(r"\\\s+|\s+", "", out)
    
    mult_tok = f' {mult_symbol} ' if space_around_mult else mult_symbol
    if insert_mult_before_paren and single_var:
        out = re.sub(r'(?<=[0-9\)A-Za-z])(?=[A-Za-z\\(])', mult_tok, out)
    else:
        out = re.sub(r'(?<=[0-9\)])(?=[\\(])', mult_tok, out)
    
    func_list = [r"\\sqrt",r"\\ln",r"\\sin",r"\\cos",r"\\tan",r"\\e",r"\\pi",r"\\arcsin",r"\\arccos",r"\\arctan"]
    

    
    py_list = ["np.sqrt","np.log","np.sin","np.cos","np.tan","np.exp","np.pi","np.arcsin","np.arccos","np.arctan"]
    mat_list = ["sqrt","log","sin","cos","tan","exp","pi","asin","acos","atan"]

    if convert_to == "PYTHON":

        if single_var:
            out = re.sub(r"\\s\*q\*r\*t\*|\\s\*q\*r\*t",func_list[0], out)
            out = re.sub(r"\\l\*n\*|\\l\*n",func_list[1], out)
            out = re.sub(r"\\s\*i\*n\*|\\s\*i\*n",func_list[2], out)
            out = re.sub(r"\\c\*o\*s\*|\\c\*o\*s",func_list[3], out)
            out = re.sub(r"\\t\*a\*n\*|\\t\*a\*n",func_list[4], out)
            out = re.sub(r"e\^|e\.\^|e\*\*",func_list[5], out)
            out = re.sub(r"\\p\*i",func_list[6], out)
            out = re.sub(r"\\a\*r\*c\*s\*i\*n\*|\\a\*r\*c\*s\*i\*n",func_list[7], out)
            out = re.sub(r"\\a\*r\*c\*c\*o\*s\*|\\a\*r\*c\*c\*o\*s",func_list[8], out)
            out = re.sub(r"\\a\*r\*c\*t\*a\*n\*|\\a\*r\*c\*t\*a\*n",func_list[9], out)

        out = re.sub(r'\\sqrt',py_list[0], out)
        out = re.sub(r'\\ln',py_list[1], out)
        out = re.sub(r'\\sin',py_list[2], out)
        out = re.sub(r'\\cos',py_list[3], out)
        out = re.sub(r'\\tan',py_list[4], out)
        
        if not single_var:
            out = re.sub(r"e\^|e\.\^|e\*\*",func_list[5], out)
        out = re.sub(r'\\e\^|\\e\.\^|\\e\*\*|\\e',py_list[5], out)
       

        
        out = re.sub(r'\\pi',py_list[6], out)
        out = re.sub(r'\\arcsin',py_list[7], out)
        out = re.sub(r'\\arccos',py_list[8], out)
        out = re.sub(r'\\arctan',py_list[9], out)

    elif convert_to == "MATLAB":

        if single_var:
            out = re.sub(r"\\s\.\*q\.\*r\.\*t\.\*|\\s\.\*q\.\*r\.\*t|\\s\*q\*r\*t\*",func_list[0], out)
            out = re.sub(r"\\l\.\*n\.\*|\\l\.\*n|\\l\*n\*",func_list[1], out)
            out = re.sub(r"\\s\.\*i\.\*n\.\*|\\s\.\*i\.\*n|\\s\*i\*n\*",func_list[2], out)
            out = re.sub(r"\\c\.\*o\.\*s\.\*|\\c\.\*o\.\*s|\\c\*o\*s\*",func_list[3], out)
            out = re.sub(r"\\t\.\*a\.\*n\.\*|\\t\.\*a\.\*n|\\t\*a\*n\*",func_list[4], out)
            out = re.sub(r"e\^|e\.\^|e\*\*|e\.\*",func_list[5], out)
            out = re.sub(r"\\p\.\*i|\\p\*i",func_list[6], out)
            out = re.sub(r"\\a\.\*r\.\*c\.\*s\.\*i\.\*n\.\*|\\a\.\*r\.\*c\.\*s\.\*i\.\*n|\\a\*r\*c\*s\*i\*n\*",func_list[7], out)
            out = re.sub(r"\\a\.\*r\.\*c\.\*c\.\*o\.\*s\.\*|\\a\.\*r\.\*c\.\*c\.\*o\.\*s|\\a\*r\*c\*c\*o\*s\*",func_list[8], out)
            out = re.sub(r"\\a\.\*r\.\*c\.\*t\.\*a\.\*n\.\*|\\a\.\*r\.\*c\.\*t\.\*a\.\*n|\\a\*r\*c\*t\*a\*n\*",func_list[9], out)

        out = re.sub(r'\\sqrt',mat_list[0], out)
        out = re.sub(r'\\ln',mat_list[1], out)
        out = re.sub(r'\\sin',mat_list[2], out)
        out = re.sub(r'\\cos',mat_list[3], out)
        out = re.sub(r'\\tan',mat_list[4], out)
        if not single_var:
            out = re.sub(r"e\^|e\.\^|e\*\*",func_list[5], out)
        out = re.sub(r'\\e\^|\\e\.\^|\\e\*\*|\\e',mat_list[5], out)
        out = re.sub(r'\\pi',mat_list[6], out)
        out = re.sub(r'\\arcsin',mat_list[7], out)
        out = re.sub(r'\\arccos',mat_list[8], out)
        out = re.sub(r'\\arctan',mat_list[9], out)
    # 6) insert explicit multiplication between:
    #    - a digit or a closing ')' and a following letter or backslash-macro
    #    Optionally also insert between number and '(' if insert_mult_before_paren=True
    print(out)

    # 7) allow remapping of plus and minus if requested (default leaves them unchanged)
    if plus_symbol != '+':
        out = out.replace('+', plus_symbol)
    if minus_symbol != '-':
        out = out.replace('-', minus_symbol)

    # 8) tidy repeated multipliers if they accidentally appear
    #out = re.sub(re.escape(mult_tok) + r'\s*' + re.escape(mult_tok), mult_tok, out)

    if not single_var:
        out = out.replace('\\', "")

    return out

# ---------- space reserved for adding extra rules ----------
# If you need more transformations later, append them as new functions or add calls
# in the pipeline above (for example: handle implicit multiplication with parentheses,
# convert other latex macros, handle trigonometric functions, etc.)
#
# Example: define a function `handle_custom_macro(out)` and call it before the final return.

# ---------- quick example (your provided test) ----------
if __name__ == "__main__":
    
    sample = input()
    print("INPUT:")
    print(sample)
    print("\nOUTPUT:")
    print(transform_latex(sample))
    