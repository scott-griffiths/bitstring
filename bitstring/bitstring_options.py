from __future__ import annotations

import os


class Options:
    """Internal class to create singleton module options instance."""

    _instance = None

    def __init__(self):
        if hasattr(self, "_initialised"):
            return
        self._bytealigned = False

        self.no_color = False
        no_color = os.getenv('NO_COLOR')
        self.no_color = True if no_color else False
        self._initialised = True

    def __repr__(self) -> str:
        attributes = {attr: getattr(self, attr) for attr in dir(self) if not attr.startswith('_') and not callable(getattr(self, attr))}
        return '\n'.join(f"{attr}: {value!r}" for attr, value in attributes.items())

    @property
    def bytealigned(self) -> bool:
        return self._bytealigned

    @bytealigned.setter
    def bytealigned(self, value: bool) -> None:
        self._bytealigned = bool(value)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


class Colour:
    def __new__(cls, use_colour: bool) -> Colour:
        x = super().__new__(cls)
        if use_colour:
            cls.blue = '\033[34m'
            cls.purple = '\033[35m'
            cls.green = '\033[32m'
            cls.off = '\033[0m'
        else:
            cls.blue = cls.purple = cls.green = cls.off = ''
        return x
