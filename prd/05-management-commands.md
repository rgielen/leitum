# PRD 05 — Management-Subcommands

Die Management-Subcommands sind alles, was nicht `leitum claude` ist. Sie
helfen beim Einrichten, Pflegen und Diagnostizieren der Konfiguration.

Alle Management-Subcommands reichen **nichts** an externe Binaries durch und
haben jeweils eigene, abgeschlossene Argument-Parser.

## `leitum init`

Erstinstallation für neue User.

Verhalten:

1. Lege `${XDG_CONFIG_HOME:-$HOME/.config}/leitum/` mit Mode `0700` an.
2. Wenn `api-providers.yaml` nicht existiert: erstelle sie mit einer
   kommentierten Beispielkonfiguration (Requesty als Provider, Token als
   `${REQUESTY_API_KEY}`-Platzhalter, ohne `models`-Liste). Mode `0600`.
3. Wenn die Datei existiert: nichts überschreiben, Hinweis ausgeben.
4. Schreibe leere `state.yaml` (nur `schema_version: 1`), falls keine
   existiert.
5. Drucke zum Schluss einen kurzen Hinweis: "Set REQUESTY_API_KEY in your
   shell and run `leitum claude` to start."

Flags:

- `--force`: existierende Dateien überschreiben (mit Confirm-Prompt, außer
  `--yes` zusätzlich).
- `--provider <name>`: statt Requesty einen anderen vordefinierten
  Provider-Stub schreiben. v1 unterstützt nur `requesty`.

## `leitum provider`

Subgroup für Provider-Verwaltung.

### `leitum provider list`

Tabelle der definierten Provider, eine Zeile pro Provider:

```
NAME        BASE URL                       AUTH ENV VAR           MODELS
requesty *  https://router.requesty.ai     ANTHROPIC_AUTH_TOKEN   3 (yaml)
openrouter  https://openrouter.ai/api      ANTHROPIC_AUTH_TOKEN   42 (cached)
```

Markierungen:

- `*` neben dem Namen = aktuell `last_provider`.
- "yaml" = Modelle aus `provider.models`, "cached" = aus Modell-Cache,
  "api" = wird beim nächsten Launch frisch geholt, "—" = keine Liste
  verfügbar.

### `leitum provider show <name>`

Komplette Konfiguration für einen Provider in YAML-Form, **mit redacted
Token** (`token: ***redacted***`). Zusätzlich am Ende:

- Pfad zur Quelldatei.
- Modell-Quelle (yaml/cache/api).
- Cache-Alter, falls cache.

`--reveal-token`: zeigt den Klartext-Token (aufgelöst). Erfordert Bestätigung
und schreibt eine Warnung auf stderr.

### `leitum provider add`

Interaktiver Wizard. Fragt nach:

1. `name` (Pflicht, Validierung wie in PRD 01).
2. `base_url` (Pflicht).
3. Token-Quelle: "Environment variable reference" (Default,
   `${VAR}`-Syntax) oder "Inline secret" (mit deutlicher Warnung).
4. Bei ENV: Name der Variable. Default `<NAME>_API_KEY`.
5. `auth.env_var`: select aus `ANTHROPIC_AUTH_TOKEN` (Default) und
   `ANTHROPIC_API_KEY`.
6. Optional: "Test the provider now?" → führt einen `GET /v1/models` aus
   und meldet OK/Fehler.

Schreibt am Ende den neuen Eintrag ans Ende der `api-providers.yaml`,
unter Erhalt aller Kommentare (deshalb `ruamel.yaml`).

### `leitum provider remove <name>`

Entfernt den Provider nach Confirm-Prompt. Wenn der entfernte Provider
gerade `last_provider` ist, wird `last_provider` in `state.yaml` geleert.
`--yes` überspringt den Prompt.

## `leitum refresh [--provider <name>]`

Löscht den Modell-Cache.

- Ohne `--provider`: alle Provider.
- Mit `--provider`: nur den genannten.

Anschließend wird sofort ein `GET /v1/models` versucht und das Ergebnis
gecacht. Fehler werden gemeldet, aber der Befehl selbst gibt nur dann
Exit ≠ 0, wenn keinerlei Provider erfolgreich war.

## `leitum doctor`

Sanity-Check-Suite. Reihenfolge der Checks:

1. **Pfade & Permissions**
   - Existieren `~/.config/leitum/` und Inhalt mit `0700`/`0600`?
2. **Konfig-Validierung**
   - `api-providers.yaml` parsbar, Schema gültig?
   - Falls `$CWD/leitum.yaml` existiert (oder per `--project-config` gesetzt):
     parsbar, Schema gültig, referenzierter Provider in `api-providers.yaml`
     vorhanden? Verdacht auf eingecheckte Secrets in `extra_env` (Werte mit
     ≥24 Zeichen ohne `${VAR}`-Interpolation) → Warnung mit Hinweis.
3. **State-Datei**
   - `state.yaml` parsbar?
   - Verweist `last_provider` auf einen existierenden Provider?
   - Letzte Modelle pro Provider noch in der Modell-Liste?
4. **ENV-Variablen**
   - Sind alle in `auth.token`/`extra_env` referenzierten Variablen gesetzt?
5. **Modell-Discovery**
   - Pro Provider: Cache vorhanden? Falls nein, ein leichter HEAD/GET
     gegen `base_url` (kein Token nötig → Erreichbarkeit grob prüfen).
6. **Claude-Binary**
   - `claude` in `PATH`? Welche Version? (`claude --version` mit Timeout.)

Ausgabe: pro Check eine Zeile mit `[ ok ]`, `[warn]` oder `[fail]` + kurze
Erklärung. Am Ende Zusammenfassung. Exit 0 wenn keine `fail`, sonst 1.

`doctor` führt keine Korrekturen aus, schlägt aber pro Befund konkrete
Befehle vor.

## `leitum completions <shell>`

Druckt Shell-Completions auf stdout. Unterstützte Shells: `bash`, `zsh`,
`fish`. Realisiert via typer-native Completions.

User-Anwendung (manuell, Doku im README):

```bash
leitum completions zsh > ~/.zfunc/_leitum
```

## `leitum --version`

Druckt `leitum <semver>` (gelesen aus `importlib.metadata`). Kein Network-
Call.

## Konventionen für alle Management-Subcommands

- Englisch.
- Knappe stdout-Ausgabe, ausführliches Logging nur mit `--verbose`.
- Niemals Tokens im Klartext drucken, außer `provider show --reveal-token`
  mit explizitem Opt-In.
- Exit 0 bei Erfolg, sinnvolle Codes ab 1 bei Fehlern, gleiches Codeset wie
  in PRD 02 wo zutreffend.
