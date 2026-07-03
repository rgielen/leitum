import { useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

// A block cursor. Steady while typing; pass blink=true for the idle blink.
export const Cursor: React.FC<{ blink?: boolean; color?: string }> = ({
  blink = false,
  color = theme.fg,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const period = Math.max(1, Math.round(fps * 0.53));
  const visible = blink ? Math.floor(frame / period) % 2 === 0 : true;
  return (
    <span
      style={{
        display: "inline-block",
        width: "0.55em",
        height: "1.15em",
        backgroundColor: color,
        opacity: visible ? 0.9 : 0,
        transform: "translateY(0.22em)",
        borderRadius: 1,
      }}
    />
  );
};
