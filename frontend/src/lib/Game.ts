import { useEffect, useState } from "react";

export type GameRequest = CreateGameRequest | JoinGameRequest;

export type CreateGameRequest = {
  type: "create";
  moduleId: number;
  playerName: string;
};

export type JoinGameRequest = {
  type: "join";
  gameId: number;
  playerName: string;
};

export type Game =
  | GameLoading
  | GameInvalid
  | GameWaiting
  | GamePlaying
  | GameClosed;

export type GameLoading = { type: "loading" };

export type GameInvalid = {
  type: "invalid";
  error?: string;
};

export type GameWaiting = {
  type: "waiting" | "starting";
  info: GameInfo;
  reason?: string;
  error?: string;
  startRound?: () => void;
};

export type GamePlaying = {
  type: "playing";
  info: GameInfo;
  data: RoundData;
  error?: string;
  playAction?: (action: Action) => void;
};

export type Action =
  | { type: "next" }
  | { type: "select-coll"; collectionId: number }
  | { type: "select"; cardId: number }
  | { type: "against"; selectCardId: number; againstCardId: number }
  | { type: "wild"; cardId: number; typeId: number };

export type GameClosed = {
  type: "closed";
  error?: string;
  reason?: string;
};

export type Player = {
  id: number;
  name: string;
};

export type GameInfo = {
  playerId: number;
  gameId: number;
  joinMode: Mode;
  startMode: Mode;
  players: Map<number, Player>;
};

export type Mode = Open | Closed;
export type Open = { type: "open" };
export type Closed = { type: "closed"; reason: string };

export type RoundData = {
  types: Map<number, CardType>;
  collections: Map<number, Collection>;
  cards: Map<number, Card>;
  nextable: boolean;
};

export type CardType = {
  id: number;
  name: string;
  description: string;
  url: string;
};

export type Collection = {
  id: number;
  display: "hand" | "spread" | "stack";
  playerId: number | null;
  cardIds: number[];
  selectable: boolean;
};

export type Card = {
  id: number;
  typeId: number;
  collectionId: number;
  actionable?:
    | { type: "select" }
    | { type: "against"; cardIds: number[] }
    | { type: "wild"; typeIds: number[] };
};

const BASE_URL = "ws://localhost:4000";

