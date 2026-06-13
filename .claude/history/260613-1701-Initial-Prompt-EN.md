I want to build a small Python CLI tool that launches a coding agent such as Claude Code in a way that allows alternative LLM routers and models to be used.

A good example of what I want is the Ollama CLI command `ollama launch`, which I prepend to `claude` on the command line so that I access local Ollama models instead of Anthropic models and APIs — see also https://docs.ollama.com/integrations/claude-code.

Another tool that has this as a feature is the CLI of OMLX (https://github.com/jundot/omlx). It also has a `launch` command. The CLI itself is written in Python; here is the relevant code for launching Claude Code with an adjusted environment so that the models provided by OMLX can be selected and used.

My CLI tool shall be called `leitum` and work along the lines of the examples above, i.e. invoking `leitum claude` to call Claude Code with a pre-configured API provider. To begin with, only Claude Code shall be supported; other tools such as copilot-cli, opencode, etc. may follow later.

Here are my functional ideas:

* Configuration via YAML, with configuration files located in `$HOME/.config/leitum`
* `api-providers.yaml` to register providers along with their credentials. Each provider has an identifier/name, a URL, and an API token. Additionally, a list of models *may* be provided, with each model specifying the technical model name and (optionally) a display name.
* The reference provider for the first iteration of the project is Requesty.ai. The standard Claude Code integration for Requesty is described here: https://docs.requesty.ai/integrations/claude-code
* The tool stores the most recently set context parameters in its config directory, e.g. the last selected provider. I'm thinking of a management approach similar to a Kubernetes kubectl `context.yaml`, where multiple contexts can be stored and a `current-context` field remembers the most recently set context and reuses it on the next start.
* A provider can be specified via the parameter `--provider <name>` or `-p <name>`. If this is not done and more than one provider is registered, a selection dialog (via Curses or similar) shall be shown to pick a provider. The most recently chosen one is always pre-selected. Each selection is stored in the context config (`current-context`) for the next start. If only one provider is present, it is used automatically. `--use-last-provider` or `-P` skips the provider-selection dialog and uses the most recently chosen provider.
* After that, the model selection happens, similar in its basic approach:
    * Available models are either those retrieved from the provider as a list of available models via an API call, or those pre-configured in `api-providers.yaml`. If pre-configured ones exist, they always take precedence and the list of available models is not retrieved or is ignored.
    * The model selection again uses a curses list, unless already specified via the parameters described below, and of course only if more than one model is available. The most recent selection is always pre-selected, if one exists. The selectable items are:
        * START MODEL — corresponds to the model passed to `claude` via the `--model` parameter
        * OPUS MODEL — sets the environment variable `ANTHROPIC_DEFAULT_OPUS_MODEL` for the `claude` start
        * SONNET MODEL — sets the environment variable `ANTHROPIC_DEFAULT_SONNET_MODEL` for the `claude` start
        * HAIKU MODEL — sets the environment variable `ANTHROPIC_DEFAULT_HAIKU_MODEL` for the `claude` start
    * `--model <name>` or `-m <name>` alternatively selects the START MODEL directly. `--use-last-model` or `-M`, if available, selects the last model and skips the interactive model selection.
    * `--opus <name>` or `-o <name>` alternatively selects the OPUS MODEL directly. `--use-last-opus` or `-O`, if available, selects the last model.
    * `--sonnet <name>` or `-s <name>` alternatively selects the SONNET MODEL directly. `--use-last-sonnet` or `-S`, if available, selects the last model.
    * `--haiku <name>` or `-h <name>` alternatively selects the HAIKU MODEL directly. `--use-last-haiku` or `-H`, if available, selects the last model.
* Once the specifications are in place, `claude` is launched with the chosen environment configuration.

Further non-functional ideas and requirements:
* The language for documentation, commit messages, pull requests, and similar artifacts is English.
* The language for PRDs is the language of the prompt — at this moment, German.
* The tool shall be published on PyPI and be runnable/installable via `uvx` or Homebrew. The reference system is, for now, a current version of macOS.
* The tool's documentation shall be authored in Markdown so that, when published on GitHub, the documentation is immediately accessible.

Please do the following:
1. Scrutinize the requirements above and challenge them for consistency and soundness. Make improvement suggestions where appropriate. Discuss intensively with me all open questions, ambiguities, and decisions. Use the insights gained for the subsequent tasks.
2. Create a `CLAUDE.md` that contains all foundational requirements for the project. Keep it as detailed as necessary and as concise as possible. Also state therein that this is meant to be the overall communication style for the project.
3. Afterwards, create a detailed implementation plan in the form of PRD documents. This includes production code, tests, and documentation. Ask questions if needed. Do not yet implement anything from the created PRDs.
