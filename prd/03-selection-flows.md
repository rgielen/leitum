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
Modell-Dialog (siehe unten) lassen Schritt 2 aus und gehen direkt zu
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

### Dialog-Design: Single-Maske mit vier Slots

Eine zusammenhängende Maske statt vier sequenzieller Dialoge. Konkret: ein
`questionary.form` (oder eine kleine Eigenimplementierung darauf) zeigt für
jeden Slot eine Select-Zeile.

Layout (Beispiel):

```
Select models for Requesty:

  Start  (--model)                  ▸ anthropic/claude-sonnet-4
  Opus   (ANTHROPIC_DEFAULT_OPUS_MODEL)   ▸ anthropic/claude-opus-4
  Sonnet (ANTHROPIC_DEFAULT_SONNET_MODEL) ▸ anthropic/claude-sonnet-4
  Haiku  (ANTHROPIC_DEFAULT_HAIKU_MODEL)  ▸ (do not set)

  [Enter] Confirm   [Esc] Cancel   [Ctrl-R] Refresh models
```

Jede Slot-Zeile öffnet beim Aktivieren ein Sub-`select` mit:

- "(do not set)" als erster Eintrag (bei OPUS/SONNET/HAIKU) bzw. "(use Claude
  default)" beim START-Slot.
- Allen Modellen aus der Discovery/YAML-Liste.
- Sortierung: zuerst die `roles`-passenden Modelle, dann der Rest. Innerhalb
  einer Gruppe in Definitionsreihenfolge (YAML) bzw. lexikografisch
  (API-Discovery).
- Cursor auf der Vorbelegung.

Bestätigung mit Enter schließt die Maske komplett. Cancel (Esc/Ctrl-C):
Exit 130.

### Refresh aus dem Dialog heraus

Innerhalb der Modell-Maske kann der User die Modell-Liste neu vom Provider
holen, ohne den Dialog verlassen zu müssen.

- **Keybinding**: `Ctrl-R` (primär). `Ctrl-R` wurde gewählt, weil es nicht
  mit dem späteren Type-to-Search-Filter von `questionary` kollidiert (ein
  einfaches `r` würde dort als Eingabe interpretiert).
- **Wirkung**: dieselbe Logik wie `-r`/`--refresh` (siehe oben), aber zur
  Laufzeit. Die Liste wird neu aufgebaut, der Dialog re-rendert mit der
  frischen Auswahl, bereits in den Slots stehende Werte werden beibehalten,
  falls sie in der neuen Liste noch vorkommen — andernfalls fallen sie auf
  "(do not set)" zurück und es erscheint eine Hinweiszeile darunter:
  `"slot 'opus' reset: previous model not in refreshed list"`.
- **Statusanzeige während des Refreshs**: einzeilige Meldung am unteren
  Rand der Maske: `"Refreshing models from <provider>..."`. Bei Fehlern:
  `"Refresh failed: <reason> — kept current list"` (drei Sekunden sichtbar).
- **YAML-Modelle**: ist die Liste in YAML gepinnt, wird die Tastenkombination
  ignoriert und eine Statuszeile zeigt
  `"(refresh not applicable — provider models are pinned in YAML)"`.

### Fallback ohne TTY

Wenn `stdin`/`stdout` kein TTY ist (z.B. CI):

- Wenn alle benötigten Slots durch Flags/State/Defaults aufgelöst werden
  können → Launch.
- Sonst Exit 4 mit Hinweis: "Use --provider/--model/... or run interactively."

## Persistenz nach Auswahl

- Nach erfolgreicher Auflösung (vor dem Exec) wird `state.yaml` so
  aktualisiert:
  - `last_provider` → gewählter Provider.
  - `providers.<name>.models.<slot>` → für jeden Slot, der tatsächlich
    gesetzt wird, der finale Wert. Slots, die "do not set" sind, werden
    **nicht** in den State geschrieben (vorhandene alte Werte bleiben
    bestehen, damit `--use-last-*` weiter funktioniert).
  - `providers.<name>.last_used` → aktueller Timestamp.

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
