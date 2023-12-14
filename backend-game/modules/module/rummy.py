from __future__ import annotations
import random
from common import *


card_types = []
id_stack = []

card_types.append(ShowTypeGract(0, "Unknown", "The card type is unknown", "/playing-cards/0.svg"))

for suit_no, suit in enumerate(["Clubs", "Diamonds", "Hearts", "Spades"]):
    for rank_no, rank in enumerate(["Ace", *list("23456789"), "10", "Jack", "Queen", "King"]):
        id_stack.append(suit_no * 100 + rank_no + 1)
        card_types.append(ShowTypeGract(
            suit_no * 100 + rank_no + 1,
            f"{rank} of {suit}",
            f"{rank} of {suit}",
            f"/playing-cards/{suit_no * 100 + rank_no + 1}.svg"
        ))


class Player:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name
        self.cards = []


class RummyModule(Module):
    NAME = "rummy"

    def __init__(self) -> None:
        super().__init__()
        self.players: dict[int, Player] = {}
        self.central_stack = []
        self.discard_stack = []

    @staticmethod
    def create_module() -> RummyModule:
        return RummyModule()

    def process_msg(self, msg: EngMsg) -> ModMsg:
        if isinstance(msg, InitEngMsg):
            return ChangeStateModMsg(Open(), Closed("at least 2 players required"))

        elif isinstance(msg, PlayerJoinEngMsg):
            self.players[msg.player_id] = Player(
                msg.player_id, msg.player_name)

            if len(self.players) >= 4:
                return ChangeStateModMsg(Closed("No more than 4 players"), Open())
            if len(self.players) >= 2:
                return ChangeStateModMsg(Open(), Open())
            else:
                return EmptyModMsg()

        elif isinstance(msg, PlayerLeaveEngMsg):
            return EndGameModMsg(f"player {self.players[msg.player_id].name} left!")

        elif isinstance(msg, StartRoundEngMsg):
            gract_lists = self.create_lists()

            for type in card_types:
                gract_lists.broadcast(type)

            gract_lists.broadcast(
                ShowCollectionGract(-1, None, CollectionDisplay.STACK))
            gract_lists.broadcast(
                ShowCollectionGract(-2, None, CollectionDisplay.STACK))

            id_stack_clone = id_stack.copy()
            random.shuffle(id_stack_clone)

            for player in self.players.values():
                gract_lists.broadcast(ShowCollectionGract(
                    player.id, player.id, CollectionDisplay.HAND))
                player.cards = id_stack_clone[0:7]
                id_stack_clone = id_stack_clone[7:]

            self.discard_stack = [id_stack_clone.pop()]
            self.central_stack = id_stack_clone

            gract_lists.broadcast(ShowCardGract(
                *self.central_stack[-1:], 0, -1))
            gract_lists.broadcast(ShowCardGract(
                *self.discard_stack[-1:], *self.discard_stack[-1:], -2))

            for player in self.players.values():
                for card in player.cards:
                    gract_lists.send(
                        player.id, ShowCardGract(card, card, player.id))
                    gract_lists.broadcast_except(
                        player.id, ShowCardGract(card, 0, player.id)
                    )

            self.player_order = list(self.players.keys())
            self.current_idx = 0
            self.current_stage = 0

            current_player_id = self.player_order[self.current_idx]
            gract_lists.send(current_player_id, PossibleActionsGract([
                SelectCollectionPossibleAction([-1, -2]),
            ]))

            return GractModMsg(gract_lists)

        elif isinstance(msg, PlayerActionEngMsg):
            gract_lists = self.create_lists()
            current_player_id = self.player_order[self.current_idx]
            if current_player_id != msg.player_id:
                raise ValueError("invalid op")

            if self.current_stage == 0:
                if not isinstance(msg.action, SelectCollectionAction):
                    raise ValueError("invalid op")

                card_id = None

                if msg.action.collection_id == -1:
                    card_id = self.central_stack.pop()
                    gract_lists.broadcast(ShowCardGract(
                        *self.central_stack[-1:], 0, -1
                    ))

                elif msg.action.collection_id == -2:
                    card_id = self.discard_stack.pop()

                player = self.players[current_player_id]
                player.cards.append(card_id)
                gract_lists.broadcast(
                    MoveCardGract(card_id, current_player_id))
                gract_lists.send(current_player_id, RevealCardGract(
                    card_id, card_id, card_id))
                gract_lists.send(current_player_id, PossibleActionsGract([
                    SelectCardPossibleAction(player.cards)
                ]))
                self.current_stage = 1
                return GractModMsg(gract_lists)

            elif self.current_stage == 1:
                if not isinstance(msg.action, SelectCardAction):
                    raise ValueError("invalid op")

                player = self.players[current_player_id]
                player.cards = [
                    card for card in player.cards if card != msg.action.card_id]

                if check_hand(player.cards):
                    self.central_stack = []
                    self.discard_stack = []
                    for player in self.players.values():
                        player.cards = []

                    return EndRoundModMsg(f"Player {player.name} won!")

                self.discard_stack.append(msg.action.card_id)
                gract_lists.broadcast(MoveCardGract(msg.action.card_id, -2))
                gract_lists.broadcast(RevealCardGract(
                    msg.action.card_id, msg.action.card_id, msg.action.card_id))

                self.current_idx += 1
                self.current_idx = self.current_idx % len(self.player_order)
                self.current_stage = 0
                next_player_id = self.player_order[self.current_idx]

                gract_lists.send(next_player_id, PossibleActionsGract([
                    SelectCollectionPossibleAction([-1, -2])
                ]))

                return GractModMsg(gract_lists)

    def create_lists(self) -> SimpleGractLists:
        return SimpleGractLists([player_id for player_id in self.players])


def check_hand(hand: list[int]) -> bool:
    # Create a copy of the hand
    hand = hand.copy()

    # Sort the hand (used for the order check, e.g., C1, C2, C3).
    hand.sort()

    # Check for cards of the same rank
    for i in range(0, 5):
        if hand[i] is None:
            continue

        value = hand[i] % 100
        count = 1

        for j in range(i + 1, len(hand)):
            if hand[j] is None:
                continue
            if hand[j] % 100 == value:
                count += 1

        if count >= 3:
            for j in range(i, len(hand)):
                if hand[j] is None:
                    continue
                if hand[j] % 100 == value:
                    hand[j] = None

    # Order check
    start_idx = None
    end_idx = None
    prev_card = None
    for i in range(0, len(hand)):
        if hand[i] is None:
            continue
        end_idx = i

        if start_idx is None:
            start_idx = i
        elif hand[i] != prev_card + 1 or (i - start_idx) == 4:
            # This short circuit works as no element is ever revisited: this
            # means that any set we leave behind is guaranteed to be present
            # in the end result, and if the end result contains any sets,
            # it is a bad hand, so it would return false anyway
            if (i - start_idx) < 3:
                return False

            for j in range(start_idx, i):
                hand[j] = None

            start_idx = i

        prev_card = hand[i]

    # This is required in the case that the end of the hand is reached before
    # the hand can be corrected (e.g., [x, x, x, x, 301, 302, 303]), meaning
    # a valid set goes unmarked
    # NOTE: if start_idx is not None, end_idx is guaranteed not to be None either
    if start_idx is not None and (end_idx - start_idx + 1) >= 3:
        for j in range(start_idx, end_idx + 1):
            hand[j] = None

    rst = [card for card in hand if card is not None]
    return len(rst) == 0


# Export `Module`
Module = RummyModule