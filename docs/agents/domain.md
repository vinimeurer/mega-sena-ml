# Domain docs

How the engineering skills consume domain documentation for **mega-sena-ml**. Layout: single-context.

## Before exploring, read these

- `GLOSSARY.md` in the vault project directory (`flowctl where`).
- `adr/` in the vault project directory: read ADRs that touch the area you are about to work in.

If any of these do not exist, proceed silently. The `domain-modeling` skill (reached through `grill-with-docs`) creates them lazily when terms or decisions are settled. When it does, write them to the vault project directory, not to this repository.

## File structure

```
<vault>/Pessoal/mega-sena-ml/
├── GLOSSARY.md
├── adr/
│   ├── 0001-short-title.md
│   └── 0002-another-decision.md
├── specs/
└── tickets/
```

## Use the glossary's vocabulary

Name domain concepts as `GLOSSARY.md` defines them in tickets, specs, test names and commit messages. Do not drift to synonyms it avoids.

## Flag ADR conflicts

If your output contradicts an existing ADR, say so explicitly instead of silently overriding it:

> Contradicts ADR-0007 (event-sourced orders), but worth reopening because...
