import "./index.css";
import { Composition } from "remotion";
import { Demo, DEMO_TOTAL } from "./Demo";
import { Intro } from "./scenes/Intro";
import { Outro } from "./scenes/Outro";
import { TerminalScene, TERMINAL_TOTAL } from "./scenes/TerminalScene";

const W = 1280;
const H = 720;
const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="LeitumDemo"
        component={Demo}
        durationInFrames={DEMO_TOTAL}
        fps={FPS}
        width={W}
        height={H}
      />
      {/* Scene previews for isolated iteration in Studio */}
      <Composition id="Intro" component={Intro} durationInFrames={175} fps={FPS} width={W} height={H} />
      <Composition
        id="Terminal"
        component={TerminalScene}
        durationInFrames={TERMINAL_TOTAL}
        fps={FPS}
        width={W}
        height={H}
      />
      <Composition id="Outro" component={Outro} durationInFrames={115} fps={FPS} width={W} height={H} />
    </>
  );
};
