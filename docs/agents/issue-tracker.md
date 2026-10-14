# Issue tracker: Obsidian vault (flowctl)

Specs and tickets for **mega-sena-ml** live as Markdown files in the Obsidian vault, not in this repository.

Find the project directory with `flowctl where` (it prints `<VAULT_PATH>/Pessoal/mega-sena-ml`). Below, `<project>` means that directory.

## Conventions

- One feature per spec: `<project>/specs/<feature-slug>.md`. The file starts with frontmatter (`feature`, `status: draft`, `created`); see the `vault-conventions` skill.
- Tickets are one file each: `<project>/tickets/T-<NNN>-<slug>.md`. Get the next id with `flowctl ticket next-id`. The format is defined by the `ticket-format` skill and checked by `flowctl ticket lint`.
- Blocking edges are ticket ids in the `blocked_by` frontmatter list (for example `[T-001, T-002]`), never plain numbers.
- Triage state is the `status` frontmatter field: `ready` for the `ready-for-agent` role when nothing blocks the ticket, `backlog` while it is blocked. Only `flowctl ticket set-status` changes status after creation.
- Comments and conversation history append to the bottom of the file under `## Comments`.

## When a skill says "publish to the issue tracker"

1. Write the file under `<project>/specs/` or `<project>/tickets/` (create no other layout).
2. For tickets run `flowctl ticket lint`, fix every error, then `flowctl kanban sync`.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path, or resolve an id with `flowctl ticket show T-001`.

## Parent issues and external trackers

Not used. Do not call `gh issue` or similar. Do not close or modify anything outside the vault.

## Wayfinding operations

Not configured. Use specs and tickets only.
