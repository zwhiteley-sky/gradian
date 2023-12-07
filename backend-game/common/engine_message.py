from abc import ABC
from .common import *


class EngMsg(ABC):
    """
    A message from an engine to the module.

    Engine refers to anything which runs a module.
    """
    pass


class InitEngMsg(EngMsg):
    """
    A dummy message used to retrieve the initialisation settings of the
    module (e.g., whether it should be open to new players, etc).

    This message should only be sent once, before any other message has been sent.
    """

    pass


class PlayerJoinEngMsg(EngMsg):
    """
    A player has joined the game.

    NOTE: this must only be sent if the game is currently accepting
    new players.
    """

    def __init__(self, player_id: int, player_name: str) -> None:
        super().__init__()
        self.player_id = player_id
        self.player_name = player_name


class PlayerLeaveEngMsg(EngMsg):
    """
    A player has left the game.
    """

    def __init__(self, player_id: int) -> None:
        super().__init__()
        self.player_id = player_id


class StartRoundEngMsg(EngMsg):
    """
    Start a round of the game.

    NOTE: this must only be sent if the round can be started, and it has not already
    been started.
    """

    pass


class EndRoundEngMsg(EngMsg):
    """
    End the current round of the game.

    NOTE: this must only be sent if the round has been started and has not ended.
    """

    pass


class PlayerActionEngMsg(EngMsg):
    """
    A player has performed an action.

    NOTE: this must only be sent if the round has started.
    """

    def __init__(self, player_id: int, action: Action) -> None:
        super().__init__()
        self.player_id = player_id
        self.action = action
