# PRD 09 — Dependency- und Release-Automatisierung

Implementation status: implemented — pending the manual installation of the
Renovate app and a first end-to-end release through the chain.

Dieses PRD beschreibt, wie Abhängigkeiten von `leitum` selbsttätig aktuell
gehalten werden und wie daraus ohne Handgriff eine Veröffentlichung entsteht.
Es ersetzt den Absatz „Dependabot (GitHub-nativ) für Dependency-Updates" aus
PRD 07 und verändert den dort beschriebenen Release-Workflow.

## Ausgangslage

Die Veröffentlichung ist heute ein manuelles Dreischritt-Ritual: Version in
`pyproject.toml` anheben, committen, Tag `vX.Y.Z` pushen. Der Tag löst
`.github/workflows/release.yml` aus, das auf PyPI publiziert und über
`homebrew-bump.yml` eine PR im Tap `rgielen/homebrew-taps` öffnet.

Das Ritual wird nachweislich nicht durchgehalten:

- `CHANGELOG.md` endet bei `0.1.4`. Die veröffentlichten Versionen `0.1.5` und
  `0.1.6` haben keinen Abschnitt.
- `uv.lock` führt das Wurzelprojekt mit `version = "0.1.4"`, während
  `pyproject.toml` bei `0.1.6` steht.
- Ein Tag `0.0.0` ohne `v`-Präfix liegt im Repository herum.

Dependency-Updates finden überhaupt nicht statt. Weder Dependabot noch Renovate
sind eingerichtet; die in `uv.lock` festgehaltenen Versionen altern unbemerkt.

## Ziel

1. Abhängigkeiten (Runtime, Dev-Tooling, GitHub Actions, transitive über
   Lockfile-Pflege) werden fortlaufend aktualisiert. Jedes Update durchläuft die
   volle CI-Matrix und wird bei Grün automatisch gemergt.
2. Eine wirksame Änderung auf `main` führt ohne Handgriff zu Versions-Bump,
   Changelog-Eintrag, Tag, PyPI-Release, GitHub-Release und Homebrew-PR.
3. Manueller Eingriff ist nur nötig, wenn etwas fehlschlägt.

## Kernentscheidung: was ist eine „wirksame Änderung"?

Die zentrale Einsicht ist, dass ein Dependency-Update bei `leitum` in aller
Regel **nichts** an dem verändert, was Nutzer bekommen:

- `pyproject.toml` deklariert offene Untergrenzen (`typer>=0.12`,
  `httpx>=0.27`, …). Ein neues `httpx` liegt weiterhin innerhalb der Range,
  also ändert Renovate nur `uv.lock`.
- `uv.lock` wird nicht ins sdist/Wheel gepackt. Die Dependency-Metadaten des
  PyPI-Artefakts sind die Ranges, nicht die gelockten Versionen.
- Die Homebrew-Formel erzeugt ihre `resource`-Blöcke aus der pip-Auflösung des
  veröffentlichten sdists, nicht aus `uv.lock`.

Ein Release für ein reines Lockfile-Update wäre daher bitidentisch zum
Vorgänger — reine Versionsinflation. `uv.lock` ist für `leitum` ein
**Frühwarn-Instrument**: die CI beweist laufend, dass das Projekt gegen die
neuesten Versionen seiner Abhängigkeiten baut, testet und typprüft.

Daraus folgt die Release-Policy:

| Änderung | Commit-Typ | Release? |
|---|---|---|
| Quellcode-Feature | `feat:` | ja, Minor |
| Quellcode-Fehlerbehebung | `fix:` | ja, Patch |
| Sicherheitsfix, hebt Untergrenze in `pyproject.toml` | `fix(deps):` | ja, Patch |
| Dependency-Update nur in `uv.lock` | `chore(deps):` | nein |
| Dev-Dependency (ruff, mypy, pytest, …) | `chore(deps):` | nein |
| GitHub-Actions-Version | `chore(deps):` | nein |
| Lockfile-Pflege (transitive) | `chore(deps):` | nein |
| Dokumentation, Tests, Refactoring, CI | `docs:`/`test:`/`refactor:`/`ci:` | nein |

Nicht-releasende Änderungen gehen nicht verloren: sie sammeln sich auf `main`
an und gehen mit dem nächsten `feat:`/`fix:` raus.

## Zielbild

```
Renovate PR ─→ CI (3.11-3.13 × macOS/Ubuntu) ─┬─ grün → Renovate merged (rebase)
                                              └─ rot  → PR bleibt offen  ← Eingriff

Push main ──→ CI ──→ grün ──→ Workflow "Release"
                               ├─ feat:/fix: seit letztem Tag
                               │   → PSR: Version + CHANGELOG + uv.lock
                               │          + Commit + Tag + GitHub-Release
                               │   → uv build → PyPI (OIDC) → Homebrew-PR
                               └─ sonst: kein Release
```

## Randbedingungen

Diese vier Punkte sind bei jeder Umsetzung zu respektieren; ihre Verletzung
bricht die Kette an einer Stelle, die im Grünlauf nicht auffällt.

1. **PyPI Trusted Publishing ist an den Workflow-Dateinamen gebunden.** Der
   konfigurierte Publisher zeigt auf `release.yml`. Die Datei behält Namen und
   `name: Release`; nur Trigger und Inhalt werden umgebaut. Andernfalls muss die
   Trusted-Publisher-Konfiguration auf PyPI von Hand nachgezogen werden.
2. **Mit `GITHUB_TOKEN` erzeugte Events lösen keine Workflows aus.** Der von PSR
   gepushte Bump-Commit und Tag starten daher weder CI noch einen zweiten
   Release-Lauf. Das ist hier erwünscht — es verhindert eine Endlosschleife und
   macht einen PAT entbehrlich, solange die gesamte Kette in **einem** Workflow
   liegt.
3. **Das Repository hat weder Branch Protection noch Rulesets**, und
   `allow_auto_merge` ist `false`. GitHubs natives Auto-Merge würde ohne
   Required Checks auch rote PRs mergen. Renovate muss deshalb mit
   `platformAutomerge: false` seinen eigenen, statusprüfenden Merge verwenden.
   Es sind **keine** Repository-Einstellungen zu ändern.
4. **Das Default-Workflow-Token hat nur `read`.** Jeder Job deklariert seine
   Rechte explizit.

## Komponente 1 — Renovate

### Betrieb

Gehostete **Mend Renovate GitHub App** (`github.com/apps/renovate`), kostenlos
für öffentliche Repositories. Sie wird einmalig für `rgielen/leitum` installiert
— ein manueller, nach außen wirkender Schritt, der nicht automatisiert werden
kann.

Der Betrieb als selbstgehostete GitHub Action wurde verworfen: mit
`GITHUB_TOKEN` erzeugte PRs lösen keine Workflows aus, die CI liefe also nie auf
Renovate-PRs und Auto-Merge-auf-Grün wäre unmöglich. Es bräuchte zwingend einen
zusätzlichen PAT oder eine eigene GitHub App.

### `renovate.json`

Im Repository-Root. Verbindliche Festlegungen:

- `extends`: `["config:recommended", ":semanticCommits"]`.
- `automerge: true`, `automergeType: "pr"`, `automergeStrategy: "rebase"` —
  `CLAUDE.md` schreibt Rebase-Merges für einen flachen Commit-Log vor.
- `platformAutomerge: false` — siehe Randbedingung 3.
- `minimumReleaseAge: "3 days"` — Karenzzeit gegen zurückgezogene oder
  fehlerhafte Releases.
- `lockFileMaintenance`: aktiviert, wöchentlich, mit Auto-Merge. Hält
  transitive Abhängigkeiten frisch.
