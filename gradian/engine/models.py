from typing import Union
from enum import Enum


class Player:
    """
    A player of the game.
    """

    def __init__(self, id: int, name: str) -> None:
        """
        Create a new player with name `name`.

        Args:
            id (int): The unique identifier of the new player.
            name (str): The name of the new player.
        """
        self._id: int = id
        self._name = name

    @property
    def id(self) -> int:
        """
        The unique identifier of the player. This field is assigned by
        the engine, ideally sequentially (though no guarantee is made).

        Returns:
            int: The unique identifier
        """
        return self._id

    @property
    def name(self) -> str:
        """
        The name of the player.

        Returns:
            str: The name of the player.
        """
        return self._name


class CardType:
    """The type of a card"""

    def __init__(self, type_id: int, name: str, desc: str, img_up: str, img_down: str) -> None:
        """
        Create a new card type.

        Args:
            type_id (int): 
            The unique identifier of the card type.
            It should be noted that two card types which share the same id
            are considered to be the same, and will thus compare equal.
            name (str): The name of the card type.
            desc (str): The description of the card type.
            img_up (str): The image URL showing the up face of the card.
            img_down (str): The image URL showing the down face of the card.
        """
        self._id = type_id
        self._name = name
        self._desc = desc
        self._img_up = img_up
        self._img_down = img_down

    @property
    def id(self) -> int:
        """
        The unique identifier of the type. This is an integer assigned by the
        card module.
        
        It should be noted that there are no restrictions on identifier assignment:
        as long as the id is unique and an integer, it can hold any value. This
        allows for the integer to be split up into groups (e.g., for playing cards,
        the upper bits can represent the suit and the lower bits the rank).

        Returns:
            int: The unique identifier used to identify/compare the card type.
        """
        return self._id

    def __eq__(self, other: object) -> bool:
        """
        Compare two card types (returns false otherwise).

        Args:
            other (object): The other card type.

        Returns:
            bool: Whether the card types are the same (i.e., whether they share the same unique identifier).
        """
        if not isinstance(other, CardType):
            return False
        return self._id == other._id

    @property
    def name(self) -> str:
        """
        The name of the card type.
        
        For example, Five of Hearts.

        Returns:
            str: The name of the card type.
        """
        return self._name

    @property
    def desc(self) -> str:
        """
        The description of the card.

        Returns:
            str: The description of the card.
        """
        return self._desc

    @property
    def img_up(self) -> str:
        """
        The URL to the image representing the up face of the card.

        Returns:
            str: A URL to an image.
        """
        return self._img_up

    @property
    def img_down(self) -> str:
        """
        The URL to the image representing the down face of the card.

        Returns:
            str: A URL to an image.
        """
        return self._img_down


class Action:
    """
    An action a player can take.
    
    For example, some cards can simply be selected whist others can be
    played against another card.
    """

    NONE = 0
    """The card cannot be used."""

    SELECT = 1
    """The card can be played as-is."""

    AGAINST = 2
    """The card can be played, but only against another card."""

    WILD = 3
    """The card is wild."""

    def __init__(self, type: int, data: object) -> None:
        """
        Create a new action.

        Args:
            type (int): The type of action that can be taken.
            data (object): The parameter affecting the action (e.g., a list of
            card types a wild card can become).
        """
        self._type = type
        self._data = data

    @property
    def type(self) -> int:
        """The type of the action."""
        return self._type

    @property
    def data(self) -> object:
        """The parameter affecting the action."""
        return self._data


class Visibility(Enum):
    """
    Visibility refers to the knowledge each player should have of a particular
    card (e.g., whether they know it exists, what type it is, etc).

    Visibility is specified for each player, as each player may have a different
    view of the situation.
    """

    HIDDEN = -1
    """The card is hidden (i.e., the player does not even know it exists)."""

    NOTVISIBLE = 0
    """The card face is not visible (e.g., it is face down)."""

    VISIBLE = 1
    """The card face (and thus its type) is visble to the player."""

    ACTIONABLE = 2
    """
    The card face is visible, and how the card can be used is also known.
    
    There are two primary reasons actionable is a separate variant and not
    implied by visible:
    
     * It may be used to determine which cards a player is able to play on
       their turn (e.g., a card marked actionable may be assumed to be
       playable).

     * The action may be calculated using the context available to a particular
       player (e.g., p1 may be able to see a card A, and be able to play
       one of their cards against A, whilst p2 is completely ignorant to
       A's existence).

    As a result, actionable should only be used if the player could actually
    play the card.
    """


class Card:
    """A particular card."""

    def __init__(self, type: CardType, action: Action, visibility: dict[int, Visibility]) -> None:
        """
        Create a new card.

        Args:
            type (CardType): The type of the card.
            action (Action): How the card can be played.
            visibility (dict[int, Visibility]): A list of the visibilities each player has of the card.
        """
        self._type = type
        self._action = action
        self._visibility = visibility

    @property
    def action(self) -> Action:
        """The action that can be taken with the card."""
        return self._action

    @property
    def type(self) -> CardType:
        """The type of the card (e.g., its name, image, etc)."""
        return self._type

    @property
    def player_visibility(self, player_id: int) -> Union[Visibility, None]:
        """The visibility a particular player has of the card."""
        return self._visibility.get(player_id)
