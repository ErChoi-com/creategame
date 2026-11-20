import type { GameApi, Options, Status } from '../api';

/** Everything a screen or flow step needs to talk about the current run. */
export interface Game {
  id: string;
  seed: number;
  intro: string;
  ambition: string;
  api: GameApi;
}

export interface FlowBase {
  game: Game;
  options: Options;
  status: Status;
  /** One line for the hub's "what's happening" card once the flow ends. */
  outcome?: string;
}
