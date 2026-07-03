# leitum demo video — storyboard & build state

Single source of truth for the demo video. **To resume after a context reset:**
read this file top to bottom, then run `td usage` in the repo root for live task
state. Task IDs below map to `td` issues. Update the checklist as scenes land.

## Goal

A ~33s terminal demo for the GitHub README hero, showing: `init` → `provider add`
(Ollama) → `claude` with provider + model selection → payoff (leitum rewired
Claude Code to the provider). Rendered as **MP4 master + optimized GIF**.

## Global settings

- Composition: 1280×720 @ 30fps. Final id: `LeitumDemo` (currently the showcase
  is id `Playground` in `Root.tsx` — rename during assembly, task td-1b1bad).
- Fonts: JetBrains Mono (terminal), Urbanist SemiBold (brand) via
  `@remotion/google-fonts` (`src/fonts.ts`).
- Palette: `src/theme.ts` (terminal tones + brand indigo `#8B93FF`).
- Design keeps flat colors (no gradients/blur in motion) so the GIF stays crisp
  and small.

## Base components (DONE)

`src/components/`: `Terminal` (window chrome), `TypeLine` (typing engine),
`Cursor`, `TermLine` (`Prompt` + `Line`), `SelectMenu` (questionary select with
walking `»` pointer + collapse). Helper `src/util/timing.ts` (`typedCount`).
Verified via stills.

## Scenes (exact text — do not re-derive; captured from the real CLI)

Use `~` paths (not tmp). Prompt symbol `❯` in accent. questionary `?` in cyan,
pointer `»`, collapsed form `? Question › value`.

### Scene 0 — Intro (~2.5s) · td-0c3ad4

Detour mark draws itself in (stroke dash-offset animation), wordmark `leitum`
fades in beside it, tagline below: **Launch Claude Code against any LLM router.**
Assets from `design/` (see td-41a2be).

### Scene 1 — `init` (~6s) · td-fd9c8c

```
❯ leitum init
Created ~/.config/leitum/api-providers.yaml
Created ~/.local/state/leitum/state.yaml

Set REQUESTY_API_KEY in your shell and run `leitum claude` to start.
```

### Scene 2 — `provider add` (Ollama) (~10s) · td-9e6a80

Full preset menu (trim to fit): Ollama (local), LM Studio (local), llama.cpp
(local), vLLM (local), Generic local (Anthropic-compat), Detect local providers…,
Custom (manual). Pointer lands on **Ollama (local)**.

```
❯ leitum provider add
? Provider type: › Ollama (local)
? Provider name (lowercase, kebab-case): ollama
? Base URL: http://localhost:11434
? Token value: ollama
? Test the provider now (GET /v1/models)? Yes
OK — 12 models returned.
Provider 'ollama' added to ~/.config/leitum/api-providers.yaml.
```

### Scene 3 — `claude` with selection + payoff (~12s) · td-b8d361

Provider picker (now 2 providers → dialog appears); then Start-model picker;
then the resolved env as the payoff.

```
❯ leitum claude
? Select API provider › requesty — https://router.requesty.ai
      requesty — https://router.requesty.ai
      ollama — http://localhost:11434
? Select models for requesty — Start  (--model) › Sonnet 4.5 (Requesty)
      (use Claude default)
      Sonnet 4.5 (Requesty)
      Opus 4.5 (Requesty)
      Haiku 4.5 (Requesty)

→ ANTHROPIC_BASE_URL    https://router.requesty.ai
→ ANTHROPIC_AUTH_TOKEN  ••••••••••••
→ model                 anthropic/claude-sonnet-4-5
  Launching Claude Code…
```

### Scene 4 — Outro (~3s) · td-acdf86

Logo + install line `uvx leitum` + `github.com/rgielen/leitum`.

## Timing plan (approx, 30fps — refine per scene)

| Scene | frames | ~sec |
|---|---|---|
| Intro | 0–75 | 2.5 |
| init | 75–255 | 6 |
| provider add | 255–555 | 10 |
| claude | 555–915 | 12 |
| outro | 915–1010 | 3 |

Between scenes: quick clear/fade (keep it snappy). Total ≈ 33s (~1010 frames).

## Assembly (td-1b1bad)

Each scene = its own component in `src/scenes/`. Main composition `src/Demo.tsx`
sequences them with `<Sequence from=…>`. Update `Root.tsx`: id `LeitumDemo`,
`durationInFrames` = total. Keep the `Playground` showcase or remove it.

## Render pipeline (td-ce1886)

```bash
cd video
npx remotion render LeitumDemo out/leitum-demo.mp4 --codec=h264
# GIF via ffmpeg palette (crisp, ~1000px, 15fps):
ffmpeg -y -i out/leitum-demo.mp4 -vf "fps=15,scale=1000:-1:flags=lanczos,palettegen=stats_mode=diff" out/palette.png
ffmpeg -y -i out/leitum-demo.mp4 -i out/palette.png -lavfi "fps=15,scale=1000:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3" out/leitum-demo.gif
```

Output targets (td-de8866): copy MP4 + GIF to `docs/assets/`, embed GIF at top of
root `README.md` (`![leitum demo](docs/assets/leitum-demo.gif)`). `video/out/` is
gitignored; committed outputs live under `docs/assets/`.

## Progress checklist

- [x] Scaffold Remotion in `video/` (Tailwind removed, google-fonts added)
- [x] Base components, stills verified
- [x] td-41a2be — copy logo/favicon assets into `video/public/brand/`
- [x] td-0c3ad4 — Intro scene (`scenes/Intro.tsx`, `components/LogoMark.tsx`)
- [x] td-fd9c8c — init act (`scenes/acts/InitAct.tsx`)
- [x] td-9e6a80 — provider add (Ollama) act (`scenes/acts/ProviderAddAct.tsx`)
- [x] td-b8d361 — claude act + payoff (`scenes/acts/ClaudeAct.tsx`)
- [x] td-acdf86 — Outro scene (`scenes/Outro.tsx`)
- [x] td-1b1bad — assembly: `Demo.tsx` (Intro→Terminal→Outro, crossfades), Root id `LeitumDemo`, DEMO_TOTAL=810f (~27s)
- [ ] td-ce1886 — render pipeline (MP4 + GIF) — IN PROGRESS
- [ ] td-de8866 — README embed + docs/assets

### Current state (for resume)

All scenes built + lint/tsc green + per-frame stills verified. Compositions in
`Root.tsx`: `LeitumDemo` (final, 810f), plus `Intro`/`Terminal`/`Outro` previews.
The 3 CLI acts play in one persistent `TerminalScene` (`ACT_INIT=150`,
`ACT_PROVIDER=210`, `ACT_CLAUDE=300`). Next: render MP4 then derive GIF (commands
above), copy to `docs/assets/`, embed in root README.

## Conventions / decisions

- Launch scene uses **requesty** (hero provider, nice model names); Ollama proves
  multi-provider in the picker.
- questionary accent recolored to brand indigo (not questionary's cyan) for the
  pointer/selection; the `?` mark stays cyan.
- Branch for the whole effort: `feat/demo-video` (logo `design/` + `video/` +
  README). Nothing committed to `main`.
