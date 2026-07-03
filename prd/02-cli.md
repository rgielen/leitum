# PRD 02 — CLI, Flags und Pass-Through

## Aufbau

```
leitum [LEITUM_OPTS] <subcommand> [SUBCOMMAND_ARGS...]
```

- `leitum`-eigene Flags stehen **vor** dem Subcommand.
- Alles nach dem Subcommand-Namen `claude` wird unverändert an das echte
  `claude`-Binary weitergereicht. Damit gibt es keinen Flag-Konflikt mit
  Claude Codes eigenen Kurzflags wie `-p` (Print-Modus).
- Andere Subcommands (`provider`, `doctor`, `refresh`, `init`) reichen nichts
  durch und haben eigene Argument-Parser.

`typer` wird mit `context_settings={"allow_extra_args": True, "ignore_unknown_options": True}` für den `claude`-Subcommand konfiguriert, damit auch beliebige Long-Options durchgereicht werden.

## Globale Flags (vor dem Subcommand)

| Lang                     | Kurz | Wirkung                                                              |
| ------------------------ | ---- | -------------------------------------------------------------------- |
| `--provider <name>`      | `-p` | Provider direkt setzen.                                              |
| `--use-last-provider`    | `-P` | Letzten verwendeten Provider ohne Dialog wiederverwenden.            |
| `--model <id>`           | `-m` | START-Modell direkt setzen.                                          |
| `--use-last-model`       | `-M` | Letztes START-Modell für gewählten Provider wiederverwenden.         |
| `--opus <id>`            | `-o` | OPUS-Modell direkt setzen.                                           |
| `--use-last-opus`        | `-O` | Letztes OPUS-Modell wiederverwenden.                                 |
| `--sonnet <id>`          | `-s` | SONNET-Modell direkt setzen.                                         |
| `--use-last-sonnet`      | `-S` | Letztes SONNET-Modell wiederverwenden.                               |
| `--haiku <id>`           | `-k` | HAIKU-Modell direkt setzen. `-k` statt `-h` (das bleibt `--help`).   |
| `--use-last-haiku`       | `-K` | Letztes HAIKU-Modell wiederverwenden.                                |
| `--refresh`              | `-r` | Modell-Cache des gewählten Providers vor der Auswahl invalidieren und neu fetchen. |
| `--no-project-config`    | —    | `leitum.yaml` im aktuellen Verzeichnis ignorieren.                   |
| `--project-config <path>`| —    | Alternative Project-Config laden statt `$CWD/leitum.yaml`.           |
| `--save-local`           | `-l` | Aufgelöste Auswahl (Provider + Modelle) in `leitum.yaml` schreiben statt in den globalen State. |
| `--dry-run`              | —    | Resolved Environment + finale Exec-Zeile drucken, nicht starten.     |
| `--verbose`              | `-v` | Verbose Logging auf stderr. Tokens redacted.                         |
| `--help`                 | `-h` | Hilfe. `-h` bleibt für Hilfe reserviert.                             |
| `--version`              | —    | Versionsnummer und Exit.                                             |

### Regeln zur Auflösung

Für jeden Slot (Provider, START, OPUS, SONNET, HAIKU) gilt dieselbe
Reihenfolge (höchste Präzedenz zuerst):

1. Explizites Flag (`--provider`, `--model`, `--opus`, `--sonnet`, `--haiku`).
2. `--use-last-*`: aus `state.yaml` lesen. Wenn kein State vorhanden ist,
   Warnung und Fallback auf Dialog.
3. Wert aus `leitum.yaml` (Project-Config) im CWD, sofern vorhanden und nicht
   per `--no-project-config` deaktiviert. Pinnt den Slot ohne Dialog.
4. Letzte Auswahl aus `state.yaml` als Vorbelegung.
5. Provider-Defaults aus `api-providers.yaml` (`defaults.<slot>`) als
   Vorbelegung in der Auswahlmaske.
6. Interaktiver Auswahl-Dialog (`questionary`) für alle nicht aufgelösten
   Slots (siehe PRD 03).

Spezialfall: gibt es nur einen Provider in `api-providers.yaml`, wird er
automatisch ausgewählt — auch ohne `-P`.

Spezialfall: gibt es für einen Slot exakt einen verfügbaren Wert, wird er
automatisch übernommen, ohne Dialog.

Spezialfall START-Slot: bleibt START am Ende leer (kein Flag, kein State, kein
Default, kein Single-Option-Provider-Modell), wird `claude` **ohne** `--model`
gestartet. Claude Code verwendet dann seinen eigenen Default.

OPUS/SONNET/HAIKU-Slots: bleiben sie leer, werden die jeweiligen ENV-Variablen
**nicht gesetzt**. Claude Code fällt auf seine internen Defaults zurück.

Spezialfall `-r`/`--refresh`: gilt nur für Provider, deren Modell-Liste per
API-Discovery aufgebaut wird. Bei Providern mit einer `models:`-Liste in der
YAML hat die Flag keine Wirkung — `leitum` gibt in dem Fall eine kurze
Warnung auf stderr aus und arbeitet wie ohne `-r`. Wirksamer Effekt: nach
Provider-Auflösung wird der Cache des gewählten Providers gelöscht und ein
frischer `GET /v1/models` ausgeführt, bevor die Modell-Auswahl beginnt
(siehe PRD 03).

### Auswahl lokal speichern (`-l`/`--save-local`)

