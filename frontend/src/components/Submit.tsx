import styles from "./Submit.module.scss";

export default function SubmitButton({
  text,
  disabled,
}: {
  text: string;
  disabled: boolean;
}) {
  let className;

  if (disabled) {
    className = `${styles["rainbow-border"]} ${styles.disabled}`;
  } else {
    className = styles["rainbow-border"];
  }

  return (
    <div className={className}>
      <input
        type="submit"
        className={styles["submit-button"]}
        value={text}
        disabled={disabled}
      />
    </div>
  );
}
