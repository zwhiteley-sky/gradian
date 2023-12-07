from __future__ import annotations

import json
import unittest

from asyncio import Queue
from gradian.engine import EngineManager
from common import *
from typing import Union


class MockWebSocket:
    def __init__(self, sender: Queue[str, None], recver: Queue[str, None]) -> None:
        self.sender = sender
        self.recver = recver

    async def recv(self) -> str:
        msg = await self.recver.get()
        if msg is None: raise ValueError("connection closed")
        return msg

    async def send(self, msg):
        await self.sender.put(msg)

    async def close(self):
        await self.sender.put(None)
        await self.recver.put(None)


class MockPlayer:
    def __init__(self) -> None:
        self.recver = Queue()
        self.sender = Queue()
        
        # NOTE: the order is deliberately inverted: their sender is
        # our receiver, and vice-versa
        self.ws = MockWebSocket(self.recver, self.sender)

    async def recv(self) -> Union[str, None]:
        return await self.recver.get()

    async def send(self, msg: str):
        await self.sender.put(msg)

    async def close(self):
        await self.sender.put(None)
        await self.recver.put(None)


class MockModule(Module):
    def __init__(self) -> None:
        super().__init__()
        self.players = 0

    @staticmethod
    def create_module() -> MockModule:
        return MockModule()

    def process_msg(self, msg: EngMsg) -> ModMsg:
        # Fairly simple mock card game which does basically nothing
        if isinstance(msg, InitEngMsg):
            return ChangeStateModMsg(Open(), Closed("2 players required"))

        elif isinstance(msg, PlayerJoinEngMsg):
            self.players += 1
            if self.players ==  2: return ChangeStateModMsg(Closed("2 players max"), Open())
            else: return EmptyModMsg()

        elif isinstance(msg, StartRoundEngMsg):
            simple_gracts = SimpleGractLists([0, 1])
            simple_gracts.broadcast(ShowTypeGract(0, "a card", "", ""))
            simple_gracts.broadcast(ShowTypeGract(1, "wild 1", "", ""))
            simple_gracts.broadcast(ShowTypeGract(2, "wild 2", "", ""))
            simple_gracts.broadcast(ShowCollectionGract(0, 0, CollectionDisplay.HAND))
            simple_gracts.broadcast(ShowCollectionGract(1, None, CollectionDisplay.SPREAD))
            simple_gracts.broadcast(ShowCollectionGract(2, None, CollectionDisplay.STACK))
            simple_gracts.broadcast(ShowCardGract(0, 0, 0))
            simple_gracts.broadcast(ShowCardGract(1, 0, 0))
            simple_gracts.broadcast(ShowCardGract(2, 0, 0))
            simple_gracts.send(0, PossibleActionsGract([
                NextPossibleAction(),
                SelectCollectionPossibleAction([0, 1]),
                SelectCardPossibleAction([0]),
                AgainstCardPossibleAction(1, [0]),
                WildCardPossibleAction(2, [2])
            ]))
            return GractModMsg(simple_gracts)

        elif isinstance(msg, PlayerActionEngMsg):
            if isinstance(msg.action, WildCardAction):
                return EndRoundModMsg("wild played")

            simple_gracts = SimpleGractLists([0, 1])
            simple_gracts.send(0, PossibleActionsGract([
                NextPossibleAction(),
                SelectCollectionPossibleAction([0, 1]),
                SelectCardPossibleAction([0]),
                AgainstCardPossibleAction(1, [0]),
                WildCardPossibleAction(2, [2])
            ]))
            return GractModMsg(simple_gracts)

        elif isinstance(msg, PlayerLeaveEngMsg):
            return EndGameModMsg("player left")

        elif isinstance(msg, EndRoundEngMsg):
            return EmptyModMsg()


class EngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid(self):
        engine = EngineManager()
        host = MockPlayer()
        joiner = MockPlayer()

        await engine.create(MockModule, host.ws)
        await host.send(json.dumps({
            "type": "intro",
            "player-name": "zachary"
        }))
        self.assertDictEqual(json.loads(await host.recv()), {
            "type": "intro",
            "game-id": 0,
            "player-id": 0
        })

        await engine.join(0, joiner.ws)
        await joiner.send(json.dumps({
            "type": "intro",
            "player-name": "jed"
        }))
        self.assertDictEqual(json.loads(await joiner.recv()), {
            "type": "intro",
            "game-id": 0,
            "player-id": 1
        })

        for i in range(0, 3):
            await host.send(json.dumps({
                "type": "start-round"
            }))

            self.assertDictEqual(json.loads(await host.recv()), {
                "type": "gract-list",
                "gract-list": [
                    { 
                        "type": "show-type", 
                        "type-id": 0, 
                        "type-name": "a card",
                        "type-desc": "",
                        "type-url": ""
                    },
                    { 
                        "type": "show-type", 
                        "type-id": 1, 
                        "type-name": "wild 1",
                        "type-desc": "",
                        "type-url": ""
                    },
                    { 
                        "type": "show-type", 
                        "type-id": 2, 
                        "type-name": "wild 2",
                        "type-desc": "",
                        "type-url": ""
                    },
                    {
                        "type": "show-coll",
                        "coll-id": 0,
                        "player-id": 0,
                        "coll-display": "hand"
                    },
                    {
                        "type": "show-coll",
                        "coll-id": 1,
                        "player-id": None,
                        "coll-display": "spread"
                    },
                    {
                        "type": "show-coll",
                        "coll-id": 2,
                        "player-id": None,
                        "coll-display": "stack"
                    },
                    {
                        "type": "show-card",
                        "card-id": 0,
                        "type-id": 0,
                        "coll-id": 0
                    },
                    {
                        "type": "show-card",
                        "card-id": 1,
                        "type-id": 0,
                        "coll-id": 0
                    },
                    {
                        "type": "show-card",
                        "card-id": 2,
                        "type-id": 0,
                        "coll-id": 0
                    },
                    {
                        "type": "possible-actions",
                        "possible-actions": [
                            { "type": "next" },
                            { "type": "select-coll", "coll-ids": [0, 1] },
                            { "type": "select", "card-ids": [0] },
                            { "type": "against", "select-card-id": 1, "against-card-ids": [0] },
                            { "type": "wild", "card-id": 2, "type-ids": [2] }
                        ]
                    }
                ]
            })
            self.assertDictEqual(json.loads(await joiner.recv()), {
                "type": "gract-list",
                "gract-list": [
                    { 
                        "type": "show-type", 
                        "type-id": 0, 
                        "type-name": "a card",
                        "type-desc": "",
                        "type-url": ""
                    },
                    { 
                        "type": "show-type", 
                        "type-id": 1, 
                        "type-name": "wild 1",
                        "type-desc": "",
                        "type-url": ""
                    },
                    { 
                        "type": "show-type", 
                        "type-id": 2, 
                        "type-name": "wild 2",
                        "type-desc": "",
                        "type-url": ""
                    },
                    {
                        "type": "show-coll",
                        "coll-id": 0,
                        "player-id": 0,
                        "coll-display": "hand"
                    },
                    {
                        "type": "show-coll",
                        "coll-id": 1,
                        "player-id": None,
                        "coll-display": "spread"
                    },
                    {
                        "type": "show-coll",
                        "coll-id": 2,
                        "player-id": None,
                        "coll-display": "stack"
                    },
                    {
                        "type": "show-card",
                        "card-id": 0,
                        "type-id": 0,
                        "coll-id": 0
                    },
                    {
                        "type": "show-card",
                        "card-id": 1,
                        "type-id": 0,
                        "coll-id": 0
                    },
                    {
                        "type": "show-card",
                        "card-id": 2,
                        "type-id": 0,
                        "coll-id": 0
                    }
                ]
            })

            GRACT_DICT = {
                "type": "gract-list",
                "gract-list": [
                    {
                        "type": "possible-actions",
                        "possible-actions": [
                            { "type": "next" },
                            { "type": "select-coll", "coll-ids": [0, 1] },
                            { "type": "select", "card-ids": [0] },
                            { "type": "against", "select-card-id": 1, "against-card-ids": [0] },
                            { "type": "wild", "card-id": 2, "type-ids": [2] }
                        ]
                    }
                ]
            }
            await host.send(json.dumps({
                "type": "action",
                "action-type": "next"
            }))
            self.assertDictEqual(json.loads(await host.recv()), GRACT_DICT)

            await host.send(json.dumps({
                "type": "action",
                "action-type": "select-coll",
                "coll-id": 0
            }))
            self.assertDictEqual(json.loads(await host.recv()), GRACT_DICT)

            await host.send(json.dumps({
                "type": "action",
                "action-type": "select-coll",
                "coll-id": 1
            }))
            self.assertDictEqual(json.loads(await host.recv()), GRACT_DICT)

            await host.send(json.dumps({
                "type": "action",
                "action-type": "select",
                "card-id": 0
            }))
            self.assertDictEqual(json.loads(await host.recv()), GRACT_DICT)

            await host.send(json.dumps({
                "type": "action",
                "action-type": "against",
                "select-card-id": 1,
                "against-card-id": 0
            }))
            self.assertDictEqual(json.loads(await host.recv()), GRACT_DICT)
            
            await host.send(json.dumps({
                "type": "action",
                "action-type": "wild",
                "card-id": 2,
                "type-id": 2
            }))

            self.assertDictEqual(json.loads(await host.recv()), {
                "type": "end-round",
                "reason": "wild played"
            })
            self.assertDictEqual(json.loads(await joiner.recv()), {
                "type": "end-round",
                "reason": "wild played"
            })

        await host.send(None)
        self.assertDictEqual(json.loads(await joiner.recv()), {
            "type": "end-game",
            "reason": "player left"
        })
        self.assertIsNone(await joiner.recv())

        # Verify the game is closed upon all players leaving
        new_joiner = MockPlayer()
        await engine.join(0, new_joiner.ws)
        self.assertDictEqual(json.loads(await new_joiner.recv()), {
            "type": "error",
            "reason": "game does not exist"
        })

    async def test_invalid_actions(self):
        host_actions = [
            {
                "type": "action",
                "action-type": "select-coll",
                "coll-id": 2
            },
            {
                "type": "action",
                "action-type": "select",
                "card-id": 1
            },
            {
                "type": "action",
                "action-type": "select",
                "card-id": 2
            },
            {
                "type": "action",
                "action-type": "against",
                "select-card-id": 0,
                "against-card-id": 0
            },
            {
                "type": "action",
                "action-type": "against",
                "select-card-id": 2,
                "against-card-id": 0
            },
            {
                "type": "action",
                "action-type": "against",
                "select-card-id": 1,
                "against-card-id": 1
            },
            {
                "type": "action",
                "action-type": "against",
                "select-card-id": 1,
                "against-card-id": 2
            },
            {
                "type": "action",
                "action-type": "wild",
                "card-id": 0,
                "type-id": 2
            },
            {
                "type": "action",
                "action-type": "wild",
                "card-id": 1,
                "type-id": 2
            },
            {
                "type": "action",
                "action-type": "wild",
                "card-id": 2,
                "type-id": 0
            },
            {
                "type": "action",
                "action-type": "wild",
                "card-id": 2,
                "type-id": 1
            },
        ]
        
        for host_action in host_actions:
            engine = EngineManager()
            host = MockPlayer()
            joiner = MockPlayer()

            await engine.create(MockModule, host.ws)
            await host.send(json.dumps({
                "type": "intro",
                "player-name": "zachary"
            }))
            await host.recv()

            await engine.join(0, joiner.ws)
            await joiner.send(json.dumps({
                "type": "intro",
                "player-name": "jed"
            }))
            await joiner.recv()

            await host.send(json.dumps({
                "type": "start-round"
            }))
            await host.recv()
            await joiner.recv()

            await host.send(json.dumps(host_action))
            self.assertDictEqual(json.loads(await host.recv()), {
                "type": "error",
                "reason": "invalid action"
            })
            self.assertIsNone(await host.recv())
            self.assertDictEqual(json.loads(await joiner.recv()), {
                "type": "end-game",
                "reason": "player left"
            })
            self.assertIsNone(await joiner.recv())

            # Ensure it is impossible to rejoin the game
            new_joiner = MockPlayer()
            await engine.join(0, new_joiner.ws)
            self.assertDictEqual(json.loads(await new_joiner.recv()), {
                "type": "error",
                "reason": "game does not exist"
            })
            self.assertIsNone(await new_joiner.recv())

    async def test_invalid_player(self):
        engine = EngineManager()
        host = MockPlayer()
        joiner = MockPlayer()

        await engine.create(MockModule, host.ws)
        await host.send(json.dumps({
            "type": "intro",
            "player-name": "zachary"
        }))
        await host.recv()

        await engine.join(0, joiner.ws)
        await joiner.send(json.dumps({
            "type": "intro",
            "player-name": "jed"
        }))
        await joiner.recv()

        await host.send(json.dumps({
            "type": "start-round"
        }))
        await host.recv()
        await joiner.recv()

        await joiner.send(json.dumps({
            "type": "action",
            "action-type": "next"
        }))
        self.assertDictEqual(json.loads(await joiner.recv()), {
            "type": "error",
            "reason": "invalid action"
        })
        self.assertIsNone(await joiner.recv())
        self.assertDictEqual(json.loads(await host.recv()), {
            "type": "end-game",
            "reason": "player left"
        })
        self.assertIsNone(await host.recv())

        # Ensure it is impossible to rejoin the game
        new_joiner = MockPlayer()
        await engine.join(0, new_joiner.ws)
        self.assertDictEqual(json.loads(await new_joiner.recv()), {
            "type": "error",
            "reason": "game does not exist"
        })
        self.assertIsNone(await new_joiner.recv())

    async def test_open_close(self):
        engine = EngineManager()
        host = MockPlayer()
        joiner = MockPlayer()
        additional = MockPlayer()

        await engine.create(MockModule, host.ws)
        await host.send(json.dumps({
            "type": "intro",
            "player-name": "zachary"
        }))
        await host.recv()

        await host.send(json.dumps({
            "type": "start-round"
        }))
        self.assertDictEqual(json.loads(await host.recv()), {
            "type": "error",
            "reason": "2 players required"
        })

        await engine.join(0, joiner.ws)
        await joiner.send(json.dumps({
            "type": "intro",
            "player-name": "jed"
        }))
        await joiner.recv()

        await engine.join(0, additional.ws)
        await additional.send(json.dumps({
            "type": "intro",
            "player-name": "robert"
        }))
        self.assertDictEqual(json.loads(await additional.recv()), {
            "type": "error",
            "reason": "2 players max"
        })

        await host.send(None)
        await joiner.send(None)

        


if __name__ == "__main__":
    unittest.main()