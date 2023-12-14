import styles from "./CreateGame.module.scss";
import Input from "../components/Input";
import Submit from "../components/Submit";
import { FormEvent, useState } from "react";
import { useLoading } from "../providers/LoadingProvider";
import Player from "../components/Player";

export default function CreateGame() {
  const [loading,] = useLoading();
  const [player, setPlayer] = useState(null as any);
  const { Element: ModuleIdInput, value: moduleId, valid: moduleIdValid } = Input({
    name: "module-id",
    placeholder: "Module ID",
    onValidate(value: string) {
      if (!value.length) return "Module ID must be an integer";
      const num = Number(value);
      if (isNaN(num) || !Number.isInteger(num)) return "Module ID must be an integer"
      return null;
    }
  });
  const { Element: PlayerNameInput, value: playerName, valid: playerNameValid } = Input({
    name: "player-name",
    placeholder: "Enter your player name",
    onValidate(value: string) {
      if (value.length) return null;
      else return "Player name must be provided"
    }
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPlayer({
      type: "create",
      moduleId: Number(moduleId),
      playerName
    });
  }

  if (player) {
    return <Player request={player} />
  }

  return (
    <div className={styles.positioner}>
      <div className={styles["rainbow-border"]}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <h1>Create a new game!</h1>
          { ModuleIdInput }
          { PlayerNameInput }
          <br /><br />
          <Submit text="Create!" disabled={loading || !(moduleIdValid && playerNameValid)} />
        </form>
      </div>
    </div>
  );
}
