# PRD 04 — Launch von Claude Code

## Zweck

Nachdem Provider und Modelle aufgelöst sind (siehe PRD 02 und PRD 03),
startet `leitum claude` das echte `claude`-Binary mit einem speziell
zusammengesetzten Environment.

## Ablauf

1. Konfigurations- und State-Dateien laden (PRD 01).
2. Argumente parsen, Pass-Through-Args extrahieren (PRD 02).
3. Provider und Modelle auflösen (PRD 03).
4. Sub-Environment bauen (siehe unten).
5. State persistieren (PRD 03).
6. `claude` exec'en (siehe unten).

## Projektlokale Secrets: `.leitumenv`

Vor dem Laden der Konfiguration sucht `leitum claude` im aktuellen
Arbeitsverzeichnis nach einer Datei namens `.leitumenv`. Ist sie vorhanden,
wird sie als Bash-Skript gesourct. Die dabei entstehenden Variablenwerte — inkl.
Command-Substitutions wie `$(op read ...)` — werden in `os.environ` injiziert,
bevor die YAML-Konfiguration gelesen wird, sodass `${VAR}`-Interpolation in
`api-providers.yaml` und `leitum.yaml` darauf zugreifen kann.

**Sicherheitshinweis:** Da die Datei als Shell-Code ausgeführt wird, darf
`.leitumenv` nur in vertrauenswürdigen Repositories verwendet werden. Sie soll
niemals in die Versionskontrolle eingecheckt werden.

### Regeln

- Nur reguläre Dateien werden verarbeitet; Verzeichnisse und fehlende Dateien
  werden still ignoriert.
- Bash wird mit `set -a` gestartet, sodass alle Zuweisungen automatisch
  exportiert werden — `export`-Präfix ist optional.
- Shell-Umgebung hat Vorrang: ein bereits gesetzter Wert wird nicht
  überschrieben.
- Malformed Lines (kein `=`-Zeichen) lösen mit `--verbose` eine Warnung aus
  (Inhalt wird nicht geloggt).
- `--no-dotenv` deaktiviert das Laden für einen einzelnen Aufruf.
- Werte werden niemals in Logs oder `--dry-run`-Ausgaben angezeigt.

### Kompositionsreihenfolge (erweitert)

0. `.leitumenv` sourcing: Variablen in `os.environ` setzen (shell-Werte haben
   Vorrang).

Danach folgen die bestehenden Schritte 1–6 (siehe unten).

## Sub-Environment

Ausgangspunkt: vollständige Kopie des aktuellen Prozess-Environments (inklusive
der in Schritt 0 gesetzten `.leitumenv`-Werte).

Dann werden gezielt Einträge gesetzt, ergänzt oder entfernt:

| Variable                          | Quelle                                    | Wann gesetzt                                       |
| --------------------------------- | ----------------------------------------- | -------------------------------------------------- |
| `ANTHROPIC_BASE_URL`              | `provider.base_url`                       | immer.                                             |
| `<provider.auth.env_var>`         | `provider.auth.token` (nach Interpolation) | immer. Default-Name: `ANTHROPIC_AUTH_TOKEN`.       |
| `ANTHROPIC_API_KEY`               | —                                         | **gelöscht**, wenn `auth.env_var` ≠ `ANTHROPIC_API_KEY`. |
| `ANTHROPIC_DEFAULT_OPUS_MODEL`    | gewähltes OPUS-Modell                     | nur wenn Slot gesetzt.                             |
| `ANTHROPIC_DEFAULT_SONNET_MODEL`  | gewähltes SONNET-Modell                   | nur wenn Slot gesetzt.                             |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL`   | gewähltes HAIKU-Modell                    | nur wenn Slot gesetzt.                             |
| `provider.extra_env.*`            | YAML, nach Interpolation                  | immer, vor dem Exec, überschreibt nicht die obigen, wenn der User denselben Schlüssel angibt — Konflikte protokolliert leitum als Warnung. |
| `project.extra_env.*`             | `leitum.yaml`, nach Interpolation         | immer, **nach** `provider.extra_env`, gewinnt also bei gleichem Key. Konflikte werden mit `--verbose` als "overridden by project" geloggt. |

### ENV-Interpolation

- Werte aus `auth.token`, `provider.extra_env` und `project.extra_env` mit
  Syntax `${VAR}` oder `${VAR:-default}` werden gegen die aktuelle
  Shell-Umgebung aufgelöst.
- Unbekannte Variablen ohne Default → Exit 3 mit klarer Fehlermeldung
  ("Required env var `REQUESTY_API_KEY` not set").
- Keine rekursive Interpolation.

### Reihenfolge der Komposition

1. Kopie des aktuellen Prozess-Environments als Basis.
2. `ANTHROPIC_API_KEY` ggf. entfernen.
3. `ANTHROPIC_BASE_URL` und Auth-Variable setzen.
4. Modell-ENV-Variablen für gesetzte Slots schreiben.
5. `provider.extra_env` (interpoliert) einfügen — überschreibt Schritt 3
   und 4 nicht, Warnung bei Kollision.
6. `project.extra_env` aus `leitum.yaml` (interpoliert) einfügen —
   überschreibt Schritt 5 und damit auch Schritt 3/4 nicht, sondern nur
   gleiche Keys aus Schritt 5. Konflikte mit Schritt 3/4 werden ebenfalls
   verweigert (Warnung).

## Exec

- Auf macOS und Linux wird mit `os.execvpe("claude", argv, env)` ersetzt —
  kein Wrapper-Prozess, kein Zombie. Der Exit-Code von `claude` ist der
  Exit-Code von `leitum`.
- `argv` ist `["claude", *pass_through_args, *injected_args]`.
  - `injected_args`: enthält `--model <id>`, wenn START-Slot gesetzt **und**
    nicht bereits in `pass_through_args` enthalten ist.
- Wenn `claude` nicht in `PATH`: Exit 5 mit Hinweis auf
  `https://docs.claude.com/en/docs/claude-code/quickstart`.

### Sonderfall `--dry-run`

- Statt `exec` wird auf stdout das resolved Environment (nur leitum-gesetzte
  Variablen, Werte für Secrets als `***redacted***`) und die finale
  Exec-Zeile gedruckt.
- Exit 0.

### Sonderfall `--verbose`

- Vor dem `exec` werden auf stderr in dieser Reihenfolge geloggt:
  1. `.leitumenv`-Datei (Pfad) und welche Keys tatsächlich in `os.environ`
     gesetzt wurden (nur Namen, **nicht** Werte). Keys, die bereits in der
     Shell-Umgebung existierten, erscheinen nicht.
  2. Gewählter Provider und Base-URL.
  3. Gesetzte ENV-Variablen (Namen, **nicht** Werte).
  4. Gelöschte ENV-Variablen.
  5. Final exec line (Argumente, ohne ENV).
- Keine Anzeige von Token-Inhalten, auch nicht bei `--verbose`.

## Signale

- `SIGINT` (Ctrl-C) während des Dialogs → Exit 130. Nach `exec` reicht
  `claude` sich SIGINT selbst durch — leitum ist da nicht mehr im Spiel.
- `SIGTERM` während des Dialogs → sauberer Exit 143.

## Beobachtbarkeit

`leitum claude --dry-run --verbose -p requesty` erzeugt eine reproduzierbare
Trace-Ausgabe, die in Bug-Reports kopiert werden kann (Tokens redacted). Das
ist die Grundlage von `leitum doctor` (siehe PRD 05).
