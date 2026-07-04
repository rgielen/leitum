# PRD 03 — Auswahl von Provider und Modellen

## Überblick

Vor jedem Launch löst `leitum` zwei Dinge auf:

1. **Provider** — genau einer.
2. **Modelle pro Slot** — bis zu vier, davon mindestens null gesetzte.

Die Auflösung folgt für beide derselben Hierarchie (CLI-Flag → `--use-last-*`
→ Defaults → State → Dialog), siehe PRD 02. Dieses PRD beschreibt das
Verhalten, sobald ein interaktiver Dialog tatsächlich nötig wird.

## Provider-Auswahl

### Wann interaktiv?

Es gibt einen Dialog, wenn

- weder `-p` noch `-P` gesetzt sind, **und**
- `leitum.yaml` (Project-Config) im CWD entweder fehlt, kein `provider:`-Feld
  setzt oder per `--no-project-config` deaktiviert wurde, **und**
- in `api-providers.yaml` mehr als ein Provider existiert.

In allen anderen Fällen wird der Provider deterministisch bestimmt.

### Dialog-Design

`questionary.select`:

- Titel: "Select API provider".
- Items: Provider in der Reihenfolge ihrer YAML-Definition. Anzeige als
  `<name> — <base_url>`.
- Vorbelegung (Cursor-Position): `state.last_provider`, sonst Eintrag 0.
- Auswahl per Pfeil + Enter, Abbruch per Ctrl-C → Exit 130, keine
  Persistenz.
- Type-to-Filter aktiv (`use_search_filter=True`): Tippen filtert die
  Provider-Liste live. Verhalten identisch zum Modell-Dialog (siehe Abschnitt
  "Type-to-Filter" unter Modell-Auswahl).
- Nach Bestätigung wird `state.last_provider` sofort persistiert (siehe PRD 01).

## Modell-Discovery

Bevor der Modell-Dialog erscheint, baut `leitum` die Modell-Liste des
gewählten Providers nach folgendem Algorithmus auf:

1. Wenn `provider.models` in der YAML gesetzt und nicht leer ist, **nur**
   diese Liste verwenden. API wird nicht angefasst.
2. Sonst: Cache-Datei prüfen. Wenn vorhanden und nicht abgelaufen, verwenden.
3. Sonst: `GET ${base_url}/v1/models` mit `Authorization: Bearer ${token}`,
   Timeout 10s. Antwort wird auf OpenAI-kompatibles Format normalisiert:
   Liste `data[*].id`. `display` wird auf `id` gesetzt (kein Anzeige-Name
   verfügbar).
4. Erfolg: Cache schreiben (siehe PRD 01), Liste verwenden.
5. Fehler und abgelaufener Cache vorhanden: stale Cache verwenden + Warnung
   auf stderr. Kein Cache und Fehler: Exit 4 mit klarer Meldung.

### Erzwungener Refresh

`-r`/`--refresh` (siehe PRD 02) und die Refresh-Tastenkombination im
Modell-Dialog (Ctrl-R, siehe unten) lassen Schritt 2 aus und gehen direkt zu
Schritt 3. Schritt 3 bekommt zusätzlich einen `no_cache=True`-Hinweis, damit
auch ETag-/Conditional-Mechanismen umgangen werden. Cache wird auf Erfolg
wie üblich neu geschrieben.

Bei einem Provider mit `models:`-Liste in der YAML ist ein Refresh
wirkungslos: weder Flag noch Tastendruck zeigen einen Effekt, beide werden
ignoriert (Flag mit kurzer Warnung auf stderr, Tastendruck im Dialog mit
einer dezenten Statuszeile "(refresh not applicable — provider models are
pinned in YAML)").

## Modell-Auswahl

### Slots

Vier Slots in fester Reihenfolge: `start`, `opus`, `sonnet`, `haiku`. Jeder
Slot kann den Wert "keine Auswahl / nicht setzen" haben (siehe PRD 02 für die
Auswirkungen).

### Vorbelegung pro Slot

