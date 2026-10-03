# Instructions for Copilot code review

A review comment is useful only when it names a concrete failure: the input or state, and what
goes wrong. Fewer, sure comments are better than many.

## Comment on

1. A bug: wrong result, crash, data loss, or a regression of behaviour that works on `main`.
2. A secret, token or credential disclosed (logs, errors, files, release artefacts).
3. A security hole: command or path injection, unsafe file permissions, untrusted input executed.
4. A test weakened so that it no longer checks what it claims.
5. Documentation or agent instructions (`README.md`, `CLAUDE.md`, `.claude/**`) that contradict
   the code or each other, or name a file, command or flag that does not exist.

## Do not comment on

- Style, naming, formatting, type-hint or docstring wording.
- Defence in depth or performance, unless one of the cases above follows.
- Suggestions to add tests, logging or abstractions without a concrete defect.
