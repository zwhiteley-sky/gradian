import { GameWaiting } from "../lib/Game";
import styles from "./Waiting.module.scss";

export default function Waiting({ game }: { game: GameWaiting }) {
  const players = [...game.info.players.values()];

  return (
    <div className={styles["positioner"]}>
      <div className={styles["rainbow-box"]}>
        <div>
          {
            game.reason && 
            <div className={styles.info} style={{ marginTop: "0", marginBottom: "20px" }}>
              <h4>Round Ended!</h4>
              <span>{game.reason}</span>
            </div>
          }
          {
            game.error && 
            <div className={styles.warning} style={{ marginTop: "0", marginBottom: "20px" }}>
              <h4>An error occurred!</h4>
              <span>{game.error}</span>
            </div>
          }
          <h1>Game ID: {game.info.gameId}</h1>
          Players ({game.info.players.size}):{" "}
          {players.map((player, idx) => (
            <>
              <span
                style={{
                  color: player.id === game.info.playerId ? "green" : "black",
                }}
                key={player.id}
              >
                {player.name}
              </span>
              {idx < players.length - 1 && ", "}
            </>
          ))}
          <br />
          {game.info.joinMode.type !== "open" && (
            <div className={styles.warning}>
              <h4>WARNING! Player limit reached!</h4>
              <span>{game.info.joinMode.reason}</span>
            </div>
          )}
          <br />
          {game.info.startMode.type === "closed" ? (
            <div className={styles.warning}>
              <h4>WARNING! Cannot start game!</h4>
              <span>{game.info.startMode.reason}</span>
            </div>
          ) : (
            <div
              className={
                game.type === "waiting"
                  ? styles["button-box"]
                  : `${styles["button-box"]} ${styles.disabled}`
              }
            >
              <button
                disabled={game.type === "starting"}
                onClick={() => game.startRound && game.startRound()}
              >
                Start Round!
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
