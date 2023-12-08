import styles from "./CreateGame.module.scss";
import Input from "../components/Input";
import Submit from "../components/Submit";
import { FormEvent } from "react";
import { useLoading } from "../providers/LoadingProvider";

export default function CreateGame() {
  const [loading, setLoading] = useLoading();
  const { Element: ModuleIdInput, valid: moduleIdValid } = Input({
    name: "module-id",
    placeholder: "Module ID",
    onValidate(value: string) {
      if (!value.length) return "Module ID must be an integer";
      const num = Number(value);
      if (isNaN(num) || !Number.isInteger(num)) return "Module ID must be an integer"
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
