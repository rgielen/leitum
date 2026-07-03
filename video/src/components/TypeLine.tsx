import { useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { typedCount } from "../util/timing";
import { Cursor } from "./Cursor";
import { Prompt } from "./TermLine";

// Types out `text` one character at a time. With `active`, keeps a blinking
// cursor after the line finishes (i.e. this is the current input line).
export const TypeLine: React.FC<{
  text: string;
  startFrame?: number;
  cps?: number;
  prompt?: boolean;
  active?: boolean;
  color?: string;
}> = ({
  text,
  startFrame = 0,
  cps = 24,
  prompt = true,
  active = false,
  color = theme.fg,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = typedCount(frame, startFrame, text.length, fps, cps);
  const started = frame >= startFrame;
  const typing = started && n < text.length;
  const showCursor = typing || (active && n >= text.length);
  return (
    <div style={{ whiteSpace: "pre", color, minHeight: "1.55em" }}>
      {prompt ? <Prompt /> : null}
      <span>{started ? text.slice(0, n) : ""}</span>
      {showCursor ? <Cursor blink={!typing} /> : null}
    </div>
  );
};
