from abc import ABC
from common import *


class ModMsg(ABC):
    """
    A message from the module to the engine.
    """

    pass


class EmptyModMsg(ModMsg):
    """
    There is nothing to do.
    """

    pass


class Open:
    """
    An action is able to be performed.
    """

    pass


class Closed:
    """
    An action is not able to be performed.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason


class ChangeStateModMsg(ModMsg):
    """
    Change the state of the card game (e.g., whether it is accepting new players,
    whether it can be started).
    """

    def __init__(self, join_mode: Union[Open, Closed], start_mode: Union[Open, Closed]) -> None:
        super().__init__()
        self.join_mode = join_mode
        self.start_mode = start_mode


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