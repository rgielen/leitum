# PRD 07 — Packaging, Veröffentlichung und Dokumentation

## Projektstruktur

```
leitum/
├── CLAUDE.md
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── src/
│   └── leitum/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config/
│       ├── state.py
│       ├── providers/
│       ├── selection/
│       ├── launch.py
│       └── commands/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── docs/
│   ├── index.md
│   ├── getting-started.md
│   ├── configuration.md
│   ├── providers/
│   │   └── requesty.md
│   ├── commands.md
│   └── troubleshooting.md
└── prd/
    └── *.md (dieses Verzeichnis)
```

## Build und Veröffentlichung auf PyPI

### `pyproject.toml`

- Build-Backend: `hatchling`.
- `[project]`-Metadaten: `name = "leitum"`, `requires-python = ">=3.11"`,
  Description, License (Apache-2.0), Keywords (`cli`, `claude-code`, `llm`,
  `router`).
- Runtime-Dependencies:
  - `typer>=0.12`
  - `questionary>=2.0`
  - `pydantic>=2.7`
  - `ruamel.yaml>=0.18`
  - `httpx>=0.27`
  - `rich>=13` (für hübsche Hilfetexte und Tabellen)
- Entry-Point: `leitum = "leitum.cli:app"` als `[project.scripts]`.
- Dev-Dependencies in `[dependency-groups]` (PEP 735) als `dev`:
  pytest, pytest-mock, respx, freezegun, ruff, mypy.

### Versionierung

- Semantic Versioning. v1 startet bei `0.1.0` (Pre-1.0, da öffentliche
  API noch fluide).
- Tags: `vMAJOR.MINOR.PATCH`. Tag triggert Release-Workflow.

### Release-Workflow

`.github/workflows/release.yml`:

1. Auf Tag-Push (`v*`).
2. `uv build` → `dist/`.
3. `pypa/gh-action-pypi-publish` mit Trusted Publishing
   (OIDC, kein Token-Secret).
4. GitHub-Release mit Changelog-Snippet (siehe unten).

### Changelog

`CHANGELOG.md`, Keep-a-Changelog-Format. Jede merge-fähige PR fügt einen
Eintrag unter `## [Unreleased]` ein. Release-Tag bewegt die Einträge in einen
versionierten Abschnitt.

## Ausführung via uvx

Sobald `leitum` auf PyPI ist:

```bash
uvx leitum --version
uvx leitum claude
```

Der Entry-Point sorgt dafür, dass `uvx` direkt einen funktionsfähigen
Befehl bekommt. Keine zusätzlichen Schritte in `pyproject.toml` nötig.

## Homebrew

Eigener Tap: `homebrew-leitum` (Repo-Name folgt der Konvention).

`Formula/leitum.rb` baut die Formel aus dem PyPI-Tarball auf:

- `desc`, `homepage`, `url` (PyPI Source-Dist), `sha256`.
- `depends_on "python@3.12"`.
- `virtualenv_install_with_resources` für saubere Isolation.

Installation für User:

```bash
brew tap <owner>/leitum
brew install leitum
```

Pro Release wird die Formula automatisch gebumpt: ein Workflow im Tap zieht
die PyPI-Metadaten, ersetzt URL/SHA, eröffnet eine PR.

Homebrew-Core-Submission ist für später; v1 bleibt im Tap.

## Dokumentation

### Sprache

Englisch — wie für die gesamte Projekt-Dokumentation festgelegt (siehe
`CLAUDE.md`). Einzige Ausnahme: PRDs in `prd/`.

### README.md (Pflicht für v1)

Struktur:

1. **One-liner & Badges**: PyPI-Version, License, CI-Status.
2. **What is leitum?** — 2–3 Sätze Use-Case.
3. **Install** — `uvx leitum`, `pip install leitum`, `brew install`.
4. **Quickstart** — `leitum init`, ENV setzen, `leitum claude`.
5. **Configuration** — Link auf `docs/configuration.md`, Mini-Beispiel.
6. **CLI Reference** — Top-Flags + Subcommands, Link auf
   `docs/commands.md`.
7. **Providers** — Verlinkt provider-spezifische Seiten in `docs/providers/`.
8. **Troubleshooting** — Verlinkt auf `docs/troubleshooting.md`.
9. **Contributing** — Hinweis auf `CLAUDE.md` und PRDs.
10. **License** — Apache 2.0.

Die README muss aus sich heraus verständlich sein — sie ist die GitHub-
Landing-Page.

### docs/ — vertieftes Material

- `getting-started.md`: Schritt-für-Schritt durch den ersten Launch, mit
  echtem Requesty-Beispiel.
- `configuration.md`: vollständige Schema-Referenz für
  `api-providers.yaml`. Spiegelt PRD 01, aber für End-User formuliert.
- `commands.md`: pro Subcommand ein Abschnitt mit Optionen und Beispielen.
- `providers/requesty.md`: provider-spezifische Hinweise (Auth-ENV-Var,
  Modell-Naming, Link auf Requesty-Doku).
- `troubleshooting.md`: häufige Fehlerbilder + Fixes; `leitum doctor`-
  Output erklärt.

### Auto-Doku aus Help-Texten

`leitum --help` und alle Subcommand-Helps werden über einen Skript-Schritt
in die `docs/commands.md` gerendert (`mkdocs` optional in einer späteren
Phase). v1 reicht Markdown direkt im Repo.

### Style

- Reines GitHub-Markdown, keine externen Mermaid-Server, keine Bilder die
  außerhalb des Repos liegen.
- Codeblöcke mit Sprachen-Tags.
- Wo immer möglich: copy-pastable Beispiele.

## Lizenz

Apache 2.0. Vollständiger Lizenztext als `LICENSE` im Root. Zusätzlich
`NOTICE` im Root (auch leer zulässig, aber empfohlen, sobald Drittinhalte
auftauchen). SPDX-Identifier `Apache-2.0` in `pyproject.toml`. Copyright-
Header in den Quelldateien sind nicht verpflichtend, aber begrüßenswert:

```
# Copyright <year> <copyright holder>
# SPDX-License-Identifier: Apache-2.0
```

## Compliance und Sicherheit

- README enthält einen Hinweis auf die Token-Handling-Praxis (ENV-Refs
  bevorzugen, niemals Tokens commiten).
- `SECURITY.md` mit Kontaktadresse für Vulnerability-Reports.
- Dependabot (GitHub-nativ) für Dependency-Updates.

## Roadmap (sichtbarer Backlog)

In `docs/roadmap.md`, hervorhebbar in der README:

- Weitere Provider-Presets (OpenRouter, LiteLLM, Ollama).
- macOS-Keychain-Integration für Tokens.
- Benannte Kontexte (kubectl-style).
- Andere Agenten: `leitum copilot`, `leitum opencode`.
- Homebrew-Core-Submission.
