import { interpolate } from "remotion";
import { theme } from "../theme";

// The Detour mark as inline SVG so it can be animated. `draw` (0..1) reveals the
// rerouting stroke via a normalized pathLength; the dimmed ghost route and the
// blocked-endpoint ring fade in near the end.
export const LogoMark: React.FC<{
  size?: number;
  draw?: number;
  variant?: "dark" | "light";
  gradId?: string;
}> = ({ size = 96, draw = 1, variant = "dark", gradId = "leitum-mark-grad" }) => {
  const ink = variant === "light" ? "#1C2230" : theme.fg;
  const off = 100 * (1 - Math.max(0, Math.min(1, draw)));
  const ghost = interpolate(draw, [0.55, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <svg width={size} height={size} viewBox="0 0 96 96" fill="none">
      <defs>
        <linearGradient id={gradId} x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor={ink} />
          <stop offset="1" stopColor={theme.accent} />
        </linearGradient>
      </defs>
      <line
        x1="14"
        y1="70"
        x2="86"
        y2="70"
        stroke={ink}
        strokeOpacity={0.16 * ghost}
        strokeWidth={8}
        strokeLinecap="round"
        strokeDasharray="0.5 15"
      />
      <circle
        cx="86"
        cy="70"
        r="5"
        stroke={ink}
        strokeOpacity={0.16 * ghost}
        strokeWidth={4}
      />
      <path
        d="M14 70 H40 V34 H78"
        stroke={`url(#${gradId})`}
        strokeWidth={11}
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={100}
        strokeDasharray={100}
        strokeDashoffset={off}
      />
      <path
        d="M69 24 L82 34 L69 44"
        stroke={theme.accent}
        strokeWidth={11}
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={100}
        strokeDasharray={100}
        strokeDashoffset={off}
      />
    </svg>
  );
};
