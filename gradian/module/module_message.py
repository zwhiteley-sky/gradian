from abc import ABC
from ..common import *


class ModMsg(ABC):
    """
    A message from the module to the engine.
    """

    pass


class AcceptPlayersModMsg(ModMsg):
    """
    The module is currently accepting players.
    """

    pass


class RejectPlayersModMsg(ModMsg):
    """
    The module is currently closed to new players.
    """

    def __init__(self, reason: str) -> None:
        super().__init__()
        self.reason = reason


class CanStartModMsg(ModMsg):
    """
    A new round of the game can be started.
    """

    pass


class CannotStartModMsg(ModMsg):
    """
    A round of the game cannot be started.
    """

    def __init__(self, reason: str) -> None:
        super().__init__()
        self.reason = reason


class EndRoundModMsg(ModMsg):
    """
    End the current round of the game.

    This resets the entire game (i.e., all gractions are cleared from the
    client). The only thing that stays the same are the game's openness
    settings and the current players.

    NOTE: this can be used for multiple reasons: when the game ends, if a client
    goes rogue, etc.
    """

    def __init__(self, reason: str) -> None:
        super().__init__()
        self.reason = reason


class EndGameModMsg(ModMsg):
    """
    End the entire game.

    NOTE: this should be done in cases whereby invariants are broken (e.g., if
    a player attempts to join when the game is not open, if a client roguely
    sends an action when it is not their turn, etc).
    """

    def __init__(self, reason: str) -> None:
        super().__init__()
        self.reason = reason


class GractModMsg(ModMsg):
    """
    Send a list of graphical actions to a player.
    """

    def __init__(self, gract_lists: GractLists) -> None:
        super().__init__()
        self.gract_lists = gract_lists