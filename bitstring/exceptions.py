class ReadError(IndexError):
    """Reading or peeking past the end of a bitstring."""


InterpretError = ValueError
"""Inappropriate interpretation of binary data."""


CreationError = ValueError
"""Inappropriate argument during bitstring creation."""
