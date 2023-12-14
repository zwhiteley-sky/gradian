import { useState } from "react";
import { GamePlaying, CardType, Card } from "../lib/Game";
import styles from "./Table.module.scss";

type SelectAgainst = {
  type: "against";
  cardId: number;
  cardIds: number[];
};

type SelectWild = {
  type: "wild";
  cardId: number;
  typeIds: number[];
};

export default function Table({ game }: { game: GamePlaying }) {
  const [select, setSelect] = useState(
    null as SelectAgainst | SelectWild | null
  );
  const players = [...game.info.players.values()];
  const collections = [...game.data.collections.values()];

  return (
    <div>
      {select && (
        <Modal game={game} mode={select} onComplete={() => setSelect(null)} />
      )}
      {game.data.nextable && (
        <button
          onClick={() => game.playAction && game.playAction({ type: "next" })}
        >
          Next!
        </button>
      )}

      <h1
        style={{
          fontWeight: "bold",
          color: "blue",
        }}
      >
        Deck
      </h1>

      {collections
        .filter((coll) => coll.playerId === null)
        .map((coll) => (
          <Collection
            key={coll.id}
            collectionId={coll.id}
            game={game}
            onSelect={setSelect}
          />
        ))}

      {players.map((player) => (
        <div key={player.id}>
          <h1>{player.name}</h1>
          {collections
            .filter((coll) => coll.playerId === player.id)
            .map((coll) => (
              <Collection
                key={coll.id}
                collectionId={coll.id}
                game={game}
                onSelect={setSelect}
              />
            ))}
        </div>
      ))}
    </div>
  );
}

function Collection({
  collectionId,
  game,
  onSelect,
}: {
  collectionId: number;
  game: GamePlaying;
  onSelect: (select: SelectAgainst | SelectWild) => void;
}) {
  const coll = game.data.collections.get(collectionId)!;

  if (coll.display === "stack") {
    let cardType: CardType | null = null;
    if (coll.cardIds.length > 0) {
      const card = game.data.cards.get(coll.cardIds[coll.cardIds.length - 1])!;
      cardType = game.data.types.get(card.typeId)!;
    }

    return (
      <div>
        <h2
          onClick={
            coll.selectable
              ? () =>
                  game.playAction &&
                  game.playAction({
                    type: "select-coll",
                    collectionId: coll.id,
                  })
              : undefined
          }
        >
          Collection {coll.id} - {coll.display}
        </h2>
        {cardType && <img src={cardType.url} />}
      </div>
    );
  }

  return (
    <div>
      <h2
        onClick={
          coll.selectable
            ? () =>
                game.playAction &&
                game.playAction({
                  type: "select-coll",
                  collectionId: coll.id,
                })
            : undefined
        }
      >
        Collection {coll.id} - {coll.display}
      </h2>
      {coll.cardIds
        .map((cardId) => game.data.cards.get(cardId)!)
        .map((card) => {
          let action: any;
          if (card.actionable && game.playAction) {
            switch (card.actionable.type) {
              case "select": {
                action = () =>
                  game.playAction!({ type: "select", cardId: card.id });
                break;
              }

              case "against": {
                action = () =>
                  onSelect({
                    type: "against",
                    cardId: card.id,
                    cardIds: (card.actionable as any).cardIds,
                  });
                break;
              }

              case "wild":
                action = () =>
                  onSelect({
                    type: "wild",
                    cardId: card.id,
                    typeIds: (card.actionable as any).typeIds,
                  });
                break;
            }
          }

          return (
            <img
              key={card.id}
              src={game.data.types.get(card.typeId)!.url}
              onClick={action}
            />
          );
        })}
    </div>
  );
}

function Modal({
  game,
  mode,
  onComplete,
}: {
  game: GamePlaying;
  mode: SelectAgainst | SelectWild;
  onComplete: () => void;
}) {
  if (mode.type === "against") {
    return (
      <div className={styles.background}>
        <div className={styles.modal}>
          <h1 style={{ textAlign: "center" }}>
            Select a card to play against!
          </h1>
          {mode.cardIds
            .map((cardId) => game.data.cards.get(cardId)!)
            .map(
              (card) =>
                [card, game.data.types.get(card.typeId)!] as [Card, CardType]
            )
            .map(([card, type]: [Card, CardType]) => (
              <img
                key={card.id}
                src={type.url}
                onClick={() => {
                  game.playAction &&
                    game.playAction({
                      type: "against",
                      selectCardId: mode.cardId,
                      againstCardId: card.id,
                    });
                  onComplete();
                }}
              />
            ))}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.background}>
      <div className={styles.modal}>
        <h1 style={{ textAlign: "center" }}>Select a card to play against!</h1>
        {mode.typeIds
          .map((typeId) => game.data.types.get(typeId)!)
          .map((type) => (
            <img
              key={type.id}
              src={type.url}
              onClick={() => {
                game.playAction &&
                  game.playAction({
                    type: "wild",
                    cardId: mode.cardId,
                    typeId: type.id
                  });
                onComplete();
              }}
            />
          ))}
      </div>
    </div>
  );
}
