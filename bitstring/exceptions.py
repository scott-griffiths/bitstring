class ReadError(IndexError):
    """Reading or peeking past the end of a bitstring."""


class ByteAlignError(ValueError):
    """Whole-byte position or length needed."""


InterpretError = ValueError
"""Inappropriate interpretation of binary data."""


CreationError = ValueError
"""Inappropriate argument during bitstring creation."""
