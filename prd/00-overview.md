# PRD 00 — Produktüberblick

## Ziel

`leitum` ist ein kleines CLI-Werkzeug in Python, das einen Coding-Agenten — in
v1 ausschließlich Claude Code — so startet, dass nicht die Anthropic-API direkt
genutzt wird, sondern ein konfigurierbarer alternativer LLM-Router/-Provider.
Vorbild sind `ollama launch` und `omlx launch`: der User stellt dem Befehl
`claude` ein `leitum` voran und bekommt damit ohne weitere Handgriffe die
gewünschte Provider-/Modell-Auswahl.

## Nutzer und Anwendungsfall

Primärer Nutzer ist ein:e Entwickler:in, der/die

- mehrere LLM-Provider/-Router parallel nutzt (z.B. Requesty, später
  OpenRouter, LiteLLM, lokales Ollama),
- pro Provider unterschiedliche Modelle für `--model`,
  `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`,
  `ANTHROPIC_DEFAULT_HAIKU_MODEL` setzen will,
- nicht jedes Mal ENV-Variablen von Hand exportieren oder Aliasse pflegen
  möchte,
- die letzte Auswahl beim nächsten Aufruf wieder vorgeschlagen bekommen will.

Sekundärer Anwendungsfall: scripted Aufrufe (`leitum -p req -m foo claude ...`)
ohne jegliche Interaktion.

## Erfolgsversprechen (User-Promise)

> `leitum claude` startet meinen Coding-Agenten mit dem Provider und den
> Modellen, die ich gerade brauche. Genau ein Wort vor `claude`, der Rest fühlt
> sich an wie Claude Code immer.

## Featureset v1

- Subcommand `leitum claude`, das nach erfolgreicher Provider- und
  Modellwahl das echte `claude`-Binary mit angepasstem Environment
  ausführt (siehe PRD 04).
- Provider in einer YAML-Datei (`api-providers.yaml`) konfigurierbar. Jeder
  Provider hat Name, Base-URL und Auth-Daten, optional eine Modell-Liste und
  Default-Modelle für die vier Slots (siehe PRD 01).
- Interaktive Auswahl per `questionary`, wenn nicht durch Flags oder durch
  Single-Option-Konfiguration eindeutig (siehe PRD 03).
- Pro Provider gemerkte letzte Auswahl (Provider und Modelle), persistiert in
  `state.yaml` (siehe PRD 01 und PRD 03).
- Projektlokale Konfiguration via `leitum.yaml` im aktuellen Verzeichnis,
  die zwischen State und CLI-Flags greift und damit reproduzierbare
  Repo-Vorgaben ermöglicht (siehe PRD 01 und PRD 03).
- Management-Befehle: `leitum init`, `leitum provider add|list|show|remove`,
  `leitum refresh`, `leitum doctor` (siehe PRD 05).
- `--dry-run` und `--verbose` für Sichtbarkeit (siehe PRD 04).
- Veröffentlichung auf PyPI und über einen eigenen Homebrew-Tap (siehe
  PRD 07).

## Bewusst nicht in v1

- Andere Agenten (copilot-cli, opencode, gemini-cli usw.).
- kubectl-artige benannte Kontexte/Profile. Nur die letzte Auswahl wird
  gemerkt.
- macOS-Keychain-Integration für Tokens (Backlog).
- GUI/TUI jenseits einfacher Auswahl-Prompts.
- Windows-Support. macOS ist Referenzplattform, Linux soll mitlaufen.

## Begriffe

- **Provider** — ein in `api-providers.yaml` definierter Eintrag mit Base-URL
  und Auth. Beispiel: `requesty`, `openrouter`, `local-ollama`.
- **Modell-Slot** — eine der vier Rollen, in denen Claude Code Modelle
  verwendet: START (`--model`), OPUS (`ANTHROPIC_DEFAULT_OPUS_MODEL`),
  SONNET (`ANTHROPIC_DEFAULT_SONNET_MODEL`),
  HAIKU (`ANTHROPIC_DEFAULT_HAIKU_MODEL`).
- **State** — die zuletzt verwendete Auswahl, persistiert in `state.yaml`.
  Pro Provider werden die letzten vier Modelle separat gespeichert.
- **Project-Config** — `leitum.yaml` im aktuellen Arbeitsverzeichnis.
  Eingecheckte Repo-Vorgabe für Provider und Modell-Slots; gewinnt gegen
  `state.yaml`, verliert gegen CLI-Flags. Enthält **niemals** Tokens.
- **Pass-Through** — alles, was nach dem Subcommand-Namen `claude` steht, wird
  unverändert an das `claude`-Binary übergeben.

## PRD-Karte

| Bereich                       | PRD                                  |
| ----------------------------- | ------------------------------------ |
| Konfigurations- und State-Datei | `01-configuration.md`              |
| CLI, Flags, Pass-Through      | `02-cli.md`                          |
| Auswahl von Provider & Modell | `03-selection-flows.md`              |
| Launch von Claude Code        | `04-launch.md`                       |
| Management-Subcommands        | `05-management-commands.md`          |
| Teststrategie                 | `06-testing.md`                      |
| Packaging und Doku            | `07-packaging-and-docs.md`           |

## Nicht-funktionale Vorgaben

- Sprache der Code-Doku, Commits, PRs, Issues: Englisch.
- Sprache der PRDs: Deutsch.
- Python 3.11+.
- Reference-Plattform macOS (aktuell), Linux soll mitlaufen.
- Keine Secrets in Logs.
- Konfig-Dateien mit Mode `0600`.
- `leitum` bleibt für den User binär identisch zur Erfahrung, `claude` direkt
  aufzurufen — abgesehen von der Provider-/Modell-Vorbereitung.
