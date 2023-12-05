from __future__ import annotations

import asyncio
import json
from abc import ABC
from asyncio import Queue, FIRST_COMPLETED
from module import *
from websockets import WebSocketServerProtocol


class EngineManager:
    """
    An engine manager.
    
    This manages all open engines, including interactions with them
    (e.g., to allow a new player to join).
    """

    def __init__(self) -> None:
        self.next_engine_id = 0
        self.engines: dict[int, Queue[WebSocketServerProtocol]] = {}

    async def create(self, module: type[Module], websocket: WebSocketServerProtocol) -> None:
        """
        Create a new engine.

        Args:
            module (type[Module]): The card module to instantiate.
            websocket (WebSocketServerProtocol): The connection to the creator.
        """

        # A queue is used to communicate with the engine (e.g., to notify of
        # new players). The first entry will always be the first player.
        queue = Queue()
        await queue.put(websocket)

        # Record the engine information
        engine_id = self.next_engine_id
        self.next_engine_id += 1
        self.engines[engine_id] = queue
        
        # Create a new engine task (allows this function to return
        # which asynchronously scheduling the engine).
        asyncio.create_task(engine(engine_id, self, module, queue))

    async def join(self, game_id: int, websocket: WebSocketServerProtocol) -> None:
        """
        Join a pre-existing game.

        Args:
            game_id (int): The unique identifier of the game to join.
            websocket (WebSocketServerProtocol): The connection to the joiner.
        """
        
        # Get the engine running the corresponding game
        queue = self.engines.get(game_id)

        # If the game doesn't exist, send an error
        if queue is None:
            await websocket.send(json.dumps({
                "type": "error",
                "reason": "game does not exist"
            }))
            return

        # Send the connection to the engine (where it will understand
        # it is a notification of a new player joining).
        await queue.put(websocket)


