# PRD 08 — Lokale Provider (Ollama, LM Studio, llama.cpp, vLLM)

Implementation status: planned

Dieses PRD beschreibt, wie `leitum` lokal laufende, Anthropic-kompatible
LLM-Server als Provider unterstützt: als Dokumentation, als vordefinierte
Presets im `provider add`-Wizard und als Auto-Erkennung laufender Server über
`leitum provider detect`.

## Ausgangslage und Kernentscheidung

Claude Code spricht die Anthropic Messages API. Bis Anfang 2026 brauchte man
für lokale Modelle einen Übersetzungs-Proxy (z. B. LiteLLM). Das ist nicht mehr
nötig:

- **Ollama** liefert seit dem Release vom 2026-01-16 native Anthropic-Messages-
  API-Kompatibilität. Setup: `ANTHROPIC_BASE_URL=http://localhost:11434`,
  `ANTHROPIC_AUTH_TOKEN=ollama`.
- **LM Studio** ab Version `0.4.1` liefert einen Anthropic-kompatiblen
  `/v1/messages`-Endpunkt. Setup: `ANTHROPIC_BASE_URL=http://localhost:1234`,
  `ANTHROPIC_AUTH_TOKEN=lmstudio`.
- **llama.cpp** (`llama-server`) und **vLLM** bieten ebenfalls
  Anthropic-kompatible Endpunkte an.

