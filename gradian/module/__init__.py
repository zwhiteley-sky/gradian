from abc import ABC, abstractclassmethod, abstractstaticmethod
from ..common import *
from .engine_message import *
from .module_message import *


class Module(ABC):
    """
    The base class of a card module.
    """

    @abstractstaticmethod
    def create_module() -> any:
        """
        Create an instance of the card module.
        """
        pass

    @abstractclassmethod
    def process_msg(self, eng_msg: EngMsg) -> ModMsg:
        """
        Process a message from the engine.

        Args:
            event (Event): The message to process.

        Returns:
            list[ModMsg]: The module messages to respond with.
        """
        pass