class WsWrapper:
    """
    A wrapper for a WebSocket connection which handles the serialisation/deserialisation
    of WebSocket messages for you, automatically. This was done to separate the
    parsing code from the engine code.
    """

    def __init__(self, ws: WebSocketServerProtocol) -> None:
        self.ws = ws

    @staticmethod
    def parse_response(response: dict) -> Union[WsMsg, None]:
        """
        Parse a response into a WsMsg.
        
        All WebSocket communications, at least for this implementation,
        are considered to be JSON objects -- any non-JSON object messages
        are invalid.

        Args:
            response (dict): The dictionary.

        Returns:
            Union[WsMsg, None]: The WebSocket message (None if invalid).
        """

        # The introduction message (when the player first joins to set their name)
        if response.get("type") == "intro" and isinstance(response.get("player-name"), str):
            return WsIntroMsg(response["player-name"])

        # The start round command
        elif response.get("type") == "start-round":
            return WsStartMsg()

        # The action command (e.g., select a card)
        elif response.get("type") == "action":
            action_type = response.get("action-type")

            if action_type == "next":
                return WsActionMsg(NextAction())

            elif action_type == "select":
                card_id = response.get("card-id")
                if not isinstance(card_id, int):
                    return None
                return WsActionMsg(SelectCardAction(card_id))

            elif action_type == "select-coll":
                coll_id = response.get("coll-id")
                if not isinstance(coll_id, int):
                    return None
                return WsActionMsg(SelectCollectionAction(coll_id))

            elif action_type == "against":
                select_card_id = response.get("select-card-id")
                against_card_id = response.get("against-card-id")
                if not isinstance(select_card_id, int):
                    return None
                if not isinstance(against_card_id, int):
                    return None
                return WsActionMsg(AgainstCardAction(select_card_id, against_card_id))

            elif action_type == "wild":
                card_id = response.get("card-id")
                type_id = response.get("type-id")
                if not isinstance(card_id, int):
                    return None
                if not isinstance(type_id, int):
                    return None
                return WsActionMsg(WildCardAction(card_id, type_id))

        return None

    async def send_intro(self, game_id: int, player_id: int) -> bool:
        """
        Send an introductory response (giving the game and player identifiers).

        Args:
            game_id (int): The unique identifier of the game.
            player_id (int): The unique identifier of the newly joined player.

        Returns:
            bool: Whether it was sent successfully (can be safely ignored).
        """

        return await self._send({
            "type": "intro",
            "game_id": game_id,
            "player_id": player_id
        })

    async def send_gracts(self, gracts: list[Gract]) -> bool:
        """
        Send a list of gractions.

        Args:
            gracts (list[Gract]): The gractions.

        Returns:
            bool: Whether it was sent successfully (can be safely ignored).
        """

        gract_list = []

        for gract in gracts:
            if isinstance(gract, ShowCollectionGract):
                display = None

                if gract.collection_display == CollectionDisplay.HAND:
                    display = "hand"
                elif gract.collection_display == CollectionDisplay.SPREAD:
                    display = "spread"
                elif gract.collection_display == CollectionDisplay.STACK:
                    display = "stack"

                gract_list.append({
                    "type": "show-collection",
                    "player-id": gract.player_id,
                    "collection-id": gract.collection_id,
                    "collection-display": display
                })

            elif isinstance(gract, HideCollectionGract):
                gract_list.append({
                    "type": "hide-collection",
                    "collection-id": gract.collection_id
                })

            elif isinstance(gract, ShowTypeGract):
                gract_list.append({
                    "type": "show-type",
                    "type-id": gract.type_id,
                    "type-name": gract.type_name,
                    "type-desc": gract.type_desc,
                    "type-url": gract.type_url
                })

            elif isinstance(gract, ShowCardGract):
                gract_list.append({
                    "type": "show-card",
                    "card-id": gract.card_id,
                    "type-id": gract.type_id,
                    "collection-id": gract.collection_id
                })

            elif isinstance(gract, HideCardGract):
                gract_list.append({
                    "type": "hide-card",
                    "card-id": gract.card_id
                })

            elif isinstance(gract, RevealCardGract):
                gract_list.append({
                    "type": "reveal-card",
                    "old-card-id": gract.old_card_id,
                    "new-card-id": gract.new_card_id,
                    "new-type-id": gract.new_type_id
                })

            elif isinstance(gract, ConcealCardGract):
                gract_list.append({
                    "type": "conceal-card",
                    "old-card-id": gract.old_card_id,
                    "new-card-id": gract.new_card_id,
                    "new-type-id": gract.new_type_id
                })

            elif isinstance(gract, MoveCardGract):
                gract_list.append({
                    "type": "move-card",
                    "card-id": gract.card_id,
                    "collection-id": gract.collection_id
                })

            elif isinstance(gract, PossibleActionsGract):
                possible_actions = []

                for possible_action in gract.possible_actions:
                    if isinstance(possible_action, NextPossibleAction):
                        possible_actions.append({
                            "type": "next"
                        })

                    elif isinstance(possible_action, SelectCardPossibleAction):
                        possible_actions.append({
                            "type": "select",
                            "card-ids": possible_action.card_ids
                        })

                    elif isinstance(possible_action, SelectCollectionPossibleAction):
                        possible_actions.append({
                            "type": "select-coll",
                            "coll-ids": possible_action.collection_ids
                        })

                    elif isinstance(possible_action, AgainstCardPossibleAction):
                        possible_actions.append({
                            "type": "against",
                            "select-card-id": possible_action.select_card_id,
                            "against-card-ids": possible_action.against_card_ids
                        })

                    elif isinstance(possible_action, WildCardPossibleAction):
                        possible_actions.append({
                            "type": "wild",
                            "card-id": possible_action.card_id,
                            "type-ids": possible_action.type_ids
                        })

                gract_list.append({
                    "type": "possible-actions",
                    "possible-actions": possible_actions
                })

        return await self._send({
            "type": "gract-list",
            "gract-list": gract_list
        })

    async def send_end_round(self, reason: str) -> bool:
        """
        Send the end round message.

        Args:
            reason (str): The reason the round is ending.

        Returns:
            bool: Whether the message was sent successfully (can be ignored).
        """

        return await self._send({
            "type": "end-round",
            "reason": reason
        })

    async def send_end_game(self, reason: str) -> bool:
        """
        Send the end game message.

        Args:
            reason (str): The reason the game is ending.

        Returns:
            bool: Whether the message was sent successfully (can be safely ignored).
        """

        return await self._send({
            "type": "end-game",
            "reason": reason
        })

    async def send_error(self, reason: str) -> bool:
        """
        Send an error message.

        Args:
            reason (str): The error.

        Returns:
            bool: Whether it was sent successfully (can be safely ignored).
        """

        return await self._send({
            "type": "error",
            "reason": reason
        })

    async def recv(self) -> Union[WsMsg, None]:
        """
        Receive a message from the WebSocket.
        
        Waits until a message can be returned, or the connection closes.

        Returns:
            Union[WsMsg, None]: The message, or None if the connection closed/message was invalid.
        """

        try:
            # Get the response
            response = await self.ws.recv()

            if not isinstance(response, str):
                # Close the connection
                await self.ws.close()
                return WsCloseMsg()

            response = json.loads(response)

            if not isinstance(response, dict):
                await self.ws.close()
                return WsCloseMsg()

            msg = WsWrapper.parse_response(response)
            if msg is None:
                await self.ws.close()
                return WsCloseMsg()

            return msg

        except:
            # close is idempotent (won't throw an error)
            await self.ws.close()
            return WsCloseMsg()

    async def _send(self, msg: dict) -> bool:
        # Ignore failures: failures generally indicate that the
        # WebSocket connection has been terminated, but messages may
        # still be in the WebSocket, waiting to be handled, so we just
        # "pretend" that the WebSocket is still open and receiving.
        #
        # We return a boolean indicating the success of the end, just
        # in case the send result is important
        try:
            await self.ws.send(json.dumps(msg))
            return True
        except:
            return False

    async def close(self):
        """
        Close the connection.
        """
        await self.ws.close()


