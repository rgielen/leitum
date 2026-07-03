import { Sequence } from "remotion";
import { Terminal } from "../components/Terminal";
import { ClaudeAct } from "./acts/ClaudeAct";
import { InitAct } from "./acts/InitAct";
import { ProviderAddAct } from "./acts/ProviderAddAct";

// One persistent terminal window; each CLI act plays in sequence and the screen
// "clears" between them (the previous act unmounts). Act lengths in frames:
export const ACT_INIT = 180;
export const ACT_PROVIDER = 285;
export const ACT_CLAUDE = 340;

export const TERMINAL_TOTAL = ACT_INIT + ACT_PROVIDER + ACT_CLAUDE;

export const TerminalScene: React.FC = () => (
  <Terminal>
    <Sequence durationInFrames={ACT_INIT} layout="none">
      <InitAct />
    </Sequence>
    <Sequence from={ACT_INIT} durationInFrames={ACT_PROVIDER} layout="none">
      <ProviderAddAct />
    </Sequence>
    <Sequence from={ACT_INIT + ACT_PROVIDER} durationInFrames={ACT_CLAUDE} layout="none">
      <ClaudeAct />
    </Sequence>
  </Terminal>
);
