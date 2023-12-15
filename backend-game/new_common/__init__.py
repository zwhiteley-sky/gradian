from __future__ import annotations

from abc import ABC, abstractstaticmethod, abstractclassmethod
from .actions import *
from enum import Enum
from .gractions import *
from typing import Tuple, Union


class PlayerCountResultType(Enum):
    TOO_FEW_PLAYERS = -1
    """
  The game cannot be started, but can be joined by new players.
  """

    OPEN = 0
    """
  The game is fully open: it can be both joined and started.

  This should **not** be returned if the game has reached its maximum
  number of players, as it implies that adding more players will eventually
  return another `OPEN` or `PLAYERS_MAX`.
  """

    NO_START = 1
    """
  The game cannot be started, but can be joined by new players.
  

  This implies that enough players joining/leaving will eventually result in
  the game being startable (i.e., an `OPEN` or `PLAYERS_MAX`).
  
  Do not use this response to indicate the game is at is below/above its
  minimum/maximum player count. See `TOO_MANY_PLAYERS` and `TOO_FEW_PLAYERS`.
  """

    PLAYERS_MAX = 2
    """
  The game has reached its maximum number of players, and should not be joined
  by any more. (i.e., the game can be started but not joined.)
  """

    TOO_MANY_PLAYERS = 3
    """
  The game has exceeded its maximum player count and cannot be started or joined
  until enough players leave. This can only be returned after a `PLAYERS_MAX`.
  """


class PlayerCountResult:
    """
    The result of the `check_players` call.
    """

    def __init__(self, type: PlayerCountResultType, reason: Union[str, None]) -> None:
        """
        The result of a call to `check_players`.

        Args:
            type (PlayerCountResultType): The result type (e.g., its open and close states).
            reason (Union[str, None]): The reason for this state being returned.
        """

        self.type = type
        self.reason = reason


class Player:
    """
    A player within a game.
    """

    def __init__(self, id: int, name: str) -> None:
        """
        Create a new player (this should not be run by a Card Module).

        Args:
            id (int): The unique identifier of the player. Generation of this identifier
            is entirely controlled by the Engine and is completely opaque to the
            Card Module (besides being an integer): the only guarantee provided
            is that it is unique to all other players in the current game.
            name (str): The name of the player.
        """

        self.id = id
        self.name = name


class GractList:
    """
    A list of gractions for a particular player, as well as the possible
    actions they can take.
    """

    def __init__(self, gracts: list[Gract], pactions: Pactions) -> None:
        self.gracts = gracts
        self.pactions = pactions


class GractLists(ABC):
    """
    A list of `GractList`s, containing the `GractList` for each player.
    """

    pass


class SimpleGractLists(GractLists):
    def __init__(self, players: list[Player]) -> None:
        super().__init__()
        self.gract_lists = {
            player.id: [] for player in players
        }

    def __iter__(self):
        return filter(lambda item: len(item[1]) != 0, self.gract_lists.items())

    def send(self, player_id: int, gract: Gract):
        self.gract_lists[player_id].append(gract)

    def broadcast(self, gract: Gract):
        for list in self.gract_lists.values():
            list.append(gract)

    def broadcast_except(self, except_id: int, gract: Gract):
        for player_id, list in self.gract_lists.items():
            if player_id == except_id:
                continue
            list.append(gract)


class ProcessResult(ABC):
    """
    The result of `process_action`.
    """

    pass


class ContinueProcessResult(ProcessResult):
    """
    Continue with the round (i.e., the round has yet to be won/lost/tied).
    """

    def __init__(self, gract_lists: GractLists) -> None:
        """
        Continue with the round.

        Args:
            gract_lists (GractLists): A fresh set of gractions to be sent out.
        """

        super().__init__()
        self.gract_lists = gract_lists


class EndRoundProcessResult(ProcessResult):
    """
    The round is finished and ended (implies `start_round` can be called again).
    """

    def __init__(
        self,
        gract_lists: GractLists,
        round_scoreboard: list[Tuple[int, str]],
        game_scoreboard: list[Tuple[int, str]]
    ) -> None:
        """
        The round has ended.

        Args:
            gract_lists (GractLists): The final set of gractions, which may or may not
            be ignored. This is used to show the "winning move".
            round_scoreboard (list[Tuple[int, str]]): The scoreboard for the round
            (a list, from highest to lowest, containing each player id and the message
            to display in relation to them). For example, [(1, "15 points"), (0, "-1 points")].
            game_scoreboard (list[Tuple[int, str]]): Like the `round_scoreboard`, but for
            the entire game.
        """

        super().__init__()
        self.gract_lists = gract_lists
        self.round_scoreboard = round_scoreboard
        self.game_scoreboard = game_scoreboard


class EndGameProcessResult(ProcessResult):
    """
    The game has ended and there are no more rounds to play.
    """

    def __init__(self, gract_lists: GractLists, game_scoreboard: list[Tuple[int, str]]) -> None:
        """
        The game has ended.

        Args:
            gract_lists (GractLists): The final set of gractions, which may or may not
            be ignored. This is used to show the "winning move" to the players.
            game_scoreboard (list[Tuple[int, str]]): The final scoreboard.
        """

        super().__init__()
        self.gract_lists = gract_lists
        self.game_scoreboard = game_scoreboard


class BaseModule(ABC):
    """
    The base class of all Card Module classes.
    """

    @abstractstaticmethod
    def check_players(player_count: int) -> PlayerCountResult:
        """
        Provides game join and start information based on the number of players
        in the lobby:

         * Whether the game can be started with the current number of players.
         * Whether additional players should be allowed to join the lobby (i.e.,
           if a game is at its maximum player count, additional players should not
           be given access).
         * How to go about bringing the game to a playable state (e.g., by having
           more players join to fulfil the minimum player requirement).

        This function should be deterministic, meaning the same player_count should
        return exactly the same response.

        Args:
            player_count (int): The number of players in the lobby.

        Returns:
            PlayerCountResult: The join and start states of the game.
        """

        pass

    @abstractstaticmethod
    def create_game(players: list[Player]) -> BaseModule:
        """
        Create a new game.

        The Engine must ensure the number of players is valid for the game
        to start (it usually achieves this through a prior call to `check_players`).

        Args:
            players (list[Player]): The list of the players in the game. This
            cannot be changed for the duration of the game.

        Returns:
            BaseModule: The new game instance.
        """

        pass

    @abstractclassmethod
    def start_round(self) -> GractLists:
        """
        Start a round of the game. 

        Games are split into rounds, where each round is expected to
        contribute to some overall score.

        Rounds have the following properties:

         * The players in the game are **always** the same -- if an Engine
           wishes to add, remove, or change a player, it has to end and restart
           the game.

         * Only one round can be started at a time.

         * Each round is separate: the gractions of a previous round are forgotten
           entirely when a new round is started.

        Returns:
            GractLists: The initial graction lists of the game (e.g., to set it up).
        """

        pass

    @abstractclassmethod
    def process_action(player_id: int, action: Action) -> ProcessResult:
        """
        Process an action complete by a player.

        The Engine is required to ensure the action is valid (i.e., part of
        the previously communicated pactions) before calling this method.

        Args:
            player_id (int): The unique identifier of the player who made the action.
            action (Action): The action itself.

        Returns:
            ProcessResult: The result of the action.
        """

        pass