class WsMsg(ABC):
    """
    A WebSocket message.
    """

    pass


class WsIntroMsg(WsMsg):
    """
    An introductory message specifying the name of the new player.
    
    This is the first message sent over any WebSocket connection.
    """

    def __init__(self, player_name: str) -> None:
        super().__init__()
        self.player_name = player_name


class WsStartMsg(WsMsg):
    """
    A message requesting a round of the game to start.
    """

    pass


class WsActionMsg(WsMsg):
    """
    A message specifying the action a specific player took.
    """

    def __init__(self, action: Action) -> None:
        super().__init__()
        self.action = action


class WsCloseMsg(WsMsg):
    """
    A message indicating the connection was closed.
    """

    pass


class Player:
    """
    A player in the game.
    """

    def __init__(self, id: int, name: str, ws: WsWrapper) -> None:
        """
        Create a new player.

        Args:
            id (int): The unique identifier of the player.
            name (str): The name of the player.
            ws (WsWrapper): The connection to the player.
        """

        self.id = id
        self.name = name
        self.ws = ws
        self.possible_actions = []


async def engine(id: int, manager: EngineManager, module: type[Module], queue: Queue[WebSocketServerProtocol]):
    """
    The engine which runs a game.

    Args:
        id (int): The unique identifier the game is running under.
        manager (EngineManager): The engine manager which created the engine.
        module (type[Module]): The module to instantiate.
        queue (Queue[WebSocketServerProtocol]): The queue on which new players are sent.
    """

    # Instantiate the module
    instance: Module = module.create_module()
    response = instance.process_msg(InitEngMsg())

    # If the response is anything other than a change state, quit
    if not isinstance(response, ChangeStateModMsg) or isinstance(response.join_mode, Closed):
        del manager.engines[id]
        return

    # Global variables
    join_mode = response.join_mode
    start_mode = response.start_mode
    round_active = False
    next_player_id = 0
    new_joins: dict[int, Player] = {}
    players: dict[int, Player] = {}
    queue_task = asyncio.create_task(queue.get())
    player_tasks: dict[int, asyncio.Task] = {}
    aws = (queue_task,)
    msgs = []

    while True:
        # Makeshift select statement
        # Chances are, except maybe under load, that only one task is
        # done, but if not we linearise it
        await asyncio.wait(aws, return_when=FIRST_COMPLETED)

        # Check each individual task to see if it is completed -- there
        # is at least one completed task
        if queue_task.done():
            ws = WsWrapper(queue_task.result())
            msg = await ws.recv()

            if isinstance(msg, WsIntroMsg):
                player_id = next_player_id
                next_player_id += 1
                new_joins[player_id] = Player(player_id, msg.player_name, ws)
                msgs.append(PlayerJoinEngMsg(player_id, msg.player_name))
            else:
                await ws.close()

            # Reset the task so more joins can be registered
            queue_task = asyncio.create_task(queue.get())

        for player_id, player_task in player_tasks.items():
            if not player_task.done():
                continue

            msg: Union[WsMsg, None] = player_task.result()

            if isinstance(msg, WsStartMsg):
                start_round = StartRoundEngMsg()

                # Hacky thing I would ideally like fixed but oh well
                start_round.player_id = player_id

                # Any player, at least for now, can start the game
                msgs.append(start_round)

                # Reset the task
                player_tasks[player_id] = asyncio.create_task(
                    players[player_id].ws.recv())
            elif isinstance(msg, WsActionMsg):
                msgs.append(PlayerActionEngMsg(player_id, msg.action))

                # Reset the task
                player_tasks[player_id] = asyncio.create_task(
                    players[player_id].ws.recv())
            else:
                # This player can no longer receive messages
                player = players[player_id]

                # We can close the socket here as it has no effect -- no messages
                # after a leave will be considered anyway
                await player.ws.close()
                msgs.append(PlayerLeaveEngMsg(player_id))

        for msg in msgs:
            # Because multiple messages can be queued at a time, and because a
            # previous message can have a signficiant effect on a subsequent
            # message, we have to apply all stateful changes here
            #
            # For example, a change state message may be followed by an otherwise
            # valid player join message, causing a player who should be given access
            # to be denied
            if isinstance(msg, PlayerJoinEngMsg):
                if isinstance(join_mode, Open):
                    players[msg.player_id] = new_joins[msg.player_id]
                    del new_joins[msg.player_id]
                    await players[msg.player_id].ws.send_intro(id, msg.player_id)
                    player_tasks[msg.player_id] = asyncio.create_task(
                        players[msg.player_id].ws.recv())

                else:
                    await new_joins[msg.player_id].ws.send_error(join_mode.reason)
                    del new_joins[msg.player_id]

            elif isinstance(msg, PlayerLeaveEngMsg):
                del players[msg.player_id]
                del player_tasks[msg.player_id]

                # Close the game if there are 0 players left
                if len(players) == 0:
                    del manager.engines[id]
                    return

            elif isinstance(msg, StartRoundEngMsg):
                if round_active or isinstance(start_mode, Closed):
                    player = players[msg.player_id]
                    await player.ws.send_error(start_mode.reason)
                    continue
                else:
                    round_active = True

            elif isinstance(msg, EndRoundEngMsg) and not round_active:
                continue

            elif isinstance(msg, PlayerActionEngMsg):
                if not round_active:
                    # NOTE: we do not have to check the player hasn't left a player
                    # can only send one message per iteration (i.e., for them to
                    # have left, they would have had to use their one message
                    # already)
                    continue

                can_perform = False
                player = players[msg.player_id]
                possible_actions = player.possible_actions

                # Verify that the player can indeed make that action (bit slow,
                # faster method could be created)
                if isinstance(msg.action, NextAction):
                    for possible_action in possible_actions:
                        if isinstance(possible_action, NextPossibleAction):
                            can_perform = True
                            break

                elif isinstance(msg.action, SelectCardAction):
                    for possible_action in possible_actions:
                        if isinstance(possible_action, SelectCardPossibleAction) and msg.action.card_id in possible_action.card_ids:
                            can_perform = True
                            break

                elif isinstance(msg.action, SelectCollectionAction):
                    for possible_action in possible_actions:
                        if isinstance(possible_action, SelectCollectionPossibleAction) and msg.action.collection_id in possible_action.collection_ids:
                            can_perform = True
                            break

                elif isinstance(msg.action, AgainstCardAction):
                    for possible_action in possible_actions:
                        if \
                                isinstance(possible_action, AgainstCardPossibleAction) \
                                and msg.action.select_card_id == possible_action.select_card_id \
                                and msg.action.against_card_id in possible_action.against_card_ids:
                            can_perform = True
                            break

                elif isinstance(msg.action, WildCardAction):
                    for possible_action in possible_actions:
                        if \
                                isinstance(possible_action, WildCardPossibleAction) \
                                and msg.action.card_id == possible_action.card_id \
                                and msg.action.type_id in possible_action.type_ids:
                            can_perform = True
                            break

                if not can_perform:
                    await player.ws.send_error("invalid action")
                    await player.ws.close()
                    continue

            response = instance.process_msg(msg)

            if isinstance(response, ChangeStateModMsg):
                join_mode = response.join_mode
                start_mode = response.start_mode

            elif isinstance(response, EndRoundModMsg):
                round_active = False
                for player in players.values():
                    await player.ws.send_end_round(response.reason)

            elif isinstance(response, EndGameModMsg):
                for player in players.values():
                    await player.ws.send_end_game(response.reason)
                    await player.ws.close()

                for task in aws:
                    task.cancel()

                del manager.engines[id]
                return

            elif isinstance(response, GractModMsg):
                for player_id, gract_list in response.gract_lists:
                    player = players[player_id]

                    for gract in gract_list:
                        if isinstance(gract, PossibleActionsGract):
                            player.possible_actions = gract.possible_actions

                    await player.ws.send_gracts(gract_list)

        msgs = []
        aws = (queue_task, *player_tasks.values())