export function useGame(request: GameRequest): Game {
  // NOTE: unfortunately a reducer has to be used here as useEffect cannot be
  // dependent on state (i.e., it can only dispatch, it cannot read -- perks
  // of using React). If `useState` were to be used, it'd just be a recreation
  // implementation of `useReducer`.
  const [game, setGame] = useState({ type: "loading" } as Game);

  useEffect(() => {
    let ws: WebSocket;
    let currentGame: Game = { type: "loading" };
    setGame(currentGame);

    if (request.type === "join") {
      ws = new WebSocket(`${BASE_URL}/join/${request.gameId}`);
    } else {
      ws = new WebSocket(`${BASE_URL}/create/${request.moduleId}`);
    }

    function openHandler() {
      ws.send(
        JSON.stringify({
          type: "intro",
          "player-name": request.playerName,
        })
      );
    }

    function messageHandler(ev: MessageEvent) {
      try {
        const msg = JSON.parse(ev.data);

        switch (currentGame.type) {
          // Handle the loading case
          case "loading":
            currentGame = handleLoading(ws, msg);
            break;

          case "waiting":
          case "starting":
            currentGame = handleWaiting(currentGame, ws, msg);
            break;

          case "playing":
            currentGame = handlePlaying(currentGame, ws, msg);
            break;

          // Do not handle any messages if the game is closed
          case "invalid":
          case "closed":
            return;
        }

        switch (currentGame.type) {
          case "waiting":
            setGame({
              ...currentGame,
              startRound() {
                if (currentGame.type === "waiting") {
                  ws.send(
                    JSON.stringify({
                      type: "start-round",
                    })
                  );
                }
              },
            });
            break;

          case "playing":
            setGame({
              ...currentGame,
              playAction(action: Action) {
                if (currentGame.type !== "playing") return;

                switch (action.type) {
                  case "next":
                    if (currentGame.data.nextable) {
                      ws.send(
                        JSON.stringify({
                          type: "action",
                          "action-type": "next",
                        })
                      );
                    } else return;
                    break;

                  case "select-coll": {
                    const coll = currentGame.data.collections.get(
                      action.collectionId
                    )!;
                    if (!coll.selectable) return;
                    ws.send(
                      JSON.stringify({
                        type: "action",
                        "action-type": "select-coll",
                        "coll-id": coll.id,
                      })
                    );
                    break;
                  }

                  case "select": {
                    const card = currentGame.data.cards.get(
                      action.cardId
                    )!;
                    if (card.actionable?.type !== "select") return;
                    ws.send(JSON.stringify({
                      type: "action",
                      "action-type": "select",
                      "card-id": card.id
                    }));
                    break;
                  }

                  case "against":
                  case "wild":
                    throw new Error("not implemented yet");
                }

                currentGame = {
                  ...currentGame,
                  data: {
                    ...currentGame.data,
                    collections: new Map<number, Collection>(
                      [...currentGame.data.collections].map(([id, coll]) => [
                        id,
                        {
                          ...coll,
                          selectable: false,
                        } as Collection,
                      ])
                    ),
                    cards: new Map(
                      [...currentGame.data.cards].map(([id, card]) => [
                        id,
                        {
                          ...card,
                          actionable: undefined
                        }
                      ])
                    ),
                    nextable: false,
                  },
                };
                setGame(currentGame);
              },
            });
            break;

          case "loading":
          case "starting":
          case "invalid":
          case "closed":
            setGame(currentGame);
            break;
        }
      } catch (e) {
        console.error(e);
        ws.close();
      }
    }

    function closeHandler() {
      ws.removeEventListener("open", openHandler);
      ws.removeEventListener("message", messageHandler);
      ws.removeEventListener("error", closeHandler);
      ws.removeEventListener("close", closeHandler);
      if (currentGame.type !== "closed" && currentGame.type !== "invalid") {
        currentGame = { type: "closed" };
        setGame(currentGame);
      }
    }

    ws.addEventListener("open", openHandler);
    ws.addEventListener("message", messageHandler);
    ws.addEventListener("error", closeHandler);
    ws.addEventListener("close", closeHandler);
    return () => {
      ws.removeEventListener("open", openHandler);
      ws.removeEventListener("message", messageHandler);
      ws.removeEventListener("error", closeHandler);
      ws.removeEventListener("close", closeHandler);
      ws.close();
      if (currentGame.type !== "closed" && currentGame.type !== "invalid") {
        currentGame = { type: "closed" };
        setGame(currentGame);
      }
    };
  }, [request]);

  return game;
}

function handleLoading(ws: WebSocket, msg: any): Game {
  if (msg["type"] === "intro") {
    const joinMode: Mode =
      msg["join-mode"]["status"] === "open"
        ? { type: "open" }
        : { type: "closed", reason: msg["join-mode"]["reason"] };

    const startMode: Mode =
      msg["start-mode"]["status"] === "open"
        ? { type: "open" }
        : { type: "closed", reason: msg["start-mode"]["reason"] };

    const players = new Map<number, Player>(
      msg["players"].map((player: any) => [
        player["id"],
        {
          id: player["id"],
          name: player["name"],
        },
      ])
    );

    return {
      type: "waiting",
      info: {
        playerId: msg["player-id"],
        gameId: msg["game-id"],
        joinMode,
        startMode,
        players,
      },
    };
  } else if (msg["type"] === "error") {
    ws.close();
    return {
      type: "invalid",
      error: msg["reason"],
    };
  } else {
    ws.close();
    return { type: "closed" };
  }
}

