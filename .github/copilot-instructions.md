# Copilot Instructions for Patient_Explorer

Purpose: Make AI coding agents immediately productive in this greenfield sandbox by codifying current conventions, expected structure, and workflows sourced from `README.md` and `CLAUDE.md`.

## Project Snapshot
- Status: Minimal scaffold; no build system or runtime yet.
- Intent: Prototype and test code generation patterns in an App Agent PP developer environment.
- Key files: `README.md` (project overview), `CLAUDE.md` (assistant guidance and conventions).

## Tech Choices & Defaults
- Language: Prefer TypeScript over JavaScript for new code.
- Structure: Use the following baseline directories when adding code:
  - `src/`, `src/services/`, `src/utils/`, `src/components/` (if frontend)
  - `tests/` or `__tests__/`
  - `config/`, `docs/`, `public/`
- Naming:
  - Files: kebab-case (e.g., `patient-data.ts`)
  - Components: PascalCase (e.g., `PatientCard.tsx`)
  - Tests: `*.test.ts` or `*.spec.ts`

## Initial Setup Pattern (when introducing tooling)
- Create minimal configs alongside code you add:
  - `package.json` (scripts + deps), `tsconfig.json`
  - `.eslintrc.*`, `.prettierrc`, `.gitignore`
  - `jest.config.js` (if using Jest)
- Keep solutions simple; avoid over-engineering for prototypes.

## Scripts & Workflows (to add when `package.json` exists)
- Example scripts to provision:
  - `dev`: start dev server or ts-node runner
  - `build`: compile TypeScript to `dist/`
  - `test`: run unit tests
  - `lint` / `format`: enforce style
- Until scripts exist, document any ad-hoc commands directly in PRs and update `CLAUDE.md`.

## Coding Conventions
- Small, focused functions; meaningful names; add comments only for non-obvious logic.
- Follow consistent patterns once established; update `CLAUDE.md` when you introduce new ones.
- Prefer dependency-light implementations suited to a sandbox.

## Test Conventions
- Place tests near source or in `tests/`.
- Use descriptive test names; target critical paths first.
- Keep test runners simple (e.g., Jest or Vitest); avoid complex harnesses unless justified.

## Git Practices
- Atomic commits with descriptive messages; conventional commits when convenient: `feat`, `fix`, `docs`, `refactor`, `test`.
- For foundational changes (bootstrapping tooling), include a brief rationale in the PR description.

## Architecture Guidance (current phase)
- Start minimal; add modules only as needed.
- Document decisions in `CLAUDE.md` as the architecture evolves.
- If you add a service boundary (e.g., `src/services/patientRepo.ts`), describe the data flow and usage example in the file header or associated `docs/` note.

## Integration & External Dependencies
- No external integrations are defined yet.
- If adding any (APIs, DBs, auth), include:
  - A thin client in `src/services/` with clear method contracts.
  - Mock strategy for tests.
  - Minimal config under `config/` and example env docs in `README.md`.

## Examples
- New utility: `src/utils/formatDate.ts` with a corresponding `src/utils/formatDate.test.ts`.
- New service: `src/services/patientRepo.ts` exposing `getPatientById(id: string)`; add tests and usage from a sample CLI or component.

## Agent Operating Principles
- Ask for clarification only when multiple options are equally valid.
- Prefer small, incremental PRs; update `CLAUDE.md` when introducing or changing patterns.
- Keep the repo runnable: when you add scripts/configs, include a short "Try it" section in `README.md`.

References: See `CLAUDE.md` for detailed guidance and TODOs (TypeScript setup, linting, testing framework, dev server).