# PRD 01 — Konfiguration und State

Dieses PRD beschreibt alle Dateien, die `leitum` auf der Platte hat: was sie
enthalten, wo sie liegen, wie sie validiert werden, wie sie geschützt werden
und wie sie versioniert sind.

## Pfade

`leitum` folgt dem XDG-Basisverzeichnis-Standard (mit sinnvollen Defaults auf
macOS):

| Inhalt                | Pfad                                                                 |
| --------------------- | -------------------------------------------------------------------- |
| Provider-Konfiguration | `${XDG_CONFIG_HOME:-$HOME/.config}/leitum/api-providers.yaml`        |
| Laufzeit-State        | `${XDG_STATE_HOME:-$HOME/.local/state}/leitum/state.yaml`            |
| Modell-Cache          | `${XDG_CACHE_HOME:-$HOME/.cache}/leitum/models/<provider>.json`      |
| Projekt-Konfiguration | `$CWD/leitum.yaml` (optional, pro Repository eingecheckt)            |

Alle Verzeichnisse werden bei Bedarf rekursiv mit Mode `0700` angelegt.
Die `api-providers.yaml` wird mit `0600` angelegt. `state.yaml` ebenfalls
`0600` (kann beim nächsten Token-Tausch indirekt Hinweise auf Provider-Namen
enthalten).

## api-providers.yaml

### Beispiel

```yaml
schema_version: 1
providers:
  - name: requesty
    base_url: https://router.requesty.ai
    auth:
      token: ${REQUESTY_API_KEY}
      env_var: ANTHROPIC_AUTH_TOKEN   # default
    defaults:
      start: anthropic/claude-sonnet-4
      opus: anthropic/claude-opus-4
      sonnet: anthropic/claude-sonnet-4
      haiku: anthropic/claude-haiku-4
    models:
      - id: anthropic/claude-opus-4
        display: "Opus 4 (Requesty)"
        roles: [opus, start]
      - id: anthropic/claude-sonnet-4
        display: "Sonnet 4 (Requesty)"
        roles: [sonnet, start]
      - id: anthropic/claude-haiku-4
        display: "Haiku 4 (Requesty)"
        roles: [haiku]
    extra_env:
      ANTHROPIC_CUSTOM_HEADERS: "x-leitum: 1"
```

### Felder

`schema_version` (int, pflicht)
: Versionsschlüssel. v1 ist `1`. Bei Schemaänderungen wird der Wert erhöht
  und in PRD 01 eine Migration dokumentiert.

`providers` (Liste, pflicht, ≥1)
: Liste der Provider. Die Reihenfolge bestimmt die Reihenfolge im
  Auswahldialog.

Pro Provider:

`name` (string, pflicht, eindeutig, lowercase, kebab-case)
: Identifier für CLI-Flags und State.

`base_url` (URL, pflicht)
: Wird beim Launch in `ANTHROPIC_BASE_URL` geschrieben.

`auth.token` (string, pflicht)
: Wert des Tokens. Unterstützt `${VAR}`-Interpolation aus dem laufenden
  Shell-Environment. Beim Schreiben des Configs niemals klartext-loggen.
  Bei `${VAR}` mit nicht gesetzter Variable: harter Fehler beim Launch.

`auth.env_var` (string, optional, default `ANTHROPIC_AUTH_TOKEN`)
: Name der Environment-Variable, in die das Token beim Launch geschrieben
  wird. Anpassbar für Provider, die `ANTHROPIC_API_KEY` brauchen.

`defaults` (Objekt, optional)
: Pro Slot (`start`, `opus`, `sonnet`, `haiku`) der Default-Modellname, der
  in der Auswahlmaske vorbelegt wird (siehe PRD 03). Nur Namen referenzieren,
  die sich entweder in `models` oder in der API-Liste wiederfinden.

`models` (Liste, optional)
: Wenn vorhanden, **immer** Vorrang vor API-Discovery. Pro Eintrag:

  - `id` (string, pflicht): technischer Modellname, wird unverändert an
    `claude` und in die ENV-Variablen geschrieben.
  - `display` (string, optional): Anzeigename im Auswahldialog. Wenn fehlt,
    fällt der Dialog auf `id` zurück.
  - `roles` (Liste, optional): Hinweise, in welche Slots dieses Modell
    sinnvoll passt. Beeinflusst nur die Vorbelegung/Sortierung im Dialog.
    Erlaubte Werte: `start`, `opus`, `sonnet`, `haiku`.

`extra_env` (Objekt, optional)
: Beliebige Key/Value-Paare, die zusätzlich in das Sub-Environment geschrieben
  werden. Spätere Provider-Eigenheiten lassen sich damit ohne Schemaänderung
  abbilden. Wert unterstützt ebenfalls `${VAR}`-Interpolation.

### Validierung

- `pydantic` v2 Modelle. Strikte Typen, `extra = "forbid"` für unbekannte
  Felder (außer in `extra_env`).
- `name`: regex `^[a-z][a-z0-9-]*$`.
- Namen der Provider müssen über die ganze Datei eindeutig sein.
- `defaults`-Modelle müssen in `models` (falls gesetzt) referenziert sein
  oder in der zuletzt gecachten API-Liste vorkommen. Andernfalls warnt
  `leitum doctor`, der Launch funktioniert aber weiter (falls die User
  die Modelle inzwischen kennt).
- ENV-Interpolation passiert **nicht** beim Laden, sondern beim Launch, damit
  `leitum provider show` weiterhin den literalen Wert anzeigen kann.

### Permissions

- Beim Lesen prüfen, ob Mode strenger als `0600` ist. Wenn nicht, Warnung
  ausgeben und Vorschlag `chmod 600`. Kein automatischer Rewrite.
- Symlinks akzeptiert, aber dieselbe Permissions-Prüfung gilt für das Ziel.

## state.yaml

### Zweck

Speichert die letzten interaktiven Auswahlen, damit der User sie beim
nächsten Start nicht erneut treffen muss. Pro Provider werden alle vier
Modell-Slots separat gemerkt.

### Beispiel

```yaml
schema_version: 1
last_provider: requesty
providers:
  requesty:
    models:
      start: anthropic/claude-sonnet-4
      opus: anthropic/claude-opus-4
      sonnet: anthropic/claude-sonnet-4
      haiku: anthropic/claude-haiku-4
    last_used: 2026-06-13T14:33:12+02:00
  openrouter:
    models:
      start: anthropic/claude-3.7-sonnet
    last_used: 2026-05-30T11:00:00+02:00
```

### Felder

- `schema_version` — int, v1 ist `1`.
- `last_provider` — Name eines in `api-providers.yaml` definierten Providers
  (oder leer, wenn noch nie gewählt).
- `providers.<name>.models.<slot>` — letzter ausgewählter Modellname pro Slot.
  Nicht ausgewählte Slots fehlen einfach.
- `providers.<name>.last_used` — ISO-8601-Timestamp.

### Verhalten

- Fehlende Datei: kein Fehler, State-Lookup gibt `None` zurück.
- Korrupte Datei: leitum logge eine Warnung, behandle es wie "fehlt", und
  schreibe beim nächsten erfolgreichen Launch eine frische Datei.
- Schreibvorgang atomar (`os.replace` von einer Temp-Datei).
- Permissions `0600`.

## leitum.yaml (Project-Konfiguration)

### Zweck

Reproduzierbare Repo-Vorgabe für Provider und Modelle. `leitum.yaml` wird
ins Repository eingecheckt. Es überschreibt `state.yaml` (zuletzt verwendet)
und Provider-Defaults aus `api-providers.yaml`, wird selbst aber durch
CLI-Flags überschrieben (siehe PRD 03 zur vollständigen Präzedenz).

### Pfad und Discovery

- Genau eine Datei wird gelesen: `$CWD/leitum.yaml`. Es findet **keine
  Aufwärtssuche** statt. Wer aus einem Unterordner heraus startet und die
  Repo-Vorgabe benötigt, ruft `leitum` aus dem Repo-Root auf.
- Existiert die Datei nicht: kein Fehler, das Feature ist inaktiv.

### Beispiel

```yaml
schema_version: 1
provider: requesty
models:
  start: anthropic/claude-sonnet-4
  opus: anthropic/claude-opus-4
  sonnet: anthropic/claude-sonnet-4
  haiku: anthropic/claude-haiku-4
extra_env:
  ANTHROPIC_CUSTOM_HEADERS: "x-project: leitum-demo"
  PROJECT_REGION: ${LEITUM_REGION:-eu-central-1}
```

### Felder

`schema_version` (int, pflicht)
: v1 ist `1`. Migrationen analog zu den anderen Dateien.

`provider` (string, optional)
: Name eines Providers, der in der globalen `api-providers.yaml` definiert
  ist. Pinnt den Provider. Existiert der Provider dort nicht: Exit 3 mit
  klarer Fehlermeldung und Liste der bekannten Provider.

`models` (Objekt, optional)
: Pro Slot (`start`, `opus`, `sonnet`, `haiku`) ein Modellname. Jeder
  Slot ist einzeln optional. Pinnt das Modell für den Slot. Modell **muss
  nicht** in der aktuellen Discovery-Liste vorkommen — fehlt es, gibt es
  eine Warnung auf stderr, der Launch geht trotzdem durch (Discovery kann
  unvollständig sein).

`extra_env` (Objekt, optional)
: Beliebige Key/Value-Paare, die zusätzlich in das Sub-Environment
  geschrieben werden. Werte unterstützen `${VAR}`- und
  `${VAR:-default}`-Interpolation gegen das aktuelle Shell-Environment.
  **Diese Datei ist eingecheckt — Secrets gehören nicht hier hinein.**
  Werte sollten Konfigurations- und Routing-Informationen tragen
  (Region, Headers, Logging-Level), keine API-Keys. Verstöße kann
  `leitum` nicht hart erkennen; `leitum doctor` warnt heuristisch bei
  Werten, die wie hochentropische Tokens aussehen (Länge ≥ 24 und keine
  ENV-Interpolation), aber das ist keine Garantie.

Nicht zugelassen sind in v1:

- Neue Provider-Definitionen (keine `providers:`-Liste). Provider werden
  zentral in der globalen `api-providers.yaml` verwaltet, sonst landet
  irgendwann ein Token im Repo.
- `auth:`-Blöcke. Authentifizierung ist immer Sache des globalen Configs.

### Validierung

- `pydantic` v2, `extra = "forbid"` für unbekannte Top-Level-Felder
  (außer in `extra_env`).
- `provider`: muss in `api-providers.yaml` existieren. Fehlerfall: Exit 3.
- `models.<slot>`: nicht-leerer String, falls gesetzt.
- ENV-Interpolation erfolgt erst beim Launch.

### Permissions

Keine Anforderungen. Die Datei ist Teil des Repos und unterliegt dessen
üblichen Lese-/Schreibrechten. `leitum` prüft die Mode-Bits nicht.

### Interaktion mit state.yaml

- `leitum.yaml` schreibt nichts zurück. State-Writeback für interaktiv
  bestätigte Slots läuft normal weiter (für gepinnte Slots wirkungslos —
  die Werte landen in `state.yaml`, gewinnen aber beim nächsten Launch
  nicht gegen `leitum.yaml`).
- Wird `leitum.yaml` aus dem Repo entfernt, übernimmt der State wieder
  wie vorher.

### Override per CLI

- `--no-project-config`: ignoriert `leitum.yaml` für diesen Aufruf
  vollständig.
- `--project-config <path>`: lädt eine alternative Datei statt
  `$CWD/leitum.yaml`. Praktisch für Tests und CI-Sonderfälle.

## Modell-Cache

### Zweck

Die API-Discovery-Liste (`GET /v1/models`) wird gecacht, damit nicht bei
jedem Launch HTTP gemacht werden muss.

### Format

JSON, ein Eintrag pro Provider:

```json
{
  "schema_version": 1,
  "fetched_at": "2026-06-13T14:33:12+02:00",
  "base_url": "https://router.requesty.ai",
  "models": [
    { "id": "anthropic/claude-sonnet-4", "display": "Sonnet 4" }
  ]
}
```

### TTL und Invalidierung

- TTL: 24 Stunden. Danach wird beim nächsten Launch erneut gefetched.
- `leitum refresh` löscht den Cache und holt sofort neu (siehe PRD 05).
- Bei HTTP-Fehler: bestehender Cache wird auch über TTL hinaus benutzt; ohne
  jeglichen Cache und mit Netzfehler — harter Fehler mit Hinweis auf
  `models:` in YAML.

### Pfad

`${XDG_CACHE_HOME:-$HOME/.cache}/leitum/models/<provider>.json`.

## Sicherheit

- Tokens nie in stderr/stdout/Logfiles erscheinen. `--verbose` zeigt nur, dass
  die jeweilige ENV-Variable gesetzt wurde, nicht den Wert.
- Beim Laden der Konfig wird der token-Klartext im RAM gehalten; kein
  unnötiges Wiederlesen. Keine Persistenz außerhalb der vorhergesehenen
  Dateien.
- Vor Launch: `ANTHROPIC_API_KEY` aus dem Sub-Environment entfernen, wenn
  der Provider eine andere `auth.env_var` verwendet, damit nicht eine
  User-Shell-Variable das Token überschreibt.

## Migrationen

Schemaversion erhöhen, Migrationscode in `leitum/config/migrations/` ablegen.
Beim Laden alter Versionen automatisch und in-place migrieren, vorher eine
`.bak`-Kopie schreiben.