Ist `-l` gesetzt, wird nach der Auflösung von Provider und Modellen und
**vor** dem Launch die aufgelöste Auswahl in die Project-Config geschrieben
(Details in PRD 01, Abschnitt "Schreiben per `--save-local`"). Kurzform:

- Ziel ist `$CWD/leitum.yaml` bzw. der mit `--project-config <path>` gesetzte
  Pfad.
- Eine bestehende Datei wird gemergt: Kommentare und `extra_env` bleiben
  erhalten, nur `provider` und `models` werden auf die aktuelle Auswahl
  gesetzt. Slots ohne gesetzten Wert werden aus dem `models`-Block entfernt.
- In diesem Modus wird der globale `state.yaml` **nicht** zusätzlich
  geschrieben — die Persistenz wandert vollständig in die eingecheckte
  Project-Config.
- `--dry-run` schreibt nichts (seiteneffektfrei); mit `-v` erscheint nur ein
  Hinweis, dass geschrieben *würde*.
- `-l` und `--no-project-config` schließen sich gegenseitig aus (Exit 2).

### Konfliktbehandlung

- Wenn `--model` und `--use-last-model` zusammen angegeben werden: Hard
  Error, `--use-last-*` und expliziter Wert schließen sich aus. Analog für
  alle Slot-Paare.
- Wenn ein Wert (`-m foo`) nicht in der Modell-Liste des Providers vorkommt:
  Warnung auf stderr, aber Launch geht durch (User weiß evtl. mehr als die
  Discovery).
- `-l`/`--save-local` zusammen mit `--no-project-config`: Hard Error (Exit 2),
  da widersprüchlich (kein Project-Config lesen, aber eines schreiben).

## Subcommands

| Subcommand        | Beschreibung                                            | Pass-Through |
| ----------------- | ------------------------------------------------------- | ------------ |
| `claude`          | Claude Code launchen (siehe PRD 04).                    | ja           |
| `provider list`   | Provider aus `api-providers.yaml` auflisten.            | nein         |
| `provider show <name>` | Konfig eines Providers anzeigen (Token redacted). | nein         |
| `provider add`    | Interaktiv neuen Provider hinzufügen.                   | nein         |
| `provider remove <name>` | Provider entfernen (mit Confirm).                | nein         |
| `refresh [--provider <name>]` | Modell-Cache löschen, sofort neu fetchen.   | nein         |
| `doctor`          | Sanity-Check: Datei-Perms, ENV-Vars, Reachability.       | nein         |
| `init`            | Erstinstallation: Verzeichnisse, Beispielconfig.         | nein         |
| `completions <shell>` | Shell-Completions ausgeben (bash/zsh/fish).         | nein         |

`provider`, `doctor`, `refresh`, `init` und `completions` sind detailliert in
PRD 05 beschrieben.

## Beispiel-Aufrufe

```bash
# Voll interaktiv: Dialog für Provider und alle leeren Slots
leitum claude

# Provider und START-Modell fix, Rest aus Defaults/State/Dialog
leitum -p requesty -m anthropic/claude-sonnet-4 claude

# Letzten Provider wiederverwenden, sonst alles wie vorher
leitum -P -M -O -S -K claude

# Mit Pass-Through-Args an claude
leitum -p requesty claude --resume

# Print-Modus in Claude Code, leitum-Provider gesetzt
leitum -p requesty claude -p "Erkläre dieses Repo"

# Dry-Run: zeige nur, was passieren würde
leitum --dry-run -p requesty claude

# Vor der Auswahl die Modell-Liste neu vom Provider holen
leitum -p requesty -r claude

# Im aktuellen Verzeichnis liegt eine leitum.yaml, die Provider und Modelle pinnt;
# der Launch ist dann vollständig nicht-interaktiv:
leitum claude

# Project-Config ignorieren und Provider ad-hoc überschreiben:
leitum --no-project-config -p experimental claude

# Interaktiv Provider/Modelle wählen und die Auswahl ins eingecheckte
# leitum.yaml schreiben (kein Schreiben in den globalen State):
leitum -l claude
```

## Exit-Codes

| Code | Bedeutung                                                  |
| ---- | ---------------------------------------------------------- |
| 0    | Erfolg.                                                    |
| 2    | Argument- oder Validierungsfehler in leitum.               |
| 3    | Konfig fehlt oder fehlerhaft.                              |
| 4    | Provider/Modell konnte nicht aufgelöst werden.             |
| 5    | `claude`-Binary nicht in `PATH`.                           |
| 130  | Vom User abgebrochen (Ctrl-C im Dialog).                   |
| >127 | Vom `claude`-Prozess durchgereicht (bei `exec`/`subprocess`). |

## Hilfetexte und Doku

- `leitum --help` zeigt nur die globalen Flags und die Liste der Subcommands.
- `leitum claude --help` zeigt zusätzlich einen Hinweis, dass alle Args nach
  `claude` an das Binary durchgereicht werden — und einen Link auf
  `claude --help`.
- Alle Hilfetexte Englisch. Beispiele in den Hilfetexten zeigen typische
  Aufrufe wie oben.

## Logging

- `--verbose` aktiviert Info-Logs auf stderr: gewählter Provider, gewählte
  Modelle, gesetzte ENV-Variablen (Namen, nicht Werte), finale Exec-Zeile
  (ohne ENV).
- Ohne `--verbose` ist `leitum` still, abgesehen von interaktiven Dialogen
  und Fehlern.

## Stabilität von Flags

- Kurzflags sind Teil der öffentlichen API. Änderungen sind Breaking Changes
  und erfordern einen Major-Version-Bump.
