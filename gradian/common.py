from abc import ABC, abstractmethod
from enum import Enum
from typing import Union


class Action(ABC):
    """
    An action performed by a player.
    """

    pass


class NextAction(Action):
    """
    The next button was hit by a player.
    """

    pass


class SelectCardAction(Action):
    """
    The player selected a card.
    """

    def __init__(self, card_id: int) -> None:
        super().__init__()
        self.card_id = card_id


class SelectCollectionAction(Action):
    """
    The player selected a collection.
    """

    def __init__(self, collection_id: int) -> None:
        super().__init__()
        self.collection_id = collection_id


class AgainstCardAction(Action):
    """
    The player selected a card to play against another card.
    """

    def __init__(self, select_card_id: int, against_card_id: int) -> None:
        super().__init__()
        self.select_card_id = select_card_id
        self.against_card_id = against_card_id


class WildCardAction(Action):
    """
    The player selected a wild card and chose the new type.
    """

    def __init__(self, card_id: int, type_id: int) -> None:
        super().__init__()
        self.card_id = card_id
        self.type_id = type_id


class PossibleAction(ABC):
    """
    A possible action the player could make.
    """

    pass


class NextPossibleAction(PossibleAction):
    """
    The player could hit the next button to progress the round.
    """

    pass


class SelectCardPossibleAction(PossibleAction):
    """
    The player could select any of these cards.
    """

    def __init__(self, card_ids: list[int]) -> None:
        super().__init__()
        self.card_ids = card_ids


class SelectCollectionPossibleAction(PossibleAction):
    """
    The player could select any of these collections.
    """

    def __init__(self, collection_ids: list[int]) -> None:
        super().__init__()
        self.collection_ids = collection_ids


class AgainstCardPossibleAction(PossibleAction):
    """
    The player could play this card against any of these other cards.
    """

    def __init__(self, select_card_id: int, against_card_ids: list[int]) -> None:
        super().__init__()
        self.select_card_id = select_card_id
        self.against_card_ids = against_card_ids


class WildCardPossibleAction(PossibleAction):
    """
    The player could play this card as a wild card and set it to any
    of these types.
    """

    def __init__(self, card_id: int, type_ids: list[int]) -> None:
        super().__init__()
        self.card_id = card_id
        self.type_ids = type_ids


class Gract(ABC):
    """
    A GRaphical ACTion.

    A graction is something the UI must do (e.g., display a card, show a collection,
    reveal a card, allow a user to select a card).
    """
    pass


class ShowTypeGract(Gract):
    """
    Reveal a card type to the player.
    """

    def __init__(
        self,
        type_id: int,
        type_name: str,
        type_desc: str,
        type_url: str
    ) -> None:
        super().__init__()
        self.type_id = type_id
        self.type_name = type_name
        self.type_desc = type_desc
        self.type_url = type_url


class CollectionDisplay(Enum):
    """
    The ways in which a collection can be displayed.
    """

    HAND = 0
    """
    As a hand of cards.
    
    NOTE: there should only be, at most, one hand collection per player.
    """

    SPREAD = 1
    """
    A spread of cards.
    """

    STACK = 2
    """
    A stack of cards. This would be used to display a deck of cards.
    """


class ShowCollectionGract(Gract):
    """
    Show a collection to the player.
    """

    def __init__(
        self,
        collection_id: int,
        player_id: Union[int, None],
        collection_display: CollectionDisplay
    ) -> None:
        super().__init__()
        self.collection_id = collection_id
        self.player_id = player_id
        self.collection_display = collection_display


class HideCollectionGract(Gract):
    """
    Hide a collection from a player.

    NOTE: the collection must have already been shown to the player.
    """

    def __init__(self, collection_id: int) -> None:
        super().__init__()
        self.collection_id = collection_id


class ShowCardGract(Gract):
    """
    Show a card to the player.

    NOTE: both the type and the collection must have already been shown to the
    player.
    """

    def __init__(self, card_id: int, type_id: int, collection_id: int) -> None:
        super().__init__()
        self.card_id = card_id
        self.type_id = type_id
        self.collection_id = collection_id


class MoveCardGract(Gract):
    """
    Move a card from one (shown) collection to another (shown) collection.
    """

    def __init__(self, card_id: int, collection_id: int) -> None:
        super().__init__()
        self.card_id = card_id
        self.collection_id = collection_id


class RevealCardGract(Gract):
    """
    Reveal a card to the player.

    Both the card and the new type must have already been shown to the player.

    The purpose of this graction is to allow a flipping effect to be used (e.g.,
    for turning a card over). This is also the reason it allows the type of
    the card to be changed: the events API does not have native support for
    face-down cards, so this must be emulated with a face-down type.

    The reason it allows the unique identifier of the card to be modified is
    to prevent card tracking (whereby a malicious player attempts to keep
    cards shown by tracking their unique identifiers -- by changing the unique
    identifier, we can mix up the cards to prevent this, although doing so
    should only really be used in competitive contexts).

    The new ids can be the same as the old ids.
    """

    def __init__(self, old_card_id: int, new_card_id: int, new_type_id: int) -> None:
        super().__init__()
        self.old_card_id = old_card_id
        self.new_card_id = new_card_id
        self.new_type_id = new_type_id


class ConcealCardGract(Gract):
    """
    Conceal a card from the player.

    This is exactly the same, functionally, as RevealCardGract -- the only real
    difference between the two is semantics: this graction implies the card is
    being turned face-down, whereas RevealCardGract implies it is being turned
    face-up.
    """

    def __init__(self, old_card_id: int, new_card_id: int, new_type_id: int) -> None:
        super().__init__()
        self.old_card_id = old_card_id
        self.new_card_id = new_card_id
        self.new_type_id = new_type_id


class HideCardGract(Gract):
    """
    Hide a card from the player.

    NOTE: the card must have been previously shown to the player.
    """

    def __init__(self, card_id: int) -> None:
        super().__init__()
        self.card_id = card_id


class PossibleActionsGract(Gract):
    """
    Inform a player of the possible actions they are able to make.

    NOTE: these actions should not overlap (i.e., a wild card should
    not also be selectable). Actions are conservatively assumed to
    be mutually exclusive, meaning once a player selects one of the actions,
    all other actions are immediately discarded.
    """

    def __init__(self, possible_actions: list[PossibleAction]) -> None:
        super().__init__()
        self.possible_actions = possible_actions


class GractLists(ABC):
    @abstractmethod
    def __iter__(self):
        pass


class SimpleGractLists(GractLists):
    def __init__(self, player_ids: list[int]) -> None:
        super().__init__()
        self.gract_lists = {
            player_id: [] for player_id in player_ids
        }

    def __iter__(self):
        return filter(lambda item : len(item[1]) != 0, self.gract_lists.items())

    def send(self, player_id: int, gract: Gract):
        self.gract_lists[player_id].append(gract)

    def broadcast(self, gract: Gract):
        for list in self.gract_lists.values():
            list.append(gract)
