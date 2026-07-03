import type { ReactNode } from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { Intro } from "./scenes/Intro";
import { Outro } from "./scenes/Outro";
import { TerminalScene, TERMINAL_TOTAL } from "./scenes/TerminalScene";
import { theme } from "./theme";

const INTRO_LEN = 175;
const OUTRO_LEN = 115;
const OVERLAP = 12; // crossfade overlap between scenes

const TERMINAL_FROM = INTRO_LEN - OVERLAP;
const OUTRO_FROM = TERMINAL_FROM + TERMINAL_TOTAL - OVERLAP;
export const DEMO_TOTAL = OUTRO_FROM + OUTRO_LEN;

// Fades a scene in at its start and out at its end (crossfade with neighbours).
const Fade: React.FC<{ len: number; children: ReactNode }> = ({ len, children }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [0, OVERLAP, len - OVERLAP, len],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

export const Demo: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: theme.bg }}>
    <Sequence durationInFrames={INTRO_LEN} layout="none">
      <Fade len={INTRO_LEN}>
        <Intro />
      </Fade>
    </Sequence>
    <Sequence from={TERMINAL_FROM} durationInFrames={TERMINAL_TOTAL} layout="none">
      <Fade len={TERMINAL_TOTAL}>
        <TerminalScene />
      </Fade>
    </Sequence>
    <Sequence from={OUTRO_FROM} durationInFrames={OUTRO_LEN} layout="none">
      <Fade len={OUTRO_LEN}>
        <Outro />
      </Fade>
    </Sequence>
  </AbsoluteFill>
);