Für jeden noch nicht durch CLI-Flag aufgelösten Slot wird die Vorbelegung in
dieser Reihenfolge ermittelt:

1. `--use-last-*`-Flag aktiv → State-Wert (oder Fehler, wenn keiner da).
2. `leitum.yaml` (Project-Config) im CWD pinnt den Slot → dieser Wert wird
   ohne Dialog verwendet. Übersteuert State und Provider-Defaults.
3. `state.providers.<name>.models.<slot>` (letzte Auswahl).
4. `provider.defaults.<slot>` aus `api-providers.yaml`.
5. Erster Modell-Eintrag mit `roles` enthält `<slot>`.
6. Erster Modell-Eintrag insgesamt — nur wenn `models` aus YAML kommt; bei
   API-Discovery wird in diesem Fall "kein Default" angeboten.

Wenn am Ende kein Default ermittelbar ist, wird der Slot mit "(nicht setzen)"
vorbelegt.

Hinweis zur Präzedenz: die hier genannte Reihenfolge ist die Vorbelegungs-
und Auflösungsreihenfolge für **nicht** per CLI-Flag gesetzte Slots. Die
Gesamtsicht (CLI > Project-Config > State > Defaults) ist in PRD 02
beschrieben.

### Wann interaktiv?

Es gibt einen Modell-Dialog, wenn mindestens ein Slot

- nicht per CLI-Flag explizit gesetzt ist, **und**
- nicht per `--use-last-*` direkt aus State befüllbar ist (oder zusätzlich
  Slot-Bedarf besteht), **und**
- nicht durch `leitum.yaml` (Project-Config) gepinnt ist, **und**
- die Modell-Liste mehr als einen Eintrag hat.

Hat die Liste nur einen Eintrag, wird der für alle noch offenen Slots
übernommen (kein Dialog), aber **nur** wenn der Provider keinen abweichenden
Default vorgegeben hat.

### Dialog-Design: Sequenzielle Slot-Dialoge

Der Dialog besteht aus einer Folge von `questionary.select`-Aufrufen, einem
pro Slot. Jeder Slot-Dialog enthält:

- Titel: `"Select models for <provider> — <Slot-Bezeichnung>"`.
- Choices: "(use Claude default)" resp. "(do not set)" als erster Eintrag,
  dann alle Modelle aus der Discovery/YAML-Liste. Sortierung: zuerst die
  `roles`-passenden Modelle, dann der Rest.
- Cursor auf der Vorbelegung (vorheriger Wert, falls vorhanden, sonst
  `preselected[slot]`).
- **Instruction-Footer** auf jedem Slot-Dialog:
  ```
  (↑↓ move · type to filter · Ctrl-R refresh · Ctrl-S save→project · Enter select)
  ```
  Wird `save_local_allowed=False` (d.h. `--no-project-config` aktiv), entfällt
  der `Ctrl-S save→project`-Hinweis. Ist der Save-Modus aktiv (armed), wird
  ` [save→project ON]` an den Footer angehängt.

Abbruch (Ctrl-C / `None` von `ask()`): Exit 130.

*Verworfene Alternative:* Eine zusammenhängende Maske mit `questionary.form`
(oder Eigenimplementierung) wurde im ursprünglichen Entwurf dieses PRD
beschrieben. Diese wurde als nicht realisierbar mit der aktuellen
questionary-Version eingestuft und ist kein geplantes Ziel.

### Type-to-Filter

Jedes Slot-`select` (und der Provider-Dialog oben) läuft mit
`use_search_filter=True` und `show_selected=True`. Damit kann der User lange
Modell-Listen (z.B. API-Discovery bei Requesty mit Dutzenden Einträgen) durch
Tippen eingrenzen.

- **Filter**: Tippen filtert die Choices live auf Einträge, deren angezeigter
  Titel den Suchstring enthält — case-insensitiver Substring-Match
  (`search_filter.lower() in title.lower()`).
- **Bearbeiten**: Backspace verkürzt den Suchstring; ein leerer Filter stellt
  die vollständige Liste wieder her.
