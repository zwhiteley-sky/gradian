import { ChangeEvent, useState } from "react";
import styles from "./Input.module.scss";

type InputState = {
  value: string;
  validity: InputValidity;
};

type InputValidity = InputInitial | InputValid | InputInvalid;
type InputInitial = { type: "initial" };
type InputValid = { type: "valid" };
type InputInvalid = { type: "invalid"; reason: string };

export default function Input({
  name,
  placeholder,
  onValidate,
}: {
  name: string;
  placeholder: string;
  onValidate: (value: string) => string | null;
}) {
  const [state, setState] = useState({
    value: "",
    validity: { type: "initial" },
  } as InputState);

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const invalidReason = onValidate(event.currentTarget.value);

    if (invalidReason) {
      setState({
        value: event.currentTarget.value,
        validity: {
          type: "invalid",
          reason: invalidReason,
        },
      });
      return;
    }

    setState({
      value: event.currentTarget.value,
      validity: { type: "valid" },
    });
  }

  let className = styles["rainbow-border"] + " ";

  switch (state.validity.type) {
    case "initial":
      className += styles.initial;
      break;

    case "valid":
      className += styles.valid;
      break;

    case "invalid":
      className += styles.invalid;
      break;
  }

  const element = (
    <>
      <div className={className}>
        <input
          name={name}
          placeholder={placeholder}
          value={state.value}
          onChange={handleChange}
        />
      </div>
      {state.validity.type == "invalid" && (
        <p className={styles["error-text"]}>{state.validity.reason}</p>
      )}
    </>
  );

  return {
    Element: element,
    setStale(reason: string) {
      setState({
        value: state.value,
        validity: {
          type: "invalid",
          reason,
        },
      });
    },
    value: state.value,
    valid: state.validity.type == "valid"
  };
}
