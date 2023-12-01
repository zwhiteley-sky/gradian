import unittest
import random
from asyncio import Queue
from .engine import *
from .module import *


class TestChannel(Channel):
    def __init__(self, queue: Queue) -> None:
        super().__init__()
        self.queue = queue

    async def send(self, actions: list[ModAct]):
        await self.queue.put(actions)


class PlayerInfo:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class TestModule(Module):
    def __init__(self) -> None:
        super().__init__()
        self.players = {}
        self.started = False
        self.selected_player = None

    @staticmethod
    def create_module() -> any:
        return TestModule()

    def process_event(self, event: Event) -> ActionLists:
        if isinstance(event, CreateGameEvent):
            return SimpleActionLists([])

        elif isinstance(event, JoinGameEvent):
            if self.started:
                raise ModuleError("players cannot join after game has started")

            self.players[event.id] = PlayerInfo(event.id, event.name)
            return SimpleActionLists([player.id for player in self.players.values()])

        elif isinstance(event, StartGameEvent):
            self.started = True
            action_lists = SimpleActionLists(
                [player.id for player in self.players.values()])

            # Send the card types to each player
            action_lists.broadcast(ShowTypeModAct(
                0,
                "Unknown",
                "This card is face down",
                "url"
            ))
            for i in range(0, len(self.players)):
                action_lists.broadcast(ShowTypeModAct(
                    i + 1,
                    str(i + 1),
                    f"a card with {i + 1} value",
                    "url"
                ))
                action_lists.broadcast(ShowCollectionModAct(
                    i, i, CollectionDisplay.SPREAD
                ))

            offset = random.randint(0, len(self.players) - 1)

            # For each player, show them their card
            for player in self.players.values():
                type_id = (player.id + offset) % len(self.players) + 1
                action_lists.send(player.id, ShowCardModAct(
                    type_id,
                    type_id,
                    player.id
                ))
                action_lists.broadcast_except([player.id], ShowCardModAct(
                    type_id,
                    0,
                    player.id
                ))

            start_player = random.randint(0, len(self.players) - 1)
            action_lists.send(start_player, RequestActionModAct([
                PossibleAction(PlayerActionType.SELECT,
                               (start_player + offset) % len(self.players) + 1)
            ]))
            self.selected_player = start_player

            return action_lists

        elif isinstance(event, PlayerEvent):
            if event.type != PlayerActionType.SELECT:
                raise ModuleError("invalid action type")

            if event.id != self.selected_player:
                return

            action_lists = SimpleActionLists(
                [player_id for player_id in self.players])
            action_lists.broadcast(HideCardModAct(event.data))
            return action_lists


class EngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_engine(self):
        engine = Engine(TestModule)
        player_one = Queue()
        player_two = Queue()
        player_three = Queue()
        await engine.add_player("p1", TestChannel(player_one))
        await engine.add_player("p2", TestChannel(player_two))
        await engine.add_player("p3", TestChannel(player_three))

        await engine.start_game()

        action_list_one = await player_one.get()
        action_list_two = await player_two.get()
        action_list_three = await player_three.get()
        self.assertGreaterEqual(len(action_list_one), 1 + 3 + 3 + 3)
        self.assertGreaterEqual(len(action_list_two), 1 + 3 + 3 + 3)
        self.assertGreaterEqual(len(action_list_three), 1 + 3 + 3 + 3)

        action_lists = [action_list_one, action_list_two, action_list_three]

        for idx, action_list in enumerate(action_lists):
            found = False

            for action in action_list:
                if not isinstance(action, RequestActionModAct):
                    continue

                card_id = action.actions[0].data
                await engine.player_act_select(idx, card_id)

            if found:
                break

        action_list_one = await player_one.get()
        action_list_two = await player_two.get()
        action_list_three = await player_three.get()
        self.assertEqual(len(action_list_one), 1)
        self.assertEqual(len(action_list_two), 1)
        self.assertEqual(len(action_list_three), 1)


if __name__ == "__main__":
    unittest.main()
