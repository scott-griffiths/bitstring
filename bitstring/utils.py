from __future__ import annotations

import functools
import re
from re import Pattern, Match


# A token name followed by optional : then an integer number
NAME_INT_RE: Pattern[str] = re.compile(r'^([a-zA-Z][a-zA-Z0-9_]*?):?(\d*)$')

# A token name followed by optional : then an arbitrary keyword
NAME_KWARG_RE: Pattern[str] = re.compile(r'^([a-zA-Z][a-zA-Z0-9_]*?):?([a-zA-Z0-9_]+)$')

CACHE_SIZE = 256

DEFAULT_BITS: Pattern[str] = re.compile(r'^(?P<len>[^=]+)?(=(?P<value>.*))?$', re.IGNORECASE)

MULTIPLICATIVE_RE: Pattern[str] = re.compile(r'^(?P<factor>.*)\*(?P<token>.+)')

# Hex, oct or binary literals
LITERAL_RE: Pattern[str] = re.compile(r'^(?P<name>0([xob]))(?P<value>.+)', re.IGNORECASE)

# An endianness indicator followed by one or more struct.pack codes
STRUCT_PACK_RE: Pattern[str] = re.compile(r'^(?P<endian>[<>@=])(?P<fmt>(?:\d*[bBhHlLiIqQefd])+)$')
# The same as above, but it doesn't insist on an endianness as it's byteswapping anyway.
BYTESWAP_STRUCT_PACK_RE: Pattern[str] = re.compile(r'^(?P<endian>[<>@=])?(?P<fmt>(?:\d*[bBhHlLiIqQefd])+)$')
# An endianness indicator followed by exactly one struct.pack codes
SINGLE_STRUCT_PACK_RE: Pattern[str] = re.compile(r'^(?P<endian>[<>@=])(?P<fmt>[bBhHlLiIqQefd])$')

# A number followed by a single character struct.pack code
STRUCT_SPLIT_RE: Pattern[str] = re.compile(r'\d*[bBhHlLiIqQefd]')

# These replicate the struct.pack codes
# Big-endian
REPLACEMENTS_BE: dict[str, str] = {'b': 'i8', 'B': 'u8',
                                   'h': 'ibe16', 'H': 'ube16',
                                   'l': 'ibe32', 'L': 'ube32',
                                   'i': 'ibe32', 'I': 'ube32',
                                   'q': 'ibe64', 'Q': 'ube64',
                                   'e': 'f16', 'f': 'f32', 'd': 'f64'}
# Little-endian
REPLACEMENTS_LE: dict[str, str] = {'b': 'i8', 'B': 'u8',
                                   'h': 'ile16', 'H': 'ule16',
                                   'l': 'ile32', 'L': 'ule32',
                                   'i': 'ile32', 'I': 'ule32',
                                   'q': 'ile64', 'Q': 'ule64',
                                   'e': 'fle16', 'f': 'fle32', 'd': 'fle64'}

# Size in bytes of all the pack codes.
PACK_CODE_SIZE: dict[str, int] = {'b': 1, 'B': 1, 'h': 2, 'H': 2, 'l': 4, 'L': 4, 'i': 4, 'I': 4,
                                  'q': 8, 'Q': 8, 'e': 2, 'f': 4, 'd': 8}

NATIVE_ENDIAN_STRUCT_ERROR = "Native-endian struct formats '@' and '=' are not supported; use '<' for little-endian or '>' for big-endian."


def structparser(m: Match[str]) -> list[str]:
    """Parse struct-like format string token into sub-token list."""
    endian = m.group('endian')
    if endian in '@=':
        raise ValueError(NATIVE_ENDIAN_STRUCT_ERROR)
    # Split the format string into a list of 'q', '4h' etc.
    formatlist = re.findall(STRUCT_SPLIT_RE, m.group('fmt'))
    # Now deal with multiplicative factors, 4h -> hhhh etc.
    fmt = ''.join([f[-1] * int(f[:-1]) if len(f) != 1 else
                   f for f in formatlist])
    if endian == '<':
        tokens = [REPLACEMENTS_LE[c] for c in fmt]
    else:
        assert endian == '>'
        tokens = [REPLACEMENTS_BE[c] for c in fmt]
    return tokens


