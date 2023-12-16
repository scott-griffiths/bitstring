from __future__ import annotations
import functools
import re
from typing import Tuple, List, Optional, Pattern, Dict, Union, Match
import sys
from bitstring.exceptions import Error
byteorder: str = sys.byteorder


TOKEN_RE: Pattern[str] = None

# A token name followed by optional : then an integer number
TOKEN_INT_RE: Pattern[str] = re.compile(r'^([a-zA-Z0-9_]+?):?(\d*)$')

# Tokens which have an unknowable (in advance) length, so it must not be supplied.
UNKNOWABLE_LENGTH_TOKENS: List[str] = None

# Tokens which are always the same length, so it doesn't need to be supplied.
ALWAYS_FIXED_LENGTH_TOKENS: Dict[str, int] = None

def initialise_constants(init_names: List[str], unknowable_length_names: List[str], always_fixed_length: Dict[str, int]) -> None:
    global TOKEN_RE, UNKNOWABLE_LENGTH_TOKENS, ALWAYS_FIXED_LENGTH_TOKENS
    init_names.sort(key=len, reverse=True)
    TOKEN_RE = re.compile(r'^(?P<name>' + '|'.join(init_names) + r'):?(?P<len>[^=]+)?(=(?P<value>.*))?$')
    UNKNOWABLE_LENGTH_TOKENS = unknowable_length_names
    ALWAYS_FIXED_LENGTH_TOKENS = always_fixed_length


CACHE_SIZE = 256

DEFAULT_BITS: Pattern[str] = re.compile(r'^(?P<len>[^=]+)?(=(?P<value>.*))?$', re.IGNORECASE)

MULTIPLICATIVE_RE: Pattern[str] = re.compile(r'^(?P<factor>.*)\*(?P<token>.+)')

# Hex, oct or binary literals
LITERAL_RE: Pattern[str] = re.compile(r'^(?P<name>0([xob]))(?P<value>.+)', re.IGNORECASE)

# An endianness indicator followed by one or more struct.pack codes
STRUCT_PACK_RE: Pattern[str] = re.compile(r'^(?P<endian>[<>@=]){1}(?P<fmt>(?:\d*[bBhHlLqQefd])+)$')
# The same as above, but it doesn't insist on an endianness as it's byteswapping anyway.
BYTESWAP_STRUCT_PACK_RE: Pattern[str] = re.compile(r'^(?P<endian>[<>@=])?(?P<fmt>(?:\d*[bBhHlLqQefd])+)$')
# An endianness indicator followed by exactly one struct.pack codes
SINGLE_STRUCT_PACK_RE: Pattern[str] = re.compile(r'^(?P<endian>[<>@=]){1}(?P<fmt>[bBhHlLqQefd])$')

# A number followed by a single character struct.pack code
STRUCT_SPLIT_RE: Pattern[str] = re.compile(r'\d*[bBhHlLqQefd]')

# These replicate the struct.pack codes
# Big-endian
REPLACEMENTS_BE: Dict[str, str] = {'b': 'int8', 'B': 'uint8',
                                   'h': 'intbe16', 'H': 'uintbe16',
                                   'l': 'intbe32', 'L': 'uintbe32',
                                   'q': 'intbe64', 'Q': 'uintbe64',
                                   'e': 'floatbe16', 'f': 'floatbe32', 'd': 'floatbe64'}
# Little-endian
REPLACEMENTS_LE: Dict[str, str] = {'b': 'int8', 'B': 'uint8',
                                   'h': 'intle16', 'H': 'uintle16',
                                   'l': 'intle32', 'L': 'uintle32',
                                   'q': 'intle64', 'Q': 'uintle64',
                                   'e': 'floatle16', 'f': 'floatle32', 'd': 'floatle64'}

# Native-endian
REPLACEMENTS_NE: Dict[str, str] = {'b': 'int8', 'B': 'uint8',
                                   'h': 'intne16', 'H': 'uintne16',
                                   'l': 'intne32', 'L': 'uintne32',
                                   'q': 'intne64', 'Q': 'uintne64',
                                   'e': 'floatne16', 'f': 'floatne32', 'd': 'floatne64'}

# Size in bytes of all the pack codes.
PACK_CODE_SIZE: Dict[str, int] = {'b': 1, 'B': 1, 'h': 2, 'H': 2, 'l': 4, 'L': 4,
                                  'q': 8, 'Q': 8, 'e': 2, 'f': 4, 'd': 8}


def structparser(m: Match[str]) -> List[str]:
    """Parse struct-like format string token into sub-token list."""
    endian = m.group('endian')
    # Split the format string into a list of 'q', '4h' etc.
    formatlist = re.findall(STRUCT_SPLIT_RE, m.group('fmt'))
    # Now deal with multiplicative factors, 4h -> hhhh etc.
    fmt = ''.join([f[-1] * int(f[:-1]) if len(f) != 1 else
                   f for f in formatlist])
    if endian in '@=':
        # Native endianness
        tokens = [REPLACEMENTS_NE[c] for c in fmt]
    elif endian == '<':
        tokens = [REPLACEMENTS_LE[c] for c in fmt]
    else:
        assert endian == '>'
        tokens = [REPLACEMENTS_BE[c] for c in fmt]
    return tokens