- `packageRules`: Runtime-Dependencies, Dev-Dependencies und GitHub Actions
  committen als `chore(deps)`. Dev-Dependencies und Actions dürfen gruppiert
  werden, um die PR-Zahl zu begrenzen.
- `vulnerabilityAlerts`: aktiviert, mit angehobener Untergrenze in
  `pyproject.toml` (`rangeStrategy: "bump"`), Commit-Typ `fix`, ohne
  Karenzzeit. Dies ist der **einzige** Pfad, auf dem ein Dependency-Update ein
  Release auslöst.
- `osvVulnerabilityAlerts: true` für Meldungen über GitHubs eigene Datenbank
  hinaus.

Die Renovate-Dokumentation ist widersprüchlich, ob der Schlüssel unterhalb von
`vulnerabilityAlerts` `rangeStrategy` oder `vulnerabilityFixStrategy` heißt. Die
Umsetzung prüft das gegen `renovate-schema.json` und validiert die Datei mit
`renovate-config-validator`.

Renovates uv-Unterstützung hat dokumentierte Kanten — es sind Fälle bekannt, in
denen `pyproject.toml` angefasst wird, ohne `uv.lock` mitzuziehen. Die ersten
Bot-PRs sind daher bewusst zu prüfen.

### Akzeptanzkriterien

- `renovate-config-validator` meldet keine Fehler.
- Eine Dependency-PR läuft durch die CI und wird per Rebase gemergt, ohne dass
  ein Release entsteht.
- Eine PR mit roter CI bleibt offen und wird nicht gemergt.
- Ein simulierter Vulnerability-Alert erzeugt eine PR, die die Untergrenze in
  `pyproject.toml` anhebt und als `fix(deps): …` committet.

## Komponente 2 — Conventional Commits erzwingen

Weil per Rebase gemergt wird, landet jeder einzelne Commit auf `main`, und PSR
leitet daraus den Bump ab. Ein vertipptes `feat:` erzeugt still ein falsches
oder gar kein Release. Die Konvention wird deshalb geprüft, nicht nur
vorgeschrieben.

Neuer Job in `.github/workflows/ci.yml`, nur bei `pull_request`: alle Commits
aus `origin/main..HEAD` werden gegen das Conventional-Commits-Muster geprüft.
Erlaubte Typen entsprechen `CLAUDE.md`: `feat`, `fix`, `docs`, `test`,
`refactor`, `chore`, `ci`, `build`, `perf`, `style`. Optionaler Scope in
Klammern, optionales `!` für Breaking Changes.

Bewusst als kleines Shell-Skript statt commitlint: das Repository hat keine
Node-Toolchain, und die Regel ist ein Regex.

### Akzeptanzkriterien

- Ein Commit mit gültigem Präfix passiert den Job.
- Ein Commit ohne Präfix oder mit unbekanntem Typ lässt den Job fehlschlagen
  und nennt den beanstandeten Commit.
- Renovates eigene Commits (`chore(deps): …`, `fix(deps): …`) passieren den Job.

## Komponente 3 — python-semantic-release

### Wahl der Engine

`python-semantic-release` (PSR) ist Python-nativ, konfiguriert sich in
`pyproject.toml` und hat einen offiziellen uv-Integrationsguide. Es arbeitet
ohne Release-PR: nach grüner CI auf `main` bestimmt es den Bump aus den
Conventional Commits, schreibt Version und Changelog, committet, taggt und
veröffentlicht in einem Durchgang. Das trifft die Vorgabe „manueller Eingriff
nur bei Problemen" am direktesten.

Verworfen: **release-please** sammelt Änderungen in einer Release-PR, deren
Merge der Release-Knopf ist — ein Schritt weniger automatisch, und für die volle
Automatik wäre ein PAT oder App-Token nötig. Ein **eigenes Bash-Skript** würde
Commit-Parser und Changelog-Erzeugung dauerhaft in unsere Wartung holen.

### Konfiguration

`[tool.semantic_release]` in `pyproject.toml`:

- `version_toml = ["pyproject.toml:project.version"]` — einzige
  Wahrheitsquelle für die Version.
- `commit_parser = "conventional"`, `tag_format = "v{version}"` (deckt sich mit
  den bestehenden Tags; der Streu-Tag `0.0.0` matcht nicht und ist zu löschen).
- `allow_zero_version = true` und `major_on_zero = false`. Das Projekt ist
  bewusst pre-1.0 (PRD 07: „v1 startet bei 0.1.0, da öffentliche API noch
  fluide"). Ein Breaking Change soll `0.2.0` ergeben, nicht `1.0.0`.
- `build_command` gemäß dem offiziellen uv-Guide:
  `uv lock --upgrade-package "$PACKAGE_NAME"`, dann `git add uv.lock`, dann
  `uv build`. Das hält den `leitum`-Eintrag in `uv.lock` dauerhaft synchron und
  packt ihn in den Release-Commit — genau die Drift, die heute besteht.
- `changelog.mode = "update"` mit Einfügemarke, damit der bestehende
  Keep-a-Changelog-Kopf erhalten bleibt.

**Ausführungsform.** Die PSR-GitHub-Action ist eine Docker-Action;
`build_command` läuft im Container und sieht ein per `astral-sh/setup-uv`
installiertes `uv` nicht. Bevorzugt wird deshalb der CLI-Aufruf auf dem Runner
(`uvx --from python-semantic-release semantic-release version`), weil dort die
uv-Toolchain ohnehin vorhanden ist. Fallback: uv-Installation innerhalb von
`build_command` gemäß der GHA-Variante des Guides.

### Vorbereitende Konsistenz-Arbeiten

PSR schreibt in `CHANGELOG.md` und `uv.lock` fort; beide müssen vorher stimmen.

- `CHANGELOG.md`: Abschnitte für `0.1.5` und `0.1.6` nachtragen. Inhalt aus den
  Commits:
  - `0.1.5` — Fixed: questionary-2.1.1-Inkompatibilität des Suchfilters
    (`6fb6bf7`). Changed: Homebrew-Bump nur noch über `url`+`sha256`
    (`eb4674d`, `7d63ec3`).
  - `0.1.6` — Added: Ctrl-R (refresh) und Ctrl-S (save-local) in der
    Modellauswahl (`a87c179`).
- Einfügemarke für PSR unterhalb von `## [Unreleased]` setzen.
- `uv lock` ausführen, damit der `leitum`-Eintrag von `0.1.4` auf `0.1.6` zieht.
- Tag `0.0.0` löschen (lokal und remote).

### Akzeptanzkriterien

- `semantic-release version --print` auf einem Stand mit einem `feat:`-Commit
  seit dem letzten Tag gibt die nächste Minor-Version aus.
- Derselbe Aufruf auf einem Stand mit ausschließlich `chore(deps):`-Commits
  meldet, dass kein Release ansteht.
- Ein Testlauf schreibt Version in `pyproject.toml`, Abschnitt in
  `CHANGELOG.md` und Version in `uv.lock` konsistent fort.

## Komponente 4 — Workflow „Release"

`.github/workflows/release.yml` wird umgebaut; Dateiname und `name: Release`
bleiben (Randbedingung 1).

- **Trigger**: `workflow_run` auf `workflows: ["CI"]`, `types: [completed]`,
  `branches: [main]`. Dasselbe Muster nutzt `homebrew-bump.yml` bereits.
- **Guards**:
  - `github.event.workflow_run.conclusion == 'success'`.
  - `main` steht noch auf `github.event.workflow_run.head_sha`. Andernfalls
    überspringen — der spätere CI-Lauf holt es nach. Ohne diesen Guard könnte
    bei zwei dicht aufeinanderfolgenden Pushes ungetesteter Code released
    werden, weil der Job `main` auscheckt und nicht den getesteten Commit.
- **`concurrency`**: Gruppe `release`, `cancel-in-progress: false`.
- **Rechte**: `contents: write` (Bump-Commit, Tag, GitHub-Release) und
  `id-token: write` (Trusted Publishing).
- **Schritte**: Checkout `main` mit voller Historie → uv einrichten → PSR
  `version` → nur wenn ein Release entstand: `pypa/gh-action-pypi-publish`
  (unverändert, OIDC) → Distributionsartefakte an das von PSR erzeugte
  GitHub-Release hängen → Homebrew-Bump aufrufen.
- `softprops/action-gh-release` mit `generate_release_notes` entfällt: PSR legt
  das Release mit den generierten Changelog-Notizen an.
- Kein `continue-on-error`. Ein Fehlschlag muss laut sein, sonst bleibt eine
  kaputte Release-Kette unbemerkt.

### Akzeptanzkriterien

- Ein Push mit ausschließlich `chore(deps):` erzeugt keinen Tag und kein
  Release; der Workflow endet grün.
- Ein Push mit `fix:` erzeugt Bump-Commit, Tag, GitHub-Release mit
  Changelog-Notizen, PyPI-Upload und Homebrew-PR.
- Ein fehlgeschlagener CI-Lauf startet den Release-Workflow nicht.

## Komponente 5 — Homebrew-Bump

`homebrew-bump.yml` leitet den Tag heute aus
`github.event.workflow_run.head_branch` ab. Das funktionierte nur, weil
„Release" tag-getriggert war; nach dem Umbau stünde dort `main`.

- `on: workflow_call` mit Pflicht-Input `tag` ergänzen; `workflow_dispatch`
  für den manuellen Nachzug bleibt erhalten.
- Der `workflow_run`-Trigger entfällt. Der Aufruf erfolgt aus `release.yml` als
  `needs`-Job mit dem Tag-Output von PSR.
- Das ausführliche, kommentierte Bump-Skript bleibt unangetastet — einschließlich
  des dokumentierten Verzichts auf `brew bump-formula-pr` und des
  PyPI-CDN-Retry.
- `secrets: inherit` bzw. explizite Weitergabe von `HOMEBREW_TAP_TOKEN`.

### Akzeptanzkriterien

- Nach einem echten Release existiert eine PR `leitum <version>` im Tap mit
  korrekten `url`- und `sha256`-Werten.
- `workflow_dispatch` mit explizitem Tag funktioniert weiterhin.

## Dokumentation

- PRD 07: „Dependabot (GitHub-nativ)" durch einen Verweis auf dieses PRD
  ersetzen; die Beschreibung des Release-Workflows an den neuen Trigger
  anpassen; den Absatz „Versionierung" um den Hinweis ergänzen, dass Tags nicht
  mehr von Hand gesetzt werden.
- `CLAUDE.md`, Abschnitt „Git workflow": das neue Release-Ritual festhalten —
  die Version wird nicht mehr von Hand gebumpt, der Commit-Typ entscheidet über
  die Veröffentlichung, `CHANGELOG.md` wird generiert.
- `README.md` und `docs/`: kurzer Hinweis auf die automatische Release-Kette.

## Risiken

- **Eine kaputte Release-Kette bleibt unbemerkt.** Schlägt PSR fehl, entsteht
  kein Release und keine laute Meldung an anderer Stelle. Gegenmaßnahme: harter
  Abbruch im Workflow; GitHub benachrichtigt über fehlgeschlagene Läufe auf
  `main`.
- **Auto-Merge ist nur so gut wie die Testsuite.** Ein Dependency-Update, das
  einen ungetesteten Codepfad bricht, gelangt unbemerkt nach `main`. Es gelangt
  aber nicht nach außen, solange kein `feat:`/`fix:` folgt — die Release-Policy
  begrenzt den Schaden.
- **Renovates uv-Unterstützung hat Kanten.** Die ersten Bot-PRs sind bewusst zu
  prüfen, insbesondere darauf, ob `pyproject.toml` und `uv.lock` gemeinsam
  aktualisiert werden.