@functools.lru_cache(CACHE_SIZE)
def parse_name_length_token(fmt: str, **kwargs) -> tuple[str, int | None]:
    # Any single token with just a name and length
    if m2 := NAME_INT_RE.match(fmt):
        name = m2.group(1)
        length_str = m2.group(2)
        length = None if length_str == '' else int(length_str)
    else:
        # Maybe the length is in the kwargs?
        if m := NAME_KWARG_RE.match(fmt):
            name = m.group(1)
            try:
                length_str = kwargs[m.group(2)]
            except KeyError:
                raise ValueError(f"Can't parse 'name[:]length' token '{fmt}'.")
            length = int(length_str)
        else:
            raise ValueError(f"Can't parse 'name[:]length' token '{fmt}'.")
    return name, length


@functools.lru_cache(CACHE_SIZE)
def parse_single_struct_token(fmt: str) -> tuple[str, int | None] | None:
    if m := SINGLE_STRUCT_PACK_RE.match(fmt):
        endian = m.group('endian')
        f = m.group('fmt')
        if endian in '=@':
            raise ValueError(NATIVE_ENDIAN_STRUCT_ERROR)
        if endian == '>':
            fmt = REPLACEMENTS_BE[f]
        else:
            assert endian == '<'
            fmt = REPLACEMENTS_LE[f]
        return parse_name_length_token(fmt)
    else:
        return None


@functools.lru_cache(CACHE_SIZE)
def parse_single_token(token: str) -> tuple[str, str, str | None]:
    if (equals_pos := token.find('=')) == -1:
        value = None
    else:
        value = token[equals_pos + 1:]
        token = token[:equals_pos]

    if m2 := NAME_INT_RE.match(token):
        name = m2.group(1)
        length_str = m2.group(2)
        length = None if length_str == '' else length_str
    elif m3 := NAME_KWARG_RE.match(token):
        # name then a keyword for a length
        name = m3.group(1)
        length = m3.group(2)
    else:
        # If you don't specify a 'name' then the default is 'bits'
        name = 'bits'
        length = token
    return name, length, value


@functools.lru_cache(CACHE_SIZE)
def preprocess_tokens(fmt: str) -> list[str]:
    # Remove whitespace and expand brackets
    fmt = expand_brackets(''.join(fmt.split()))

    # Split tokens by ',' and remove whitespace
    # The meta_tokens can either be ordinary single tokens or multiple struct-format token strings.
    meta_tokens = [f.strip() for f in fmt.split(',')]
    final_tokens = []

    for meta_token in meta_tokens:
        if meta_token == '':
            continue
        # Extract factor and actual token if a multiplicative factor exists
        factor = 1
        if m := MULTIPLICATIVE_RE.match(meta_token):
            factor = int(m.group('factor'))
            if factor < 0:
                raise ValueError(f"Negative multiplicative factors are not allowed: '{meta_token}'.")
            meta_token = m.group('token')

        # Parse struct-like format into sub-tokens or treat as single token
        tokens = structparser(m) if (m := STRUCT_PACK_RE.match(meta_token)) else [meta_token]

        # Extend final tokens list with parsed tokens, repeated by the factor
        final_tokens.extend(tokens * factor)
    return final_tokens


@functools.lru_cache(CACHE_SIZE)
def tokenparser(fmt: str, keys: tuple[str, ...] = ()) -> \
        tuple[bool, list[tuple[str, int | str | None, str | None]]]:
    """Divide the format string into tokens and parse them.

    Return stretchy token and list of [initialiser, length, value]
    initialiser is one of: hex, oct, bin, u, i, se, ue, 0x, 0o, 0b etc.
    length is None if not known, as is value.

    If the token is in the keyword dictionary (keys) then it counts as a
    special case and isn't messed with.

    tokens must be of the form: [factor*][initialiser][:][length][=value]

    """
    tokens = preprocess_tokens(fmt)
    stretchy_token = False
    ret_vals: list[tuple[str, str | int | None, str | None]] = []
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
            count += (s[p] == '(') - (s[p] == ')')
            if count == 0:
                break
            p += 1
        if count != 0:
            raise ValueError(f"Unbalanced parenthesis in '{s}'.")
        if start == 0 or s[start - 1] != '*':
            s = s[0:start] + s[start + 1:p] + s[p + 1:]
        else:
            # Looks for first number*(
            m = BRACKET_RE.search(s)
            if m:
                factor = int(m.group('factor'))
                matchstart = m.start('factor')
                if factor == 0:
                    s = s[0:matchstart] + s[p + 1:]
                else:
                    s = s[0:matchstart] + (factor - 1) * (s[start + 1:p] + ',') + s[start + 1:p] + s[p + 1:]
            else:
                raise ValueError(f"Failed to parse '{s}'.")
    return s