@functools.lru_cache(CACHE_SIZE)
def parse_name_length_token(fmt: str) -> Tuple[str, Optional[int]]:
    # Any single token with just a name and length
    if m2 := TOKEN_INT_RE.match(fmt):
        name = m2.group(1)
        length_str = m2.group(2)
        length = None if length_str == '' else int(length_str)
    else:
        raise ValueError(f"Can't parse 'name[:]length' token '{fmt}'.")

    if name in UNKNOWABLE_LENGTH_TOKENS:
        if length is not None:
            raise ValueError(
                f"The token '{name}' has a variable length and can't be given the fixed length of {length}.")

    if name in ALWAYS_FIXED_LENGTH_TOKENS.keys():
        token_length = ALWAYS_FIXED_LENGTH_TOKENS[name]
        if length not in [None, token_length]:
            raise ValueError(f"{name} tokens can only be {token_length} bits long, not {length} bits.")
        length = token_length
    return name, length


def parse_single_struct_token(fmt: str) -> Optional[Tuple[str, Optional[int]]]:
    if m := SINGLE_STRUCT_PACK_RE.match(fmt):
        endian = m.group('endian')
        f = m.group('fmt')
        if endian == '>':
            fmt = REPLACEMENTS_BE[f]
        elif endian == '<':
            fmt = REPLACEMENTS_LE[f]
        else:
            assert endian in '=@'
            fmt = REPLACEMENTS_NE[f]
        return parse_name_length_token(fmt)
    else:
        return None


@functools.lru_cache(CACHE_SIZE)
def parse_single_token(token: str) -> Tuple[str, str, Optional[str]]:
    if m1 := TOKEN_RE.match(token):
        name = m1.group('name')
        length = m1.group('len')
        value = m1.group('value')
    else:
        # If you don't specify a 'name' then the default is 'bits':
        name = 'bits'
        if not (m2 := DEFAULT_BITS.match(token)):
            raise ValueError(f"Don't understand token '{token}'.")
        length = m2.group('len')
        value = m2.group('value')

    if name in ALWAYS_FIXED_LENGTH_TOKENS.keys():
        token_length = str(ALWAYS_FIXED_LENGTH_TOKENS[name])
        if length is not None and length != token_length:
            raise ValueError(f"{name} tokens can only be {token_length} bits long, not {length} bits.")
        length = token_length

    return name, length, value

def preprocess_tokens(fmt: str) -> List[str]:
    # Remove whitespace
    fmt = ''.join(fmt.split())
    # Expand any brackets.
    fmt = expand_brackets(fmt)
    # Split tokens by ',' and remove whitespace
    # The meta_tokens can either be ordinary single tokens or multiple
    # struct-format token strings.
    meta_tokens = [f.strip() for f in fmt.split(',')]
    single_tokens = []
    for meta_token in meta_tokens:
        # See if it has a multiplicative factor
        if not (m := MULTIPLICATIVE_RE.match(meta_token)):
            factor = 1
        else:
            factor = int(m.group('factor'))
            meta_token = m.group('token')
        # See if it's a struct-like format
        if m := STRUCT_PACK_RE.match(meta_token):
            tokens = structparser(m)
        else:
            tokens = [meta_token]
        single_tokens.extend(tokens * factor)  # TODO: This is inefficient as the same token will be parsed multiple times.
    return single_tokens

@functools.lru_cache(CACHE_SIZE)
def tokenparser(fmt: str, keys: Tuple[str, ...] = ()) -> \
        Tuple[bool, List[Tuple[str, Union[int, str, None], Optional[str]]]]:
    """Divide the format string into tokens and parse them.

    Return stretchy token and list of [initialiser, length, value]
    initialiser is one of: hex, oct, bin, uint, int, se, ue, 0x, 0o, 0b etc.
    length is None if not known, as is value.

    If the token is in the keyword dictionary (keys) then it counts as a
    special case and isn't messed with.

    tokens must be of the form: [factor*][initialiser][:][length][=value]

    """
    tokens = preprocess_tokens(fmt)
    stretchy_token = False
    ret_vals: List[Tuple[str, Union[str, int, None], Optional[str]]] = []
    for token in tokens:
        if keys and token in keys:
            # Don't bother parsing it, it's a keyword argument
            ret_vals.append((token, None, None))
            continue
        if token == '':
            continue
        # Match literal tokens of the form 0x... 0o... and 0b...
        if m := LITERAL_RE.match(token):
            ret_vals.append((m.group('name'), None, m.group('value')))
            continue
        name, length, value = parse_single_token(token)
        if name in UNKNOWABLE_LENGTH_TOKENS:
            if length is not None:
                raise ValueError(f"The token '{name}' has a variable length and can't be given the fixed length of {length}.")
        else:
            if length is None:
                stretchy_token = True
        if length is not None:
            # Try converting length to int, otherwise check it's a key.
            try:
                length = int(length)
            except ValueError:
                if not keys or length not in keys:
                    raise ValueError(f"Don't understand length '{length}' of token.")
        ret_vals.append((name, length, value))
    return stretchy_token, ret_vals


BRACKET_RE = re.compile(r'(?P<factor>\d+)\*\(')

def expand_brackets(s: str) -> str:
    """Expand all brackets."""
    while True:
        start = s.find('(')
        if start == -1:
            break
        count = 1  # Number of hanging open brackets
        p = start + 1
        while p < len(s):
            if s[p] == '(':
                count += 1
            if s[p] == ')':
                count -= 1
            if not count:
                break
            p += 1
        if count:
            raise ValueError(f"Unbalanced parenthesis in '{s}'.")
        if start == 0 or s[start - 1] != '*':
            s = s[0:start] + s[start + 1:p] + s[p + 1:]
        else:
            # Looks for first number*(
            m = BRACKET_RE.search(s)
            if m:
                factor = int(m.group('factor'))
                matchstart = m.start('factor')
                s = s[0:matchstart] + (factor - 1) * (s[start + 1:p] + ',') + s[start + 1:p] + s[p + 1:]
            else:
                raise ValueError(f"Failed to parse '{s}'.")
    return s
