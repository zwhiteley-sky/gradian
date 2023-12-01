from .module import *
from abc import ABC, abstractclassmethod


class Channel(ABC):
    """
    An asynchronous channel used to send action lists.
    """

    @abstractclassmethod
    async def send(self, actions: list[ModAct]):
        """
        Send an action list over the channel.
        """
        pass


class Player:
    """A player's information."""

    def __init__(self, id: int, name: str, channel: Channel) -> None:
        self.id = id
        self.name = name
        self.channel = channel


class ModuleImplError(Exception):
    """An error in a module's implementation."""
    pass


class Engine:
    """
    An asynchronous engine for running a card module.

    This engine acts as a thin-layer over the card module's raw API, managing
    only essential information (e.g., player information, game status).
    """

    def __init__(self, card_module: type[Module]) -> None:
        """
        Create a new engine for the card module provided.

        Args:
            card_module (type[Module]): The card module to instantiate.

        Raises:
            ModuleImplError: If the card module is incorrectly implemented.
        """
        self.players: list[Player] = []
        self.instance: Module = card_module.create_module()
        action_lists = self.instance.process_event(CreateGameEvent())
        if len(action_lists) != 0:
            raise ModuleImplError(
                "the CreateGameEvent should return no actions")

    async def add_player(self, name: str, channel: Channel) -> int:
        """
        Add a player to the game.

        Args:
            name (str): The name of the card module.
            channel (Channel): The channel over which to send action lists.

        Returns:
            int: The newly created unique identifier of the player.
        """
        id = len(self.players)
        self.players.append(Player(id, name, channel))

        await self.send_event(JoinGameEvent(id, name))
        return id

    async def start_game(self):
        """
        Start the card game.
        """
        await self.send_event(StartGameEvent())

    async def player_act_next(self, player_id: int):
        """
        Notify that a player hit the next button.

        Args:
            player_id (int): The unique identifier of the player.
        """

        await self.send_event(PlayerEvent(
            player_id,
            PlayerActionType.NEXT,
            None
        ))

    async def player_act_select(self, player_id: int, card_id: int):
        """
        Notify that a player selected a card.

        Args:
            player_id (int): _description_
            card_id (int): _description_
        """

        await self.send_event(PlayerEvent(
            player_id,
            PlayerActionType.SELECT,
            card_id
        ))

    async def player_act_against(self, player_id: int, select_id: int, against_id: int):
        """
        Notify that a player played one card against another.

        Args:
            player_id (int): The unique identifier of the player.
            select_id (int): The unique identifier of the card they selected.
            against_id (int): The unique identifier of the card they played it against.
        """

        await self.send_event(PlayerEvent(
            player_id,
            PlayerActionType.AGAINST,
            [select_id, against_id]
        ))

    async def player_act_wild(self, player_id: int, card_id: int, type_id: int):
        """
        Notify that a player played a card wildly.

        Args:
            player_id (int): The unique identifier of the player.
            card_id (int): The unique identifier of the card they chose to play wildly.
            type_id (int): The unique identifier of the type they chose.
        """

        await self.send_event(PlayerEvent(
            player_id,
            PlayerActionType.WILD,
            [card_id, type_id]
        ))

    async def player_act_sel_coll(self, player_id: int, collection_id: int):
        """
        Notify that a player selected a collection to play.

        Args:
            player_id (int): The unique identifier of the player.
            collection_id (int): The unique identifier of the collection.
        """

        await self.send_event(PlayerEvent(
            player_id,
            PlayerActionType.SELECT_COLLECTION,
            collection_id
        ))

    async def send_event(self, event: Event):
        """
        Send an event to the underlying module.

        Args:
            event (Event): The event to send.

        Raises:
            ModuleImplError: If the module is implemented incorrectly.
        """

        action_lists = self.instance.process_event(event)
        for player_id, action_list in action_lists:
            if player_id >= len(self.players):
                raise ModuleImplError("card module returned invalid player id")

            player = self.players[player_id]
            if len(action_list) != 0:
                await player.channel.send(action_list)
