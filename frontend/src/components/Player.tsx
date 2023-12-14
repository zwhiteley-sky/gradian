import Waiting from "./Waiting";
import { GamePlaying, GameRequest, useGame } from "../lib/Game";
import Table from "./Table";

export default function Player({ request }: { request: GameRequest }) {
  const game = useGame(request);

  if (game.type === "loading") return <div></div>;
  else if (game.type === "invalid") return <h1>Invalid game!</h1>;
  else if (game.type === "closed")
    return <h1>CLOSED! Reason: {game.reason}</h1>;
  else if (game.type === "waiting" || game.type === "starting") {
    return <Waiting game={game} />;
  } else {
    return <Table game={game as GamePlaying} />;
  }
}