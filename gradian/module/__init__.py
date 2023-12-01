from abc import ABC, abstractclassmethod, abstractstaticmethod
from .common import *
from .module_events import *
from .module_actions import *


class ActionLists(ABC):
    @abstractclassmethod
    def __len__(self):
        pass

    @abstractclassmethod
    def __iter__(self):
        pass


class SimpleActionLists(ActionLists):
    """
    The actions to be performed by a module.
    """

    def __init__(self, player_ids: list[int]) -> None:
        self.player_lists = {
            player_id: [] for player_id in player_ids
        }

    def send(self, player_id: int, action: ModAct):
        """
        Send an action to an individual player. Actions are processed
        in the order which they are sent.

        Args:
            player_id (int): The unique identifier of the player to send it to.
            action (ModAct): The action to send.

        Raises:
            ValueError: If the player id does not exist.
        """

        player_list = self.player_lists[player_id]

        if player_list is None:
            raise ValueError("player_id is invalid")

        player_list.append(action)

    def broadcast(self, action: ModAct):
        """
        Broadcast an action to all players. This is the same as called
        `send` for each individual player.

        Args:
            action (ModAct): The action to send.
        """

        for player_list in self.player_lists.values():
            player_list.append(action)

    def broadcast_except(self, excl: list[int], action: ModAct):
        for player_id in self.player_lists:
            if player_id in excl:
                continue
            
            self.send(player_id, action)

    def __len__(self):
        return len(self.player_lists)

    def __iter__(self):
        return iter(self.player_lists.items())


class ModuleError(Exception):
    pass


class Module(ABC):
    """
    The base class of a card module.
    """

    @abstractstaticmethod
    def create_module() -> any:
        """Create a fresh instance of the module."""
        pass

    @abstractclassmethod
    def process_event(self, event: Event) -> ActionLists:
        """
        Process an event from a client.

        Args:
            event (Event): The event to process.

        Returns:
            ActionList: The list of actions to send to each player.
        """
        pass
