import { useCurrentFrame } from "remotion";
import { theme } from "../theme";

export type Choice = { label: string; note?: string };

// A questionary-style single-select. The pointer walks the indices in `path`
// (one step every `stepFrames`), then at `commitFrame` the whole prompt
// collapses to the chosen value — mirroring questionary's show_selected.
export const SelectMenu: React.FC<{
  question: string;
  choices: (string | Choice)[];
  selected: number;
  path?: number[];
  startFrame?: number;
  stepFrames?: number;
  commitFrame: number;
  hint?: string;
}> = ({
  question,
  choices,
  selected,
  path,
  startFrame = 0,
  stepFrames = 12,
  commitFrame,
  hint = "(Use arrow keys)",
}) => {
  const frame = useCurrentFrame();
  const norm: Choice[] = choices.map((c) => (typeof c === "string" ? { label: c } : c));
  const seq = path && path.length > 0 ? path : [selected];

  if (frame >= commitFrame) {
    return (
      <div style={{ whiteSpace: "pre" }}>
        <span style={{ color: theme.cyan }}>{"? "}</span>
        <span style={{ color: theme.fg }}>{question + " "}</span>
        <span style={{ color: theme.dim }}>{"› "}</span>
        <span style={{ color: theme.accent }}>{norm[selected].label}</span>
      </div>
    );
  }

  const step = Math.floor(Math.max(0, frame - startFrame) / stepFrames);
  const ptr = seq[Math.min(step, seq.length - 1)];

  return (
    <div style={{ whiteSpace: "pre" }}>
      <div>
        <span style={{ color: theme.cyan }}>{"? "}</span>
        <span style={{ color: theme.fg }}>{question}</span>
        <span style={{ color: theme.dim }}>{"  " + hint}</span>
      </div>
      {norm.map((c, i) => {
        const on = i === ptr;
        return (
          <div
            key={i}
            style={{
              whiteSpace: "pre",
              display: "flex",
              backgroundColor: on ? theme.selectBg : "transparent",
              borderRadius: 6,
              padding: "1px 6px",
              marginLeft: -6,
            }}
          >
            <span style={{ color: theme.accent }}>{on ? "» " : "  "}</span>
            <span style={{ color: on ? theme.accent : theme.fg }}>{c.label}</span>
            {c.note ? <span style={{ color: theme.dim }}>{"  " + c.note}</span> : null}
          </div>
        );
      })}
    </div>
  );
};
