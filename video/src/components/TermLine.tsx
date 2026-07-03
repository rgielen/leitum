import type { CSSProperties, ReactNode } from "react";
import { theme } from "../theme";

// The zsh prompt symbol.
export const Prompt: React.FC = () => (
  <span style={{ color: theme.accent, fontWeight: 700 }}>{"❯ "}</span>
);

// A single static terminal line. `whiteSpace: pre` preserves alignment spacing.
export const Line: React.FC<{
  children?: ReactNode;
  color?: string;
  style?: CSSProperties;
}> = ({ children, color = theme.fg, style }) => (
  <div style={{ whiteSpace: "pre", color, minHeight: "1.55em", ...style }}>
    {children}
  </div>
);

// An answered questionary text prompt: "? Question answer".
export const PromptLine: React.FC<{ q: string; a: string }> = ({ q, a }) => (
  <div style={{ whiteSpace: "pre", minHeight: "1.55em" }}>
    <span style={{ color: theme.cyan }}>{"? "}</span>
    <span style={{ color: theme.fg }}>{q + " "}</span>
    <span style={{ color: theme.accent }}>{a}</span>
  </div>
);
