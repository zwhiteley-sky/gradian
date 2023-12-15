from abc import ABC
from typing import Union
from enum import Enum


class Gract(ABC):
    """
    A GRaphical ACTion.

    This is an action which a client is required to perform. Includes things
    like showing a card to a particular player, or revealing a card's type
    to a player.
    """

    pass


class ShowTypeGract(Gract):
    """
    Reveal a card type to the player.

    Types cannot be hidden once revealed, except by changing the round.
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

    It is unspecified as to what happens to the cards associated with the
    collection when it is hidden and, as a result, all cards associated with
    the collection should either be hidden or moved before the collection
    itself is hidden.
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
