# PRD 06 — Teststrategie

## Ziele

- Schnell genug für die lokale Entwicklung (volle Suite < 5 s ohne Netz).
- Keine echten Provider-API-Calls in Standard-CI.
- Hohe Vertrauenswürdigkeit für das Verhalten am Rand: Auflösungs-Reihenfolge,
  ENV-Komposition, Datei-Permissions.

## Werkzeuge

- `pytest` als Runner.
- `pytest-mock` für Mock/Patch-Komfort.
- `pytest-asyncio` nur, falls in der HTTP-Schicht async eingesetzt wird
  (Default: synchrones `httpx.Client`).
- `respx` für HTTP-Mocking gegen `httpx`.
- `pyfakefs` (oder `tmp_path` + Fixtures) für Datei-Tests. Wir bevorzugen
  echte temp-Dateien (`tmp_path`), weil das Permissions-Verhalten verifiziert
  werden muss.
- `freezegun` für Cache-TTL-Tests.

## Test-Pyramide

### Unit-Tests

Stark gewichtet. Liegen in `tests/unit/`, ein Verzeichnis pro Source-Modul.

Pflicht-Abdeckung:

- **Config-Parsing**: gültige und ungültige YAMLs, Pydantic-Fehlermeldungen.
- **ENV-Interpolation**: `${VAR}`, `${VAR:-default}`, fehlende Variable,
  rekursive Verschachtelung (muss abgewiesen werden).
- **Permissions-Check**: zu lockere Modes triggern Warnung.
- **State-Datei**: Read-Write-Roundtrip, korrupte Datei, atomares Schreiben.
- **Auflösungs-Reihenfolge**: parametrisierte Tests für jede Kombination
  aus Flag, `--use-last-*`, `leitum.yaml` (Project-Config), Default, State,
  Dialog. Zusätzlich:
  - Project-Config pinnt → kein Dialog für gepinnte Slots.
  - Project-Config + CLI-Flag im selben Slot → CLI gewinnt.
  - Project-Config + `--no-project-config` → Project-Config wirkungslos.
  - Project-Config referenziert unbekannten Provider → Exit 3.
  - Project-Config + `--project-config <path>` zusammen mit
    `--no-project-config` → Exit 2.
- **Modell-Discovery**: YAML-Vorrang, Cache-Hit, Cache-Miss, Cache-Stale,
  Netz-Fehler.
- **Forced Refresh**: `-r`/`--refresh` invalidiert den Cache und löst eine
  Discovery aus, auch wenn der Cache frisch wäre; bei YAML-gepinntem
  Provider wird die Flag mit Warnung ignoriert. Die zugrunde liegende
  Discovery-Funktion akzeptiert ein `force=True` und triggert den
  HTTP-Call unabhängig vom Cache.
- **ENV-Komposition**: Tabelle aus PRD 04 wird durchgegangen, plus
  `extra_env`-Override-Logik: `project.extra_env` schlägt
  `provider.extra_env` bei gleichem Key, beide dürfen jedoch nicht die
  von leitum verwalteten Pflicht-Variablen (`ANTHROPIC_BASE_URL`,
  Auth-Var, Modell-ENV-Vars) überschreiben.
- **Pass-Through-Parsing**: `typer.allow_extra_args`-Verhalten mit jedem
  Beispiel aus PRD 02.

### Integrations-Tests

`tests/integration/`. Komponieren mehrere Module, ohne echtes Netz und ohne
echtes `claude`.

- **End-to-end mit fake-claude**: eine Fixture stellt ein temporäres
  Verzeichnis mit einem ausführbaren `claude`-Shell-Script in `PATH` bereit,
  das alle Argumente und relevante ENV-Variablen als JSON nach `stdout`
  schreibt. Der Test parsed das JSON und prüft.
- **HTTP-Discovery**: `respx` mockt `/v1/models` mit OpenAI-Format,
  Edge-Cases (leeres `data`, 401, 500).
- **doctor-Befehl**: synthetische Setups (gute Konfig, kaputte Konfig,
  fehlendes Token-ENV) → erwartete Exit-Codes und Output-Marker.

### Snapshot/Goldene Tests

- Hilfetexte (`leitum --help`, `leitum claude --help`, je Subcommand) als
  Snapshot. Bei Änderung muss das Snapshot bewusst aktualisiert werden.

### Interaktive Auswahl

Die `questionary`-Dialoge sind dünn — der eigentliche Auswahl-Algorithmus
sitzt in einer reinen Funktion, die testbar ist (Input: verfügbare Modelle,
Defaults, State, Flags → Output: gewählte Modelle). Tests laufen gegen diese
Funktion, nicht gegen das TTY-Frontend. Das Frontend bekommt einen einzelnen
Smoke-Test mit gemocktem `questionary`.

## Test-Fixtures

`tests/conftest.py` stellt zentral bereit:

- `tmp_config_dir`: temp-`~/.config/leitum/` mit anpassbarem Inhalt.
- `tmp_state_dir`: temp-State-Dir.
- `fake_claude(tmp_path) -> Path`: legt ein Executable an, das Args + ENV
  als JSON ausgibt, und prependet dessen Verzeichnis im `PATH`.
- `requesty_provider`: Default-Provider-Dict für Parametrisierung.
- `frozen_now`: `freezegun`-Fixture, fest auf einem reproduzierbaren Zeitpunkt.

## Style und Qualität

- Tests verwenden Arrange-Act-Assert mit Leerzeilen-Trennung.
- Eine Assertion pro Konzept; mehrere Assertions ok, aber keine "Mega-Tests".
- Parametrisierung mit `pytest.mark.parametrize` für Tabellentests.
- Tests sind reproducerbar (kein `time.sleep`, keine echten Sockets).

## CI

- GitHub Actions, ein Workflow `ci.yml`:
  - Matrix Python {3.11, 3.12, 3.13}.
  - Runner: `macos-latest` und `ubuntu-latest`.
  - Schritte: `uv sync`, `uv run ruff check`, `uv run ruff format --check`,
    `uv run mypy src`, `uv run pytest`.
- Release-Workflow `release.yml` für PyPI (siehe PRD 07).

## Manuelle Akzeptanzkriterien (Definition of Done für v1)

1. `leitum init` legt einwandfreie Beispiel-Konfig an.
2. `leitum --dry-run claude` zeigt erwartetes ENV + Exec-Zeile mit Requesty.
3. Mit `REQUESTY_API_KEY` gesetzt und vorhandenem `claude`-Binary startet
   `leitum claude` Claude Code erfolgreich.
4. Auswahl wird in `state.yaml` persistiert und beim nächsten Aufruf als
   Vorbelegung gezeigt.
5. `leitum doctor` meldet `[ ok ]` auf einem frisch initialisierten System.
6. Alle Tests grün, alle Linter ohne Findings.