- **Navigation/Auswahl**: Pfeiltasten navigieren die gefilterte Liste, Enter
  wählt den Eintrag unter dem Cursor. Die Vorbelegung/Cursor-Position bleibt
  initial erhalten; erst beim Tippen ändert sich die Ansicht.
- **`(do not set)` / `(use Claude default)`**: Diese Sondereinträge unterliegen
  demselben Filter und verschwinden, wenn sie nicht matchen. Filter leeren
  (Backspace) macht sie wieder sichtbar.
- **Trade-off**: `use_search_filter=True` deaktiviert die vi-artige `j`/`k`-
  Navigation, weil diese Zeichen Teil des Suchstrings werden. Pfeiltasten
  bleiben voll funktionsfähig. Dies ist genau der Kompromiss, für den unten
  `Ctrl-R` als Refresh-Keybinding reserviert wurde (ein einfaches `r` würde als
  Filtereingabe interpretiert) — es gibt keinen Konflikt.

### Refresh aus dem Dialog heraus (Ctrl-R)

Innerhalb des Slot-Dialogs kann der User die Modell-Liste neu vom Provider
holen, ohne den Dialog zu verlassen.

- **Keybinding**: `Ctrl-R` (über `prompt_toolkit` `KeyBindings.add` mit
  `eager=True`). `Ctrl-R` wurde gewählt, weil es nicht mit dem Type-to-Filter
  von `questionary` kollidiert.
- **Wirkung**: dieselbe Logik wie `-r`/`--refresh`, aber zur Laufzeit. Der
  aktuelle Slot wird neu gerendert mit der frischen Modell-Liste. Bereits in
  vorherigen Slots gewählte Werte, die in der neuen Liste nicht mehr vorkommen,
  werden auf `None` (d.h. "(do not set)") zurückgesetzt. Eine Hinweiszeile auf
  stderr erscheint:
  `"slot '<slot>' reset: previous model not in refreshed list"`.
- **Hinweismeldungen auf stderr** (zwischen den Slot-Dialogen ausgegeben, da
  der `prompt_toolkit`-App-Kontext zu diesem Zeitpunkt verlassen wurde):
  - Normaler Refresh: `"Refreshing models from <provider>..."`.
  - Fehler: `"Refresh failed: <reason> — kept current list"`.
  - YAML-gepinnte Modelle: `"(refresh not applicable — provider models are pinned in YAML)"`.
  - Unter `--dry-run`: `"(refresh skipped in --dry-run)"` (kein Netzwerkzugriff,
    kein Cache-Schreibvorgang).
- **YAML-Modelle**: Ist die Liste in YAML gepinnt, wird kein Refresh
  durchgeführt; der Callback ist `None`.

### Speichern aus dem Dialog heraus (Ctrl-S)

- **Keybinding**: `Ctrl-S` (über `prompt_toolkit` `KeyBindings.add` mit
  `eager=True`). `prompt_toolkit` deaktiviert IXON im Raw-Mode, sodass
  Ctrl-S als Tastendruck ankommt und nicht als XON/XOFF-Flusssteuerung.
- **Wirkung**: Additiver Toggle. Schaltet einen "armed"-Zustand um. Ist der
  Zustand am Ende der Auswahl aktiv, wird die abgeschlossene Auswahl in
  `leitum.yaml` (oder den `--project-config <path>`) geschrieben — exakt wie
  `--save-local` (siehe Abschnitt "Persistenz nach Auswahl"). Der globale
  `state.yaml` wird für diesen Launch nicht angefasst.
- **Startzustand**: Wenn `--save-local` auf der CLI übergeben wurde, startet
  der Dialog bereits im armed-Zustand.
- **Disabled**: Wenn `--no-project-config` aktiv ist (was sich gegenseitig mit
  `--save-local` ausschließt, erzwungen in `run_claude`), wird Ctrl-S nicht
  gebunden und der Hinweis im Footer entfällt.
- **`--dry-run`**: Es wird nichts geschrieben. Falls armed, gilt die bestehende
  Dry-Run-Meldung "would write selection to <path>".

### Persistenz-Auflösung

