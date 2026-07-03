import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { LogoMark } from "../components/LogoMark";
import { BRAND, MONO } from "../fonts";
import { theme } from "../theme";

const EASE = Easing.bezier(0.16, 1, 0.3, 1);

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();

  const draw = interpolate(frame, [6, 48], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE,
  });
  const wordOpacity = interpolate(frame, [34, 60], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const wordShift = interpolate(frame, [34, 60], [18, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE,
  });
  const tagOpacity = interpolate(frame, [64, 92], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.bg,
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        gap: 26,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 26 }}>
        <LogoMark size={132} draw={draw} gradId="intro-grad" />
        <span
          style={{
            fontFamily: BRAND,
            fontWeight: 600,
            fontSize: 116,
            color: theme.fg,
            letterSpacing: 1,
            opacity: wordOpacity,
            translate: `0 ${wordShift}px`,
          }}
        >
          leitum
        </span>
      </div>
      <span
        style={{
          fontFamily: `${MONO}, monospace`,
          fontSize: 30,
          color: "#AEB6C2",
          opacity: tagOpacity,
        }}
      >
        Launch Claude Code against any LLM router.
      </span>
    </AbsoluteFill>
  );
};