Damit funktioniert leitums Kernmechanik (`ANTHROPIC_BASE_URL` + Auth-Env-Var
setzen, `claude` exec'en, siehe PRD 04) **bereits** gegen alle vier. Lokale
Provider sind aus leitums Sicht schlicht Anthropic-kompatible Provider mit zwei
Besonderheiten:

1. Der Auth-Token ist ein **bekannter Platzhalter ohne Geheimwert** (z. B.
   `ollama`, `lmstudio`), kein echter API-Key.
2. Die `base_url` ist ein `http://localhost:<port>` statt eines Remote-Hosts.

Die Modell-Discovery über den bestehenden `GET /v1/models`-Pfad (siehe PRD 01,
`providers/discovery.py`) funktioniert unverändert gegen Ollama
(`:11434/v1/models`) und LM Studio (`:1234/v1/models`).

### Keine Schemaänderung

Presets füllen ausschließlich **bestehende** Felder der `api-providers.yaml`.
Ein literaler `auth.token: ollama` ist unter dem aktuellen Schema (PRD 01) schon
gültig. Daher:

- `schema_version` bleibt `1`. Keine Migration.
- **Verworfene Alternative:** ein `kind:`/`local:`-Feld im Provider-Schema. Es
  bringt kaum Verhaltensmehrwert, vergrößert die Schema-Oberfläche und erzwingt
  eine Migration — während alles über die vorhandenen Felder abbildbar ist. Die
  Unterscheidung „lokal vs. remote" lebt nur in der eingebauten Preset-Registry
  (Code), nicht in der Nutzer-YAML. Kein separates ADR, da die Wahl additiv und
  reversibel ist.

## Konfigurationsform lokaler Provider

Beispiel-Eintrag in `api-providers.yaml` (das, was ein Preset erzeugt):

```yaml
- name: ollama
  base_url: http://localhost:11434
  auth:
    token: ollama            # Platzhalter, kein Geheimnis — inline zulässig
    env_var: ANTHROPIC_AUTH_TOKEN
  extra_env:
    OLLAMA_CONTEXT_LENGTH: "32768"
```

- **`auth.token`**: Für lokale Provider ein literaler Platzhalter, inline
  gespeichert. `${VAR}`-Interpolation ist erlaubt, aber nicht erforderlich. Weil
  der Wert kein Geheimnis ist, darf er im Klartext in der Datei stehen; die
  üblichen `0600`-Regeln aus PRD 01 gelten unverändert (kein Sonderfall).
- **`auth.env_var`**: `ANTHROPIC_AUTH_TOKEN` (Default). Beim Launch wird ein
  eventuell geerbtes `ANTHROPIC_API_KEY` aus dem Sub-Environment entfernt (PRD
  04) — für lokale Provider genauso wichtig, damit kein Host-Key durchschlägt.
- **`extra_env`**: Trägt providertypische Tuning-Variablen. Für Ollama wird
  `OLLAMA_CONTEXT_LENGTH: "32768"` empfohlen (Claude Code ist kontext-hungrig;
  32K ist die Untergrenze, 64K der Sweet Spot). Für die anderen Presets ist
  `extra_env` leer.
- **Modelle**: keine `models:`-Liste nötig — Discovery über `/v1/models` liefert
  die lokal installierten/geladenen Modelle. `leitum provider detect` kann die
  entdeckten Modelle optional als `models:`-Liste einpinnen.

### Doctor und lokale Provider

`leitum doctor` (PRD 05) prüft die Erreichbarkeit über einen leichten Request
gegen `base_url`. Für einen lokalen Provider bedeutet „unerreichbar" in aller
Regel „Server läuft nicht". Der Erreichbarkeits-Check **darf** für Provider mit
einer `localhost`/`127.0.0.1`-`base_url` einen konkreten Hinweis ergänzen
(„Is the local server (Ollama/LM Studio) running?") statt nur einer generischen
Warnung. Das ist eine optionale Komfortverbesserung, kein harter `fail`.

Der Secret-Heuristik-Check (`_SECRET_RE` in `doctor.py`) greift nur bei
`leitum.yaml`-`extra_env` und nur bei ≥24 Zeichen ohne Interpolation — kurze
Platzhalter wie `ollama` lösen ihn nicht aus. Es ist keine Anpassung nötig.

## Preset-Registry (eingebaut, code-seitig)

Neues Modul `src/leitum/providers/presets.py`. Es definiert eine unveränderliche
Liste von `ProviderPreset`-Objekten. Die Registry ist **Code/Seed-Daten**, kein
Teil des YAML-Schemas.

### `ProviderPreset`-Felder

| Feld           | Typ         | Zweck                                                                 |
| -------------- | ----------- | --------------------------------------------------------------------- |
| `key`          | str         | Stabiler Identifier für CLI (`--preset <key>`), z. B. `ollama`.       |
| `display`      | str         | Anzeigename im Auswahldialog, z. B. `Ollama (local)`.                 |
| `default_name` | str         | Vorgeschlagener Provider-`name` (kebab-case, PRD-01-konform).         |
| `base_url`     | str         | Vorbelegte Base-URL.                                                   |
| `token`        | str         | Platzhalter-Token (inline).                                           |
| `auth_env_var` | str         | Default `ANTHROPIC_AUTH_TOKEN`.                                       |
| `extra_env`    | dict[str,str] | Empfohlene Zusatz-Env (leer, außer Ollama).                        |
| `is_local`     | bool        | Steuert UX (kein Secret-Prompt) und Auto-Detect.                     |
| `detect_ports` | list[int]   | Ports, die `provider detect` probt (leer = nicht auto-erkennbar).    |
| `docs_url`     | str \| None | Link auf die Provider-Doku (für Hinweise/Docs).                      |

### Ausgelieferte Presets

| `key`          | `display`                       | `base_url`                | `token`   | `extra_env`                         | `detect_ports` |
| -------------- | ------------------------------- | ------------------------- | --------- | ----------------------------------- | -------------- |
| `ollama`       | Ollama (local)                  | `http://localhost:11434`  | `ollama`  | `OLLAMA_CONTEXT_LENGTH: "32768"`    | `[11434]`      |
| `lm-studio`    | LM Studio (local)               | `http://localhost:1234`   | `lmstudio`| —                                   | `[1234]`       |
| `llama-cpp`    | llama.cpp (local)               | `http://localhost:8080`   | `local`   | —                                   | `[8080]`       |
| `vllm`         | vLLM (local)                    | `http://localhost:8000`   | `local`   | —                                   | `[8000]`       |
| `local-generic`| Generic local (Anthropic-compat)| `http://localhost:8080`   | `local`   | —                                   | `[]`           |

`local-generic` ist die Vorlage für beliebige weitere lokale, Anthropic-
kompatible Server: es belegt sinnvolle Defaults vor, erwartet aber, dass der
User `base_url` und ggf. `name` anpasst. Es nimmt an der Auto-Detection nicht
teil (`detect_ports = []`).

Die Default-Ports für llama.cpp/vLLM sind gängige, aber nicht garantierte Werte;
der Wizard erlaubt Override.

## `leitum provider add` mit Presets

Der bestehende interaktive Wizard (PRD 05, `run_provider_add`) erhält als
**ersten** Schritt eine Auswahl der Provider-Art:

1. **Provider type** (`questionary.select`): Liste aller Presets (nach `display`)
   plus zwei Sondereinträge:
   - `Detect local providers…` → delegiert an `provider detect` (siehe unten;
     wird mit Issue B geliefert).
   - `Custom (manual)` → der heutige Ablauf, unverändert.
2. Bei Auswahl eines **Presets**:
   - `name`: Text-Prompt, vorbelegt mit `default_name`; PRD-01-Validierung; bei
     Kollision mit existierendem Provider Fehler wie bisher (Exit 2).
   - `base_url`: Text-Prompt, vorbelegt mit `preset.base_url`.
   - **Kein Token-Quellen-Prompt und kein Password-Prompt.** Der Platzhalter
     `preset.token` wird direkt übernommen (der User kann ihn im Text-Prompt
     ändern). `auth.env_var` wird auf `preset.auth_env_var` gesetzt (ohne
     Rückfrage; nur im `Custom`-Pfad wird weiterhin gefragt).
   - `extra_env` aus dem Preset wird mitgeschrieben.
   - Optionaler „Test the provider now?"-Schritt wie bisher (`GET /v1/models`).
3. Geschrieben wird über den bestehenden `_append_provider` (ruamel-Round-Trip,
   Kommentare bleiben erhalten). `_append_provider` muss um `extra_env`
   erweitert werden.

### Nicht-interaktiv: `--preset`

`leitum provider add --preset <key> [--name <name>] [--base-url <url>]` legt den
Provider ohne Interaktion an (für Skripte, CI, Tests):

- `<key>` unbekannt → Exit 2 mit Liste gültiger Keys.
- `--name` überschreibt `default_name`, sonst `default_name`. Kollision → Exit 2.
- `--base-url` überschreibt `preset.base_url`.
- Kein Test-Request im nicht-interaktiven Modus (kein Netzwerk erzwingen).
- Ausgabe: „Provider '<name>' added to <path>."

## `leitum provider detect` (Auto-Erkennung)

Neues Subcommand unter `leitum provider`. Wird mit **Issue B** geliefert
(abhängig von der Registry aus Issue A).

Ablauf:

1. Für jedes Preset mit nicht-leeren `detect_ports`: probe
   `GET <base_url>/v1/models` mit kurzem Timeout (~1.5 s). Der Request toleriert
   sowohl authentifizierte als auch offene (`200` ohne Auth) Antworten.
2. Sammle die erreichbaren Server samt Anzahl entdeckter Modelle.
3. Ausgabe:
   - Keine gefunden → Hinweis, dass kein lokaler Server auf den bekannten Ports
     läuft, plus Verweis auf `provider add`. Exit 0.
   - Einer/mehrere gefunden → pro Server eine Zeile (`display`, `base_url`,
     Modellanzahl). Interaktiv: Mehrfachauswahl, welche hinzugefügt werden
     sollen.
4. Für jeden ausgewählten Server:
   - Provider wie im Preset-Pfad anlegen (Name = `default_name`, bei Kollision
     einen Suffix `-2` etc. vorschlagen bzw. überspringen).
   - Optional (Confirm) die entdeckten Modelle als `models:`-Liste einpinnen,
     damit keine spätere Discovery nötig ist.
5. `provider detect --json` (optional) gibt die Erkennung maschinenlesbar aus,
   ohne zu schreiben — nützlich für Tests und Skripte.

Der Eintrag `Detect local providers…` in `provider add` (Issue A/B) ruft dieselbe
Erkennungsroutine auf.

### Sicherheit

- Es werden nur `localhost`/`127.0.0.1`-Ports geprobt (aus den Presets). Kein
  Scan über andere Hosts.
- Keine Tokens in Ausgabe/Logs (die Platzhalter sind ohnehin keine Geheimnisse,
  aber die Redaction-Regeln aus PRD 01/04 gelten).

## Dokumentation (Issue C)

- **README**: Abschnitt „Local providers" unter „Providers", plus Anpassung der
  Intro/Roadmap-Erwähnung.
- **`docs/providers/ollama.md`**, **`docs/providers/lm-studio.md`**,
  **`docs/providers/local.md`** (llama.cpp, vLLM, generisch). Jeweils:
  - Versionsanforderungen (Ollama 2026-01-Release+, LM Studio 0.4.1+).
  - Manuelles Setup über `api-providers.yaml` (funktioniert heute schon).
  - Preset-Weg (`leitum provider add --preset <key>`) und
    `leitum provider detect`.
  - Empfohlene Kontextlänge und Modellwahl (Modell muss Tool-Calling können).
- **`docs/troubleshooting.md`**: Ergänzungen zu
  - `GET /v1/messages/count_tokens?beta=true` (nicht von allen lokalen Servern
    unterstützt; i. d. R. nicht fatal),
  - Kontextlänge (32K Floor / 64K Sweet Spot),
  - „Modell unterstützt keine Tools" als häufige Fehlerursache,
  - Versionsanforderungen.
- **`docs/roadmap.md`** und **PRD 07**: Ollama/lokale Presets von „geplant" nach
  „ausgeliefert" bewegen; die drei neuen `docs/providers/`-Seiten in die
  Struktur aufnehmen.

## Akzeptanzkriterien

- Eine `api-providers.yaml`, deren einziger Provider ein per Preset erzeugter
  Ollama-Eintrag ist, führt bei `leitum --dry-run claude` zu
  `ANTHROPIC_BASE_URL=http://localhost:11434`,
  `ANTHROPIC_AUTH_TOKEN=***redacted***` und (bei gesetztem Slot) den
  `ANTHROPIC_DEFAULT_*_MODEL`-Variablen — ohne Schema-/Migrationsänderung.
- `leitum provider add --preset ollama` legt nicht-interaktiv einen validen
  Provider an; `--preset unknown` endet mit Exit 2 und Key-Liste.
- Der interaktive Preset-Pfad stellt für lokale Presets **keinen** Secret-/
  Password-Prompt.
- `leitum provider detect` findet einen laufenden lokalen Server (in Tests
  gemockt), listet die Modellanzahl und bietet das Hinzufügen an; ohne
  laufenden Server exit 0 mit Hinweis.
- `schema_version` unverändert `1`; `ruff format`, `ruff check`,
  `mypy --strict`, `pytest` sind grün.
- Dokumentation für Ollama und LM Studio vorhanden und aus sich heraus
  verständlich.

## Teststrategie

- **Presets (Unit)**: Registry lädt; Keys eindeutig; jedes Preset erfüllt die
  PRD-01-`name`-Regex; `base_url` gut geformt.
- **`provider add --preset` (Unit)**: nicht-interaktiv gegen eine temporäre
  `api-providers.yaml` (Muster wie `tests/unit/commands/test_provider_io.py`);
  prüft geschriebenen Eintrag inkl. `extra_env`; Kollision → Exit 2; unbekannter
  Key → Exit 2.
- **`provider detect` (Unit)**: httpx via `respx` mocken — je ein erreichbarer
  und ein nicht erreichbarer Port; prüft Auswahlliste bzw. „nichts gefunden".
- **Interaktiver Wizard**: `questionary` wie in bestehenden Selektions-Tests
  mocken; verifizieren, dass der Preset-Pfad keinen Password-Prompt auslöst.
- **Integration**: `leitum --dry-run claude` mit einer Ollama-Preset-Config
  ergibt das erwartete Environment (Muster wie
  `tests/integration/test_end_to_end.py`).

## Referenzen

- Ollama Anthropic compatibility: https://docs.ollama.com/api/anthropic-compatibility
- Ollama × Claude Code: https://ollama.com/blog/claude
- LM Studio Anthropic-compat: https://lmstudio.ai/docs/developer/anthropic-compat
- LM Studio × Claude Code: https://lmstudio.ai/docs/integrations/claude-code
