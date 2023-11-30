from abc import ABC, abstractstaticmethod


class Event(ABC):
    """An event."""
    @abstractstaticmethod
    def event_name() -> str:
        pass


# A decorator to automatically derive module action classes
def event(*attributes):
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

        def event_name() -> str:
            return cls.EVENT_NAME

        return type(cls.__name__, (Event,), {
            "__init__": init,
            "__doc__": cls.__doc__,
            "EVENT_NAME": cls.EVENT_NAME,
            "event_name": staticmethod(event_name),
        })

    return inner


@event()
class CreateGameEvent:
    """A game has been created."""

    EVENT_NAME = "create-game"


@event("id", "name")
class JoinGameEvent:
    """
    A player has joined the game.

    Unlike other things, the player id is externally determined.

    id (int): The unique identifier of the player.
    name (str): The name of the player.
    """

    EVENT_NAME = "join-game"


@event()
class StartGameEvent:
    """A request from the host to start the game."""

    EVENT_NAME = "start-game"


@event("id", "type", "data")
class PlayerEvent:
    """
    An event by a player.

    id (int): The unique identifier of the player who caused the event.
    type (PlayerActionType): The type of action the player took.
    data (object): The data associated with the action (e.g., the unique identifier).
    """
    EVENT_NAME = "player-event"