function handleWaiting(game: GameWaiting, ws: WebSocket, msg: any): Game {
  switch (msg["type"]) {
    case "player-join": {
      const newGame: GameWaiting = {
        ...game,
        info: {
          ...game.info,
          players: new Map(game.info.players),
        },
      };

      newGame.info.players.set(msg["player-id"], {
        id: msg["player-id"],
        name: msg["player-name"],
      });

      return newGame;
    }

    case "player-leave": {
      const newGame: GameWaiting = {
        ...game,
        info: {
          ...game.info,
          players: new Map(game.info.players),
        },
      };

      newGame.info.players.delete(msg["player-id"]);
      return newGame;
    }

    case "status-change": {
      const joinMode: Mode =
        msg["join-mode"]["status"] === "open"
          ? { type: "open" }
          : { type: "closed", reason: msg["join-mode"]["reason"] };

      const startMode: Mode =
        msg["start-mode"]["status"] === "open"
          ? { type: "open" }
          : { type: "closed", reason: msg["start-mode"]["reason"] };

      const newGame: GameWaiting = {
        ...game,
        info: {
          ...game.info,
          joinMode,
          startMode,
        },
      };

      return newGame;
    }

    case "start-round": {
      const newGame: GamePlaying = {
        type: "playing",
        info: game.info,
        data: {
          types: new Map(),
          collections: new Map(),
          cards: new Map(),
          nextable: false,
        },
      };

      return newGame;
    }

    case "end-game": {
      return {
        type: "closed",
        reason: msg["reason"],
      };
    }

    case "error": {
      return {
        ...game,
        type: "waiting",
        error: msg["reason"],
      };
    }

    default:
      ws.close();
      return { type: "closed" };
  }
}

function handlePlaying(game: GamePlaying, ws: WebSocket, msg: any): Game {
  switch (msg["type"]) {
    case "gract-list": {
      return processGractList(game, msg);
    }

    case "player-join": {
      const newGame: GamePlaying = {
        ...game,
        info: {
          ...game.info,
          players: new Map(game.info.players)
        }
      };
      newGame.info.players.set(msg["player-id"], {
        id: msg["player-id"],
        name: msg["player-name"]
      });
      return newGame;
    }

    case "player-leave": {
      const newGame: GamePlaying = {
        ...game,
        info: {
          ...game.info,
          players: new Map(game.info.players),
        },
        data: {
          ...game.data,
          collections: new Map(game.data.collections),
          cards: new Map(game.data.cards)
        }
      };

      // Remove the player
      newGame.info.players.delete(msg["player-id"]);

      // Remove the collection, and all cards associated with the collection
      for (const [collId, coll] of newGame.data.collections) {
        if (coll.playerId !== msg["player-id"]) continue;

        for (const cardId of coll.cardIds) {
          newGame.data.cards.delete(cardId);
        }

        newGame.data.collections.delete(collId);
      }

      return newGame;
    }

    case "end-round": {
      return {
        type: "waiting",
        info: {
          ...game.info
        },
        reason: msg["reason"],
      } as GameWaiting;
    }

    case "end-game": {
      ws.close();
      return { type: "closed", reason: msg["reason"] };
    }

    case "error":
      return {
        ...game,
        error: msg["reason"]
      };

    default:
      throw new Error("unreachable");
  }
}

