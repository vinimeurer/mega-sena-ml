# mega-sena-ml

Project instructions for coding agents. Planning artifacts (glossary, ADRs, specs, tickets, kanban) live in the Obsidian vault; run `flowctl where` to find them.

## Quality commands

The `validator` and `tester` agents run these. Keep them accurate; leave a line empty if it does not apply.

<!-- flow:commands -->
lint:
format:
types:
test:
build:
coverage_threshold: 85
<!-- /flow:commands -->

## Conventions

- Language: code and commits in English.
- Style: follow the existing code; formatters and linters are the authority.
- Never commit secrets; configuration comes from environment variables documented in `.env.example`.

## Agent skills

<!-- flow:agent-skills -->

### Issue tracker

Specs and tickets are Markdown files in the Obsidian vault, managed with `flowctl`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context. Glossary and ADRs live in the vault project directory. See `docs/agents/domain.md`.
