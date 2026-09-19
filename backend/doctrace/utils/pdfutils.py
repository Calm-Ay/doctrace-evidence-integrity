import re
from typing import List, Tuple, Dict, Any

def tokenize_stream(data: bytes) -> List[Tuple[str, bytes]]:
    """
    Tokenizes a PDF page content stream.
    Returns a list of (token_type, token_bytes) tuples.
    Types: 'STRING', 'HEX_STRING', 'ARRAY_START', 'ARRAY_END',
           'DICT_START', 'DICT_END', 'NAME', 'DELIMITER', 'OTHER'
    """
    tokens = []
    i = 0
    n = len(data)
    while i < n:
        c = data[i:i+1]
        # Skip whitespace
        if c in b' \t\r\n\0':
            i += 1
            continue
        # Skip comments
        if c == b'%':
            while i < n and data[i:i+1] not in b'\r\n':
                i += 1
            continue
        # Literal strings
        if c == b'(':
            start = i
            i += 1
            depth = 1
            while i < n and depth > 0:
                char = data[i:i+1]
                if char == b'\\':
                    i += 2  # skip escaped character
                elif char == b'(':
                    depth += 1
                    i += 1
                elif char == b')':
                    depth -= 1
                    i += 1
                else:
                    i += 1
            tokens.append(('STRING', data[start:i]))
            continue
        # Hex strings and dictionaries
        if c == b'<':
            if i + 1 < n and data[i+1:i+2] == b'<':
                tokens.append(('DICT_START', b'<<'))
                i += 2
                continue
            start = i
            i += 1
            while i < n and data[i:i+1] != b'>':
                i += 1
            i += 1  # include '>'
            tokens.append(('HEX_STRING', data[start:i]))
            continue
        # Dict end
        if c == b'>':
            if i + 1 < n and data[i+1:i+2] == b'>':
                tokens.append(('DICT_END', b'>>'))
                i += 2
                continue
            i += 1
            tokens.append(('DELIMITER', b'>'))
            continue
        # Arrays
        if c == b'[':
            tokens.append(('ARRAY_START', b'['))
            i += 1
            continue
        if c == b']':
            tokens.append(('ARRAY_END', b']'))
            i += 1
            continue
        # Names (slash delimited)
        if c == b'/':
            start = i
            i += 1
            while i < n and data[i:i+1] not in b' \t\r\n\0%()<>[]/':
                i += 1
            tokens.append(('NAME', data[start:i]))
            continue
        # General numbers, operators, or keywords
        start = i
        while i < n and data[i:i+1] not in b' \t\r\n\0%()<>[]/':
            i += 1
        tokens.append(('OTHER', data[start:i]))
    return tokens

def tokens_to_bytes(tokens: List[Tuple[str, bytes]]) -> bytes:
    """Reconstructs the content stream bytes from a list of tokens."""
    out = []
    for idx, (t_type, t_bytes) in enumerate(tokens):
        if idx > 0:
            prev_type = tokens[idx-1][0]
            # Add whitespace between consecutive 'OTHER' or 'NAME' tokens
            if t_type in ('OTHER', 'NAME') and prev_type in ('OTHER', 'NAME'):
                out.append(b' ')
        out.append(t_bytes)
    return b''.join(out)
