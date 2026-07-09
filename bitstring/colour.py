from __future__ import annotations

import os


def should_use_color(color: bool | None) -> bool:
    if color is not None:
        return bool(color)
    return not bool(os.getenv('NO_COLOR'))


class Colour:
    __slots__ = ('blue', 'purple', 'green', 'off')

    def __init__(self, use_colour: bool) -> None:
        if use_colour:
            self.blue = '\033[34m'
            self.purple = '\033[35m'
            self.green = '\033[32m'
            self.off = '\033[0m'
        else:
            self.blue = self.purple = self.green = self.off = ''
