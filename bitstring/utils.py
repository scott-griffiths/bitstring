from __future__ import annotations
import functools
import re
from typing import Tuple, List, Optional, Pattern, Dict, Union
import sys
from bitstring.exceptions import Error

byteorder: str = sys.byteorder

CACHE_SIZE = 256

INIT_NAMES: List[str] = ['uint', 'int', 'ue', 'se', 'sie', 'uie', 'hex', 'oct', 'bin', 'bits',
                         'uintbe', 'intbe', 'uintle', 'intle', 'uintne', 'intne',
                         'float', 'floatbe', 'floatle', 'floatne', 'bfloatbe', 'bfloatle', 'bfloatne', 'bfloat',
                         'bytes', 'bool', 'pad', 'float8_143', 'float8_152']
# Sort longest first as we want to match them in that order (so floatne before float etc.).
INIT_NAMES.sort(key=len, reverse=True)

TOKEN_RE: Pattern[str] = re.compile(r'^(?P<name>' + '|'.join(INIT_NAMES) +
                                    r'):?(?P<len>[^=]+)?(=(?P<value>.*))?$', re.IGNORECASE)
# Tokens such as 'u32', 'f64=4.5' or 'i6=-3'
SHORT_TOKEN_RE: Pattern[str] = re.compile(r'^(?P<name>[uifboh]):?(?P<len>\d+)?(=(?P<value>.*))?$')
DEFAULT_BITS: Pattern[str] = re.compile(r'^(?P<len>[^=]+)?(=(?P<value>.*))?$', re.IGNORECASE)

MULTIPLICATIVE_RE: Pattern[str] = re.compile(r'^(?P<factor>.*)\*(?P<token>.+)')

# Hex, oct or binary literals
LITERAL_RE: Pattern[str] = re.compile(r'^(?P<name>0([xob]))(?P<value>.+)', re.IGNORECASE)

# An endianness indicator followed by one or more struct.pack codes
STRUCT_PACK_RE: Pattern[str] = re.compile(r'^(?P<endian>[<>@=])?(?P<fmt>(?:\d*[bBhHlLqQefd])+)$')

# A number followed by a single character struct.pack code
STRUCT_SPLIT_RE: Pattern[str] = re.compile(r'\d*[bBhHlLqQefd]')

# These replicate the struct.pack codes
# Big-endian
REPLACEMENTS_BE: Dict[str, str] = {'b': 'int:8', 'B': 'uint:8',
                                   'h': 'intbe:16', 'H': 'uintbe:16',
                                   'l': 'intbe:32', 'L': 'uintbe:32',
                                   'q': 'intbe:64', 'Q': 'uintbe:64',
                                   'e': 'floatbe:16', 'f': 'floatbe:32', 'd': 'floatbe:64'}
# Little-endian
REPLACEMENTS_LE: Dict[str, str] = {'b': 'int:8', 'B': 'uint:8',
                                   'h': 'intle:16', 'H': 'uintle:16',
                                   'l': 'intle:32', 'L': 'uintle:32',
                                   'q': 'intle:64', 'Q': 'uintle:64',
                                   'e': 'floatle:16', 'f': 'floatle:32', 'd': 'floatle:64'}

# Native-endian
REPLACEMENTS_NE: Dict[str, str] = {'b': 'int:8', 'B': 'uint:8',
                                   'h': 'intne:16', 'H': 'uintne:16',
                                   'l': 'intne:32', 'L': 'uintne:32',
                                   'q': 'intne:64', 'Q': 'uintne:64',
                                   'e': 'floatne:16', 'f': 'floatne:32', 'd': 'floatne:64'}


