import { Link } from "react-router-dom";
import { useLoading } from "../providers/LoadingProvider";
import styles from "./Header.module.scss";

export default function Header() {
  const [loading] = useLoading();
  let barClass;

  if (loading) {
    barClass = `${styles.bar} ${styles.loading}`;
  } else {
    barClass = styles.bar;
  }

  return (
    <header className={styles.header}>
      <div>
        <img src={"/logo.svg"} alt="Gradian Logo"></img>
        <h1>Gradian</h1>
      </div>
      <div>
        <Link to="/join">Join</Link>
        <Link to="/create">Create</Link>
      </div>
      <div className={barClass}></div>
    </header>
  );
}
