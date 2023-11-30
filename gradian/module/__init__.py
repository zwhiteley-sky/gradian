from enum import Enum


class PlayerActionType(Enum):
    """
    The actions a player can perform.
    """

    NEXT = 0
    """They can click the next button."""

    SELECT = 1
    """They can select a card (id provided as data)."""

    AGAINST = 2
    """
    They can select a card and play it against another card.
    
    Array provided as data: 0th entry is the selectable card id,
    all subsequent entries are against candidates.
    """

    WILD = 3
    """
    The card is wild and can have its type changed.
    
    Array provided as data: 0th entry is the selectable card id,
    all subsequent entries type ids. NOTE: all type ids must have
    been shown to the player prior.
    """

    SELECT_COLLECTION = 4
    """
    The player can select a collection (usually a deck in the centre).

    The collection id is provided as data.
    """
