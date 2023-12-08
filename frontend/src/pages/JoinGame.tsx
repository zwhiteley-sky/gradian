import styles from "./JoinGame.module.scss";
import Input from "../components/Input";
import Submit from "../components/Submit";
import { FormEvent } from "react";
import { useLoading } from "../providers/LoadingProvider";

export default function JoinGame() {
  const [loading, setLoading] = useLoading();
  const { Element: GameIdElement, valid: gameIdValid } = Input({
    name: "game-id",
    placeholder: "Game ID",
    onValidate(value: string) {
      if (!value.length) return "Game ID must be an integer";
      const num = Number(value);
      if (isNaN(num) || !Number.isInteger(num)) return "Game ID must be an integer";
      return null;
    }
  });
  const { Element: PlayerNameInput, valid: playerNameValid } = Input({
    name: "player-name",
    placeholder: "Enter your player name",
    onValidate(value: string) {
      if (value.length) return null;
      else return "Player name must be provided"
    }
  });

  function handlSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  }

  return (
    <div className={styles.positioner}>
      <div className={styles["rainbow-border"]}>
        <form className={styles.form} onSubmit={handlSubmit}>
          <h1>Join a game!</h1>
          { GameIdElement }
          { PlayerNameInput }
          <br /><br />
          <Submit text="Join!" disabled={loading || !(gameIdValid && playerNameValid)} />
        </form>
      </div>
    </div>
  );
}
