import { Sequence } from "remotion";
import { Line } from "../../components/TermLine";
import { TypeLine } from "../../components/TypeLine";
import { theme } from "../../theme";

// `leitum init` — creates the config + state files, then points at the next step.
export const InitAct: React.FC = () => (
  <>
    <TypeLine text="leitum init" startFrame={10} cps={17} />
    <Sequence from={44} layout="none">
      <Line>Created ~/.config/leitum/api-providers.yaml</Line>
    </Sequence>
    <Sequence from={60} layout="none">
      <Line>Created ~/.local/state/leitum/state.yaml</Line>
    </Sequence>
    <Sequence from={86} layout="none">
      <Line style={{ height: "0.9em" }} />
      <Line>
        Set <span style={{ color: theme.accent }}>REQUESTY_API_KEY</span> in your shell
        and run <span style={{ color: theme.accent }}>leitum claude</span> to start.
      </Line>
    </Sequence>
  </>
);
