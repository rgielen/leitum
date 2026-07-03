import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { LogoMark } from "../components/LogoMark";
import { BRAND, MONO } from "../fonts";
import { theme } from "../theme";

const EASE = Easing.bezier(0.16, 1, 0.3, 1);

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();

  const logoOpacity = interpolate(frame, [2, 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const logoScale = interpolate(frame, [2, 26], [0.92, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE,
  });
  const pillOpacity = interpolate(frame, [16, 36], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const repoOpacity = interpolate(frame, [30, 50], [0, 1], {
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
        gap: 30,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 22,
          opacity: logoOpacity,
          scale: logoScale,
        }}
      >
        <LogoMark size={104} draw={1} gradId="outro-grad" />
        <span
          style={{
            fontFamily: BRAND,
            fontWeight: 600,
            fontSize: 92,
            color: theme.fg,
            letterSpacing: 1,
          }}
        >
          leitum
        </span>
      </div>

      <div
        style={{
          fontFamily: `${MONO}, monospace`,
          fontSize: 28,
          color: theme.fg,
          backgroundColor: "rgba(139,147,255,0.10)",
          border: `1px solid ${theme.accent}55`,
          borderRadius: 12,
          padding: "12px 24px",
          opacity: pillOpacity,
        }}
      >
        <span style={{ color: theme.accent }}>{"❯ "}</span>uvx leitum
      </div>

      <span
        style={{
          fontFamily: `${MONO}, monospace`,
          fontSize: 22,
          color: theme.dim,
          opacity: repoOpacity,
        }}
      >
        github.com/rgielen/leitum
      </span>
    </AbsoluteFill>
  );
};
