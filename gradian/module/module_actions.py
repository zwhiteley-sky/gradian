from .common import PlayerActionType
from abc import ABC, abstractclassmethod, abstractstaticmethod
from enum import Enum
from typing import Union


class ModAct(ABC):
    """
    An action created by the module to be acted by the client.

    For example, show card #1, move card #1 to collection #2, etc.
    """

    @abstractstaticmethod
    def action_name() -> str:
        pass

    @abstractclassmethod
    def to_dict(self) -> dict:
        pass


# A decorator to automatically derive module action classes
def mod_act(*attributes):
    def inner(cls: type) -> type:
        def init(self, *args) -> None:
            if len(args) < len(attributes):
                raise TypeError(
                    f"{cls.__name__} missing {len(attributes) - len(args)} required args: {', '.join(attributes[len(args):])}")
            elif len(args) > len(attributes):
                raise TypeError(
                    f"{cls.__name__} given too many arguments: expected {len(attributes)}, got {len(args)}")

            for attribute, arg in zip(attributes, args):
                setattr(self, attribute, arg)

        def action_name() -> str:
            return cls.ACTION_NAME

        def to_dict(self) -> dict:
            obj = dict()

            for attribute in attributes:
                obj[attribute] = getattr(self, attribute)

            return obj

        return type(cls.__name__, (ModAct,), {
            "__init__": init,
            "__doc__": cls.__doc__,
            "ACTION_NAME": cls.ACTION_NAME,
            "action_name": staticmethod(action_name),
            "to_dict": to_dict
        })

    return inner


class CollectionDisplay(Enum):
    """The ways in which a collection can be visually displayed."""

    STACK = 0
    """Show it as a stack/deck."""

    SPREAD = 1
    """Show it as a spread/hand."""


class ShowCollectionModAct(ModAct):
    """
    Show a collection to a player.

    id (int): The unique identifier of the collection -- this will be used as the collection's
              identity in future requests.

    position (int/None): The position of the collection -- the player id the collection
                         should be displayed next to, None for central positioning.

    display (CollectionDisplay): How the collection should be displayed.
    """

    ACTION_NAME = "show-collection"

    def __init__(self, id: int, position: Union[int, None], display: CollectionDisplay) -> None:
        super().__init__()
        self.id = id
        self.position = position
        self.display = display

    @staticmethod
    def action_name() -> str:
        return ShowCollectionModAct.ACTION_NAME

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "position": self.position,
            "display": self.display.value
        }


@mod_act("collection_id")
class HideCollectionModAct:
    """
    Hide a shown collection.
    
    collection_id (int): The unique identifier of the collection.
    """
    ACTION_NAME = "hide-collection"


@mod_act("id", "name", "description", "img_url")
class ShowTypeModAct:
    """
    Show a card type to a user.

    It is recommended to create an "Unknown"/"Face Down" card type to represent
    face-down cards. No native functionality exists to facilitate this behaviour.

    id (int): The unique identifier of the type (used to uniquely identify it).
    name (str): The name of the type.
    description (str): The description of the type.
    img_url (str): The URL to the image of the card's face.
    """

    ACTION_NAME = "show-type"


@mod_act("id", "type_id", "collection_id")
class ShowCardModAct:
    """
    Show a card to a player.

    NOTE: unique identifiers are used only for communicative purposes between the
    client and the module -- it doesn't matter how they are assigned.

    id (int): The unique identifier of the card.
    type_id (int): The unique identifier of the card type (must already exist).
    collection_id (int): The unique identifier of the collection (must already exist).
    """

    ACTION_NAME = "show-card"


@mod_act("card_id", "collection_id")
class MoveCardModAct:
    """
    Move a card to a new collection.

    NOTE: "exist", in this context, means communicated to the target player --
    information is communicated only as described by the card module: if a
    collection or card has not been communicated to this player, even if it
    has been communicated to others, is considered to not exist.

    card_id (int): The unique identifier of the card to move (must already exist).
    collection_id (int): The unique identifier of the collection to move the card
                         to (must already exist).
    """

    ACTION_NAME = "move-card"


@mod_act("old_id", "new_id", "new_type_id")
class RevealCardModAct:
    """
    Replace a card with a new card, and treat it as a reveal.

    This is intended to replace a face-down card with a face-up type, as if
    it is being flipped over.

    The unique identifier of the card can be modified too, provided the new unique
    identifier is indeed unique. This is done to provide card masking (e.g., to
    prevent players from tracking cards by their unique identifiers).

    The collection_id of the card stays the same.

    old_id (int): The unique identifier of the card to replace.
    new_id (int): The new unique identifier of the replaced card -- this can be the
                  same uid as the old one.
    new_type_id (int): The unique identifier of the new type of the card -- this
                       can be the same as the old one.
    """

    ACTION_NAME = "reveal-card"


@mod_act("old_id", "new_id", "new_type_id")
class ConcealCardModAct:
    """
    Replace a card with a new card, and treat it as a reveal.

    This is intended to replace a face-up card with a face-down type, as if
    it is being flipped over and hidden.

    The unique identifier of the card can be modified too, provided the new unique
    identifier is indeed unique. This is done to provide card masking (e.g., to
    prevent players from tracking cards by their unique identifiers).

    The collection_id of the card stays the same.

    The semantics of this action are exactly the same as those as RevealCardModAct:
    it is only meant to provide additional information to the client (e.g., so
    the client can make an informed decision on how to go about animating the
    flip).

    old_id (int): The unique identifier of the card to replace.
    new_id (int): The new unique identifier of the replaced card -- this can be the
                  same uid as the old one.
    new_type_id (int): The unique identifier of the new type of the card -- this
                       can be the same as the old one.
    """

    ACTION_NAME = "conceal-card"


@mod_act("card_id")
class HideCardModAct:
    """
    Hide a card from a player.

    This will invalidate the card's unique identifier -- as a result, it should
    not be used until a card with the same unique identifier has been shown again.

    NOTE: it is perfectly valid to re-purpose the card's unique identifier
    after it is hidden. Whether doing so is a good idea is dependent on your
    exact requirements.

    card_id (int): The card to hide.
    """

    ACTION_NAME = "hide-card"


class PossibleAction:
    """
    A possible action a player could perform.

    A PlayerEvent is the other half of the transaction: when a client recieves this
    action, it guarantees that, at some point in the future, a PlayerEvent specifying
    which action was taken will be sent back.
    """

    def __init__(self, type: PlayerActionType, data: object) -> None:
        """An action a player can perform.

        Args:
            type (PlayerActionType): The type of the action.
            data (object): Data to add context.
        """
        self.type = type
        self.data = data

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "data": self.data
        }


class RequestActionModAct(ModAct):
    """
    Request a player to take an individual action.

    actions (PossibleAction[]): an array of actions. Must have at least one entry.
    """

    ACTION_NAME = "move-request"

    def __init__(self, actions: list[PossibleAction]) -> None:
        super().__init__()
        self.actions = actions

    @staticmethod
    def action_name() -> str:
        return RequestActionModAct.ACTION_NAME

    def to_dict(self) -> dict:
        return {
            "actions": self.actions
        }