In `run_claude` gilt:

```
effective_save_local = resolved.save_local if resolved.dialog_shown else save_local_cli_flag
```

Wurde der Modell-Dialog angezeigt, übernimmt sein abschließender
Armed-Zustand die Entscheidung vollständig (der User kann gegenüber dem
CLI-Flag arm oder entwaffnen). Wurde kein Dialog angezeigt, gilt das
CLI-Flag `--save-local` unverändert. Da Ctrl-S unter `--no-project-config`
nicht verfügbar ist, kann `effective_save_local` nie mit diesem Flag
kollidieren.

### Fallback ohne TTY

Wenn `stdin`/`stdout` kein TTY ist (z.B. CI):

- Wenn alle benötigten Slots durch Flags/State/Defaults aufgelöst werden
  können → Launch.
- Sonst Exit 4 mit Hinweis: "Use --provider/--model/... or run interactively."

## Persistenz nach Auswahl

Nach erfolgreicher Auflösung (vor dem Exec) persistiert `leitum` die Auswahl.
Wohin, hängt von `effective_save_local` ab (siehe "Persistenz-Auflösung"):

### Standard: globaler State

- `state.yaml` wird so aktualisiert:
  - `last_provider` → gewählter Provider.
  - `providers.<name>.models.<slot>` → für jeden Slot, der tatsächlich
    gesetzt wird, der finale Wert. Slots, die "do not set" sind, werden
    **nicht** in den State geschrieben (vorhandene alte Werte bleiben
    bestehen, damit `--use-last-*` weiter funktioniert).
  - `providers.<name>.last_used` → aktueller Timestamp.

### Mit `-l`/`--save-local` oder Ctrl-S: lokale Project-Config

- Die Auswahl wird in `leitum.yaml` geschrieben (Merge, Details in PRD 01,
  Abschnitt "Schreiben per `--save-local`"), und `state.yaml` wird für diesen
  Launch **nicht** angefasst.

### Gemeinsam

- `--dry-run` überspringt in beiden Fällen jeden Schreibvorgang.

## Edge Cases

- **Provider hat leere Modell-Liste in YAML und API liefert nichts** → der
  User kann trotzdem starten, wenn er `-m <name>` explizit angibt; sonst
  Exit 4.
- **Provider in CLI angegeben, aber unbekannt** → Exit 2 mit Hinweis auf
  `leitum provider list`.
- **State referenziert Provider, der nicht mehr in YAML existiert** →
  `last_provider` ignorieren, State unverändert lassen, normaler Flow.
- **`-M` ohne State** → Warnung, dann Dialog.
- **`-M` mit Wert aus State, der nicht mehr in der aktuellen Modell-Liste
  vorkommt** → Warnung, Wert wird trotzdem übernommen (Discovery kann
  unvollständig sein); `leitum doctor` flaggt diesen Fall separat.
- **`leitum.yaml` pinnt einen Provider, der in `api-providers.yaml` fehlt** →
  Exit 3 mit klarer Fehlermeldung und Liste der bekannten Provider. Das
  Repo verlangt explizit eine Einrichtung, die User-seitig fehlt.
- **`leitum.yaml` pinnt ein Modell, das nicht in der aktuellen Modell-Liste
  vorkommt** → Warnung auf stderr, Wert wird trotzdem verwendet (analog zu
  `-m`).
- **`leitum.yaml` ist syntaktisch kaputt** → Exit 3. Anders als bei `state.yaml`
  (das Cache ist) wird hier nicht stillschweigend weitergearbeitet — die Datei
  ist Intent des Repos.
- **`--no-project-config` und `--project-config <path>` zusammen** → Exit 2
  (gegenseitig ausschließend).

## UX-Details

- Alle Dialog-Texte Englisch.
- Cursor-Position und Vorbelegung sind identisch — der User kann mit Enter
  durchrauschen, wenn er den Vorschlag akzeptiert.
- Wenn `--verbose` aktiv ist, schreibt `leitum` nach jeder Auswahl eine Zeile
  auf stderr, was übernommen wurde.
