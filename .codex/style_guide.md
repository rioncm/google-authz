# Programming Style Guide

## General Approach

- Write code that is clear, maintainable, and easy for a competent non-professional programmer to read. Prefer elegant, simple solutions over clever or overly abstract ones.
- Assume the project owner reads code well, but does not want unnecessary complexity hidden behind magic, excessive indirection, or unexplained patterns.

## Permissions

- You may refactor existing code when it improves clarity, reduces duplication, or makes the system easier to maintain.
- You may apply DRY principles while updating existing code, especially when repeated logic is clearly emerging.
- You may suggest or create supporting libraries, helper modules, or shared utilities when functionality is reused across the codebase.
- Do not make broad architectural changes without explaining the reason and the tradeoff.
- corrent spelling and grammar as needed if your understanding of intent is clear.

## Coding Style

- Use clear names for functions, variables, files, and modules.
- Prefer small, focused functions with a single obvious purpose.
- Add simple docstrings to functions explaining what they do, especially for business logic, integrations, transformations, and non-obvious behavior.
- Avoid over-engineering. Do not introduce frameworks, abstractions, or dependencies unless they clearly reduce complexity or improve maintainability.

## Existing Code

- Do not silently work around mistakes, irregularities, dead code, unclear logic, or suspicious behavior.
- When you find something questionable, call it out clearly and explain whether it appears to be:
    - a bug
    - a design smell
    - outdated code
    - unclear intent
    - inconsistent behavior
- When intent is uncertain, ask for clarification rather than guessing.

## Documentation

- When markdown documentation already exists, update it when code behavior, setup steps, configuration, deployment, or usage changes.
- Prefer project documentation in docs/ when that folder exists.
- Keep README files accurate but concise.

- Regularly suggest updates to:
    - .codex/CONTEXT.md
    - .codex/instructions.md

- Suggest these updates when project conventions, architecture, setup details, or recurring preferences become clear.

## Testing and Validation

- When changing behavior, add or update tests when a test structure exists.
- When tests are not present, explain what validation was performed and suggest a reasonable test path.
- Prefer practical verification: run linters, unit tests, type checks, or small command-line checks when available.

## Project Fit

- Favor boring, reliable code for infrastructure, automation, ETL, Kubernetes, Airflow, APIs, and business workflows.
- Preserve operational clarity. Configuration, environment variables, credentials, paths, cron schedules, and deployment assumptions should be explicit and documented.
- Be careful with destructive operations, migrations, data rewrites, production configuration, secrets, and permissions. Explain risks before making those changes.

## Communication

- Stop and ask for clairification when you encounter ambiguity
- Summarize material changes clearly.
- Show important diffs or describe affected files.
- Mention assumptions.
- Mention unresolved questions.
- Do not hide uncertainty.

## Standing Guidance

- prefer explicit operational safety over convenience, especially for Airflow, Kubernetes, SFTP, ETL, and ERP-adjacent projects.