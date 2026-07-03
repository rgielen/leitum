import { Sequence } from "remotion";
import { Line, PromptLine } from "../../components/TermLine";
import { SelectMenu } from "../../components/SelectMenu";
import { TypeLine } from "../../components/TypeLine";
import { theme } from "../../theme";

// `leitum provider add` — pick the Ollama preset, confirm the details, test it.
export const ProviderAddAct: React.FC = () => (
  <>
    <TypeLine text="leitum provider add" startFrame={10} cps={17} />

    <Sequence from={56} layout="none">
      <SelectMenu
        question="Provider type:"
        choices={[
          "Ollama (local)",
          "LM Studio (local)",
          "llama.cpp (local)",
          "vLLM (local)",
          "Generic local (Anthropic-compat)",
          "Detect local providers…",
          "Custom (manual)",
        ]}
        selected={0}
        path={[0, 1, 2, 1, 0]}
        stepFrames={9}
        commitFrame={66}
      />
    </Sequence>

    <Sequence from={132} layout="none">
      <PromptLine q="Provider name (lowercase, kebab-case):" a="ollama" />
    </Sequence>
    <Sequence from={152} layout="none">
      <PromptLine q="Base URL:" a="http://localhost:11434" />
    </Sequence>
    <Sequence from={172} layout="none">
      <PromptLine q="Token value:" a="ollama" />
    </Sequence>
    <Sequence from={194} layout="none">
      <PromptLine q="Test the provider now (GET /v1/models)?" a="Yes" />
    </Sequence>
    <Sequence from={214} layout="none">
      <Line color={theme.green} style={{ marginTop: 8 }}>
        OK — 12 models returned.
      </Line>
    </Sequence>
    <Sequence from={232} layout="none">
      <Line>
        Provider '<span style={{ color: theme.accent }}>ollama</span>' added to
        ~/.config/leitum/api-providers.yaml.
      </Line>
    </Sequence>
  </>
);