function processGractList(game: GamePlaying, msg: any): Game {
  const newGame: GamePlaying = {
    ...game,
    data: {
      types: new Map(game.data.types),
      collections: new Map(game.data.collections),
      cards: new Map(game.data.cards),
      nextable: game.data.nextable,
    },
  };

  for (const gract of msg["gract-list"]) {
    switch (gract["type"]) {
      case "show-type": {
        newGame.data.types.set(gract["type-id"], {
          id: gract["type-id"],
          name: gract["type-name"],
          description: gract["type-desc"],
          url: gract["type-url"],
        });
        break;
      }

      case "show-coll": {
        newGame.data.collections.set(gract["coll-id"], {
          id: gract["coll-id"],
          display: gract["coll-display"],
          playerId: gract["player-id"],
          cardIds: [],
          selectable: false,
        });
        break;
      }

      case "hide-coll": {
        // Get the coll
        const coll = newGame.data.collections.get(gract["coll-id"])!;

        // Delete the coll
        newGame.data.collections.delete(gract["coll-id"]);

        // Delete all cards in the coll
        for (const cardId of coll.cardIds) {
          newGame.data.cards.delete(cardId);
        }

        break;
      }

      case "show-card": {
        // Get the coll
        const coll = newGame.data.collections.get(gract["coll-id"])!;

        // Add the card
        newGame.data.cards.set(gract["card-id"], {
          id: gract["card-id"],
          typeId: gract["type-id"],
          collectionId: gract["coll-id"],
        });

        // Add the cardId to the array
        newGame.data.collections.set(coll.id, {
          ...coll,
          cardIds: [...coll.cardIds, gract["card-id"]],
        });

        break;
      }

      case "hide-card": {
        // Get the card and the collection
        const card = newGame.data.cards.get(gract["card-id"])!;
        const coll = newGame.data.collections.get(card.collectionId)!;

        // Delete the card
        newGame.data.cards.delete(card.id);

        // Remove the card from the cardIds array
        newGame.data.collections.set(coll.id, {
          ...coll,
          cardIds: coll.cardIds.filter((cardId) => cardId !== card.id),
        });

        break;
      }

      case "move-card": {
        // Get the old collection, the new collection, and the card
        const card = newGame.data.cards.get(gract["card-id"])!;
        const oldColl = newGame.data.collections.get(card.collectionId)!;
        const newColl = newGame.data.collections.get(gract["coll-id"])!;

        newGame.data.cards.set(card.id, {
          ...card,
          collectionId: newColl.id,
        });
        newGame.data.collections.set(oldColl.id, {
          ...oldColl,
          cardIds: oldColl.cardIds.filter((cardId) => cardId !== card.id),
        });
        newGame.data.collections.set(newColl.id, {
          ...newColl,
          cardIds: [...newColl.cardIds, card.id],
        });

        break;
      }

      case "reveal-card":
      case "conceal-card": {
        // Get the old card and replace it with the new card
        const card = newGame.data.cards.get(gract["old-card-id"])!;

        // We also need to get the collection as the card's id might change
        const coll = newGame.data.collections.get(card.collectionId)!;

        newGame.data.cards.delete(card.id);
        newGame.data.cards.set(gract["new-card-id"], {
          ...card,
          id: gract["new-card-id"],
          typeId: gract["new-type-id"],
        });

        // Update the collection
        newGame.data.collections.set(coll.id, {
          ...coll,
          cardIds: [
            ...coll.cardIds.filter((cardId) => cardId !== gract["old-card-id"]),
            gract["new-card-id"],
          ],
        });

        break;
      }

      case "possible-actions": {
        for (const pAction of gract["possible-actions"]) {
          switch (pAction["type"]) {
            case "next":
              newGame.data.nextable = true;
              break;

            case "select": {
              for (const cardId of pAction["card-ids"]) {
                const card = newGame.data.cards.get(cardId)!;
                newGame.data.cards.set(card.id, {
                  ...card,
                  actionable: { type: "select" },
                });
              }
              break;
            }

            case "select-coll": {
              for (const collId of pAction["coll-ids"]) {
                const coll = newGame.data.collections.get(collId)!;
                newGame.data.collections.set(collId, {
                  ...coll,
                  selectable: true,
                });
              }

              break;
            }

            case "against": {
              const card = newGame.data.cards.get(gract["select-card-id"])!;
              newGame.data.cards.set(card.id, {
                ...card,
                actionable: {
                  type: "against",
                  cardIds: gract["against-card-ids"],
                },
              });

              break;
            }

            case "wild": {
              const card = newGame.data.cards.get(gract["card-id"])!;
              newGame.data.cards.set(card.id, {
                ...card,
                actionable: {
                  type: "wild",
                  typeIds: gract["type-ids"],
                },
              });

              break;
            }
          }
        }
      }
    }
  }

  return newGame;
}
