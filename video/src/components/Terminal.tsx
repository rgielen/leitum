import type { ReactNode } from "react";
import { AbsoluteFill } from "remotion";
import { MONO } from "../fonts";
import { theme } from "../theme";

// A macOS-style terminal window: traffic lights, centered title, flat dark body.
export const Terminal: React.FC<{ title?: string; children: ReactNode }> = ({
  title = "leitum — zsh",
  children,
}) => (
  <AbsoluteFill
    style={{
      backgroundColor: theme.bg,
      justifyContent: "center",
      alignItems: "center",
      fontFamily: `${MONO}, monospace`,
    }}
  >
    <div
      style={{
        width: 1120,
        borderRadius: 14,
        overflow: "hidden",
        border: `1px solid ${theme.border}`,
        boxShadow: "0 40px 90px rgba(0,0,0,0.55)",
      }}
    >
      <div
        style={{
          height: 46,
          backgroundColor: theme.chrome,
          display: "flex",
          alignItems: "center",
          paddingLeft: 20,
          position: "relative",
        }}
      >
        <div style={{ display: "flex", gap: 9 }}>
          {[theme.lights.red, theme.lights.yellow, theme.lights.green].map((c) => (
            <span
              key={c}
              style={{ width: 13, height: 13, borderRadius: "50%", backgroundColor: c }}
            />
          ))}
        </div>
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            textAlign: "center",
            color: theme.dim,
            fontSize: 15,
            pointerEvents: "none",
          }}
        >
          {title}
        </div>
      </div>
      <div
        style={{
          backgroundColor: theme.termBg,
          padding: "28px 32px",
          minHeight: 540,
          fontSize: 22,
          lineHeight: 1.55,
          color: theme.fg,
        }}
      >
        {children}
      </div>
    </div>
  </AbsoluteFill>
);
