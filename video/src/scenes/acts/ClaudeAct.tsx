import { Sequence } from "remotion";
import { Line } from "../../components/TermLine";
import { SelectMenu } from "../../components/SelectMenu";
import { TypeLine } from "../../components/TypeLine";
import { theme } from "../../theme";

const EnvRow: React.FC<{ k: string; v: string; vColor?: string }> = ({
  k,
  v,
  vColor = theme.fg,
}) => (
  <div style={{ whiteSpace: "pre" }}>
    <span style={{ color: theme.accent }}>{"→ "}</span>
    <span style={{ color: theme.dim, display: "inline-block", width: "22ch" }}>{k}</span>
    <span style={{ color: vColor }}>{v}</span>
  </div>
);

// `leitum claude` — now two providers exist, so the picker appears; then the
// Start-model picker; then the resolved environment as the payoff.
export const ClaudeAct: React.FC = () => (
  <>
    <TypeLine text="leitum claude" startFrame={10} cps={17} />

    <Sequence from={46} layout="none">
      <SelectMenu
        question="Select API provider"
        choices={["requesty — https://router.requesty.ai", "ollama — http://localhost:11434"]}
        selected={0}
        path={[0, 1, 0]}
        stepFrames={9}
        commitFrame={54}
      />
    </Sequence>

    <Sequence from={112} layout="none">
      <SelectMenu
        question="Select models for requesty — Start  (--model)"
        choices={[
          "(use Claude default)",
          "Sonnet 4.5 (Requesty)",
          "Opus 4.5 (Requesty)",
          "Haiku 4.5 (Requesty)",
        ]}
        selected={1}
        path={[1, 2, 3, 1]}
        stepFrames={11}
        commitFrame={64}
      />
    </Sequence>

    <Sequence from={190} layout="none">
      <Line style={{ height: "0.6em" }} />
      <EnvRow k="ANTHROPIC_BASE_URL" v="https://router.requesty.ai" />
    </Sequence>
    <Sequence from={208} layout="none">
      <EnvRow k="ANTHROPIC_AUTH_TOKEN" v="••••••••••••" vColor={theme.dim} />
    </Sequence>
    <Sequence from={226} layout="none">
      <EnvRow k="model" v="anthropic/claude-sonnet-4-5" vColor={theme.accent} />
    </Sequence>
    <Sequence from={252} layout="none">
      <Line style={{ height: "0.6em" }} />
      <Line color={theme.green}>Launching Claude Code…</Line>
    </Sequence>
  </>
);
