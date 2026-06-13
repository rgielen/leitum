Ich möchte ein kleines CLI Tool in Python erstellen, dass einen Coding Agenten wie Claude Code so launcht, dass alternative LLM Router und Modelle verwendet werden können.

Ein gutes Beispiel für das was ich möchte ist z.B. das der Ollama CLI Befehlt `ollama launch`, den ich in der Kommandozeile vor `claude` einfüge und damit auf lokale Ollama Modelle statt Anthropic Modelle und APIs zugreife - siehe auch https://docs.ollama.com/integrations/claude-code.
 
Ein anderes Wertkzeug, dass das als eine Funktion hat ist das der CLI von OMLX (https://github.com/jundot/omlx). Das Tool besitzt ebenfalls einen `launch` Befehl hat. Das CLI ist selber in Python geschrieben, hier ist der relevante Code für den Launch von Claude Code mit so angepasstem Environment, dass aben die durch OMLX bereitgestellten Modelle ausgewählt und verwendet werden können.

Mein CLI Tool soll `leitum` heißen und nach dem Vorbild der obigen Beispiele funktionieren, d.h. mit dem Aufruf `leitum claude` Claude Code mit einem vorgegeben, konfigurierten API-Provider aufrufen. Für den Start soll erst einmal nur Claude Code unterstützt werden, andere Tools wie copilot-cli, opencode etc. folgen vielleicht später.

Hier meine funktionalen Ideen:

* Konfiguration über YAML, mit Konfigurationsdateien in $HOME/.config/leitum
* `api-providers.yaml` zum Hinterlegen von Providern mit Zugangsdaten. Jeder Provider hat einen Identifier/Namen, eine URL und ein API Token. Zusätzlich *kann* eine Liste der Modelle hinterlegt werden, pro Modell mit der Angabe des technischen Modellnamen sowie (optional) eines Anzeigenamens.
* Der Referenzprovider für die erste Iteration des Projektes ist Requesty.ai. Die Standard Claude Code Integration von Requesty ist hier beschrieben: https://docs.requesty.ai/integrations/claude-code
* Das Tool speichert die zuletzt gesetzten Kontext-Parameter in seinem Config-Verzeichnis, z.B. den zuletzt ausgewählten Provider. Hier denke ich an eine ähnliche Verwaltung wie einen Kubernetes kubectl context.yaml, wo mehrere Kontexte hinterlegt werden können und ein current-context Feld den zuletzt gesetzten Kontext sich merkt und beim nächsten Start widerverwendet.
* Ein Provider kann mit dem Parameter `--provider <name>` bzw. `-p <name>` vorgegeben werden. Wenn das nicht geschieht und außerdem mehr als ein Provider hinterlegt ist, dann soll eine Auswahldialog per Curses oder ähnlichem angezeigt werden, um einen Provider zu wählen. Der zuletzt gewählte ist immer vorbelegt. Jede Auswahl im der Kontext-Config ("current-context") gespeichert für den nächsten Start. Wenn nur ein Provider da ist, wird dieser automatisch verwendet. `--use-last-provider` bzw. `-P` überspringt den Provider-Auswahldialog und benutzt den zuletzt ausgewählen.
* Danach erfolgt die Modellauswahl, ähnlich im grundsätzlichen Vorgehen
	* Verfügbare Modelle sind entweder die beim Provider als Liste der Verfügbaren per API Call erhaltenen, oder die in `api-providers.yaml` vorgegebenen. Wenn es vorgegebene git, haben die immer Vorrang und die Liste der verfügbaren wird nicht abgerufen bzw. ignoriert.
	* die Modellauswahl erfolgt wieder über eine curses Liste, wenn nicht schon vorgegeben über die folgend beschriebenen Parameter und natürlich nur, wenn mehr als ein Modell verfügbar ist. Vorbelegt ist immer die letzte Auswahl, falls vorhanden. Auswählbar sind
		* START-MODELL, entspricht dem Modell das beim Aufruf von `claude` mit dem `--model` Parameter übergeben wird
		* OPUS-MODELL, zum Setzen der Environment Variable `ANTHROPIC_DEFAULT_OPUS_MODEL` für den Start von `claude`
		* SONNET-MODELL, zum Setzen der Environment Variable `ANTHROPIC_DEFAULT_SONNET_MODEL` für den Start von `claude`
		* HAIKU-MODELL, zum Setzen der Environment Variable `ANTHROPIC_DEFAULT_HAIKU_MODEL` für den Start von `claude`
	* `--model <name>` bzw. `-m <name>` wählt alternativ das START-MODELL direkt aus. `--use-last-model` bzw. `-M` wählt, falls vorhanden, das letzte Modell aus und führt zum Überspringen der interaktiven Modellauswahl
	* `--opus <name>` bzw. `-o <name>` wählt alternativ das OPUS-MODELL direkt aus. `--use-last-opus` bzw. `-O` wählt, falls vorhanden, das letzte Modell aus
	* `--sonnet <name>` bzw. `-s <name>` wählt alternativ das SONNET-MODELL direkt aus. `--use-last-sonnet` bzw. `-S` wählt, falls vorhanden, das letzte Modell aus
	* `--haiku <name>` bzw. `-h <name>` wählt alternativ das HAIKU-MODELL direkt aus. `--use-last-haiku` bzw. `-H` wählt, falls vorhanden, das letzte Modell aus
* nach erfolgten Vorgaben launcht claude mit der gewählten Umgebungsvorgabe.

Weitere nicht-fachliche Ideen und Vorgaben:
* Sprache für Dokumentation, Commit-Messages, Pull Requests und ähnliches ist Englisch
* Sprache für PRDs ist die des Prompts, also jetzt gerade Deutsch
* das Tool soll auf Pypi veröffentlicht werden und per uvx oder Homebrew ausgeführt bzw. installiert werden können. Referenzsystem ist zunächst ein aktuelles macOS.
* Die Dokumentation des Tools soll in Markdown gestaltet sein, so dass bei einer Veröffentlichung auf GitHub ein sofortiger Einstig in die Dokumentation erfolgen kann

Bitte mache folgendes:
1. durchleuchte die gemachten Vorgaben und hinterfrage diese auf Konsistenz und Sinnhaftigkeit. Mache Verbesserungsvorschläge, wenn passend. Diskutiere intensiv alle offenen Fragen, Unklarheiten und Entscheidungen mit mir. Benutze die erarbeiteten Erkenntnisse für die folgenden Aufgaben
2. Erstelle eine CLAUDE.md, die alle grundsätzlichen Vorgaben für das Projekt enthält. Halte diese so ausführlich wie nötig und so knapp wie möglich. Halte darin auch fest, dass das der gesamte Kommunikationsstil im Projekt sein soll.
3. Erstelle danach einen detaillierten Umsetzungsplan in Form von PRD-Dokumenten. Das beinhaltet den Produktiven Code, Tests und Dokumentation. Stelle Fragen, wenn nötig. Setze noch nichts aus den erstellten PRDs um.




	
