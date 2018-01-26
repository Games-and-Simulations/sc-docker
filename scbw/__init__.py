from .game import run_game, GameResult, GameArgs
from .error import DockerException, GameException
VERSION = '0.2a21'
__all__ = [
    'run_game', 'GameResult', 'GameArgs', 'GameException', 'DockerException'
]
