from abc import ABC


class DirectPaction:
    """
    A possible direct action (an action which is not associated
    with any particular card or collection -- these actions will often
    be represented as a button).
    """

    def __init__(self, reference: int, text: str) -> None:
        """
        Create a new direct action possibility.

        Args:
            reference (int): A reference of the direct action which is communicated
            upon select (i.e., if a user selects this action, only the reference will
            be communicated). As a result, this should be unique to all other direct
            actions, although this is not required.
            text (str): Text describing the action.
        """

        self.reference = reference
        self.text = text


class CollPaction(ABC):
    """
    A possible collection action.
    """

    pass


class EmptyCollPaction(CollPaction):
    """
    There is no action that can be performed with this collection.
    """

    pass


class SelectCollPaction(CollPaction):
    """
    The collection can be selected.
    """

    pass


class CardPaction(ABC):
    """
    A possible action involving a particular card.
    """

    pass


class EmptyCardPaction(CardPaction):
    """
    No action can be performed with the card.
    """

    pass


class SelectCardPaction(CardPaction):
    """
    The card can be selected.
    """

    pass


class AgainstCardPaction(CardPaction):
    """
    The card can be played against another card.
    """

    def __init__(self, against_ids: list[int]) -> None:
        """
        Create a new against card paction.

        Args:
            against_ids (list[int]): The list of card identifiers this card
            can be played against.
        """

        super().__init__()
        self.against_ids = against_ids


class WildCardPaction(CardPaction):
    """
    The card can be played wildly (i.e., transformed into a card of a different
    type).

    It should be noted that this paction is like any other: it does not do anything
    directly, it just communicates that it has been played wildly to the Card Module,
    which then bears the burden of responsibility of actually changing the card's type.
    """

    def __init__(self, type_ids: list[int]) -> None:
        """
        Create a new wild card paction.

        Args:
            type_ids (list[int]): The list of type identifiers which the card be
            be transformed into.
        """

        super().__init__()
        self.type_ids = type_ids


class Pactions:
    """
    A list of possible actions (shortened to pactions) which a player can perform.
    """

    def __init__(
        self,
        direct_pactions: list[DirectPaction],
        coll_pactions: dict[int, CollPaction],
        card_pactions: dict[int, CardPaction]
    ) -> None:
        """
        Create a new list of pactions.

        Args:
            direct_pactions (list[DirectPaction]): The direct pactions that can be performed.
            coll_pactions (dict[int, CollPaction]): A dictionary of all collection ids and their
            associated paction.
            card_pactions (dict[int, CardPaction]): A dictionary of all cards ids and
            their associated pactions.
        """

        self.direct_pactions = direct_pactions
        self.coll_pactions = coll_pactions
        self.card_pactions = card_pactions


class Action(ABC):
    pass


class DirectAction(Action):
    def __init__(self, reference: int) -> None:
        super().__init__()
        self.reference = reference


class SelectCollAction(Action):
    def __init__(self, collection_id: int) -> None:
        super().__init__()
        self.collection_id = collection_id


class SelectCardAction(Action):
    def __init__(self, card_id: int) -> None:
        super().__init__()
        self.card_id = card_id


class AgainstCardAction(Action):
    def __init__(self, select_card_id: int, against_card_id: int) -> None:
        super().__init__()
        self.select_card_id = select_card_id
        self.against_card_id = against_card_id


class WildCardAction(Action):
    def __init__(self, card_id: int, type_id: int) -> None:
        super().__init__()
        self.card_id = card_id
        self.type_id = type_id
