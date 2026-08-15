class ReadError(ValueError):
    """Reading or peeking past the end of a bitstring."""


class InterpretationError(AttributeError, ValueError):
    """A bitstring's length has no interpretation as the dtype asked for.

    It subclasses AttributeError so that hasattr() and getattr() with a default see a
    property that simply isn't there for a bitstring of this length, and ValueError so
    that code catching that still works.
    """