def structparser(token: str) -> List[str]:
    """Parse struct-like format string token into sub-token list."""
    m = STRUCT_PACK_RE.match(token)
    if not m:
        return [token]
    else:
        endian = m.group('endian')
        if endian is None:
            return [token]
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
    # Very inefficient expanding of brackets.
    fmt = expand_brackets(fmt)
    # Split tokens by ',' and remove whitespace
    # The meta_tokens can either be ordinary single tokens or multiple
    # struct-format token strings.
    meta_tokens = (''.join(f.split()) for f in fmt.split(','))
    return_values: List[Tuple[str, Union[int, str, None], Optional[str]]] = []
    stretchy_token = False
    for meta_token in meta_tokens:
        # See if it has a multiplicative factor
        m = MULTIPLICATIVE_RE.match(meta_token)
        if not m:
            factor = 1
        else:
            factor = int(m.group('factor'))
            meta_token = m.group('token')
        # See if it's a struct-like format
        tokens = structparser(meta_token)
        ret_vals: List[Tuple[str, Union[str, int, None], Optional[str]]] = []
        for token in tokens:
            if keys and token in keys:
                # Don't bother parsing it, it's a keyword argument
                ret_vals.append((token, None, None))
                continue
            if token == '':
                continue
            # Match literal tokens of the form 0x... 0o... and 0b...
            m = LITERAL_RE.match(token)
            if m:
                name: str = m.group('name')
                value: str = m.group('value')
                ret_vals.append((name, None, value))
                continue
            # Match everything else:
            m1 = TOKEN_RE.match(token)
            if m1:
                name = m1.group('name')
                length = m1.group('len')
                value = m1.group('value')
            else:
                m1_short = SHORT_TOKEN_RE.match(token)
                if m1_short:
                    name = m1_short.group('name')
                    name = {'u': 'uint',
                            'i': 'int',
                            'f': 'float',
                            'b': 'bin',
                            'o': 'oct',
                            'h': 'hex'}[name]
                    length = m1_short.group('len')
                    value = m1_short.group('value')
                else:
                    # If you don't specify a 'name' then the default is 'bits':
                    name = 'bits'
                    m2 = DEFAULT_BITS.match(token)
                    if not m2:
                        raise ValueError(f"Don't understand token '{token}'.")
                    length = m2.group('len')
                    value = m2.group('value')

            if name == 'bool':
                if length is not None and length != '1':
                    raise ValueError(f"bool tokens can only be 1 bit long, not {length} bits.")
                length = '1'
            if name == 'bfloat':
                if length is not None and length != '16':
                    raise ValueError(f"bfloat tokens can only be 16 bits long, not {length} bits.")
                length = '16'
            if name in ['float8_143', 'float8_152']:
                if length is not None and length != '8':
                    raise ValueError(f"float8 tokens can only be 8 bits long, not {length} bits.")
                length = '8'
            if name in ('se', 'ue', 'sie', 'uie'):
                if length is not None:
                    raise ValueError(f"Exponential-Golomb codes (se/ue/sie/uie) can't have fixed lengths. Length of {length} was given.")
            else:
                if length is None:
                    stretchy_token = True

            if length is not None:
                # Try converting length to int, otherwise check it's a key.
                try:
                    length = int(length)
                    if length < 0:
                        raise Error
                    # For the 'bytes' token convert length to bits.
                    if name == 'bytes':
                        length *= 8
                except Error:
                    raise ValueError("Can't read a token with a negative length.")
                except ValueError:
                    if not keys or length not in keys:
                        raise ValueError(f"Don't understand length '{length}' of token.")
            ret_vals.append((name, length, value))
        # This multiplies by the multiplicative factor, but this means that
        # we can't allow keyword values as multipliers (e.g. n*uint:8).
        # The only way to do this would be to return the factor in some fashion
        # (we can't use the key's value here as it would mean that we couldn't
        # sensibly continue to cache the function's results).
        return_values.extend(tuple(ret_vals * factor))
    return_values = [tuple(x) for x in return_values]
    return stretchy_token, return_values


def expand_brackets(s: str) -> str:
    """Remove whitespace and expand all brackets."""
    s = ''.join(s.split())
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
            bracket_re = re.compile(r'(?P<factor>\d+)\*\(')
            m = bracket_re.search(s)
            if m:
                factor = int(m.group('factor'))
                matchstart = m.start('factor')
                s = s[0:matchstart] + (factor - 1) * (s[start + 1:p] + ',') + s[start + 1:p] + s[p + 1:]
            else:
                raise ValueError(f"Failed to parse '{s}'.")
    return s
