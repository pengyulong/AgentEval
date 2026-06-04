# Development Guidelines

## 1. Planning & Staging

Break complex work into 3–10 stages. Document in `IMPLEMENTATION_PLAN.md`:

```markdown
## Stage N: [Name]
**Goal**: [Specific deliverable]
**Success Criteria**: [Testable outcomes]
**Tests**: [Specific test cases]
**Status**: [Not Started | In Progress | Complete]
```

Update status as you progress. Remove the file when all stages are done.

## 2. Implementation Flow

1. Understand — study 3 similar features in the codebase, identify patterns and conventions.
2. Test — write the test first (red).
3. Implement — minimal code to make it pass (green).
4. Refactor — clean up with tests passing.
5. Commit — with a clear message linking to the plan.

## 3. Goal-Driven Execution

For multi-step tasks, state a brief plan before starting:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 4. Code Quality

Every commit must:

- Compile successfully.
- Pass all existing tests.
- Include tests for new functionality.
- Follow project formatting and linting rules.

Before committing:

- Run formatters and linters.
- Self-review changes.
- Ensure the commit message explains "why", not just "what".

## 5. Project Integration

### Learning the Codebase

- Find 3 similar features/components as reference.
- Identify common patterns and conventions.
- Use the same libraries and utilities when possible.
- Follow existing test patterns.

### Tooling

- Use the project's existing build system.
- Use the project's test framework.
- Use the project's formatter and linter settings.
- Don't introduce new tools without strong justification.
- Use context7 MCP for code generation, setup/configuration steps, and library/API documentation — resolve library IDs and fetch docs automatically without being asked.

### Python Environment

- Managed via Miniconda. Default environment name is `base`.
- Activate with `conda activate base` (or the project-specific env name).
- Always activate before running or installing packages.
- Dependencies managed via `requirements.txt` / `pyproject.toml`.

### Environment Variables

- `DEEPSEEK_API_KEY` — DeepSeek model API
- `DEEPSEEK_MODEL_NAME` — DeepSeek primary model (e.g. deepseek-v4-pro)
- `DEEPSEEK_FAST_MODEL_NAME` — DeepSeek fast/cheap model (e.g. deepseek-v4-flash)

Use whichever model or data source fits the task. For quick or low-stakes calls, prefer `DEEPSEEK_FAST_MODEL_NAME` to save cost. Always read credentials via `os.environ.get("VAR_NAME")`. Never hardcode keys or use placeholder strings.

## 6. Quality Gates

Definition of done:

- [ ] Tests written and passing.
- [ ] Code follows project conventions.
- [ ] No linter or formatter warnings.
- [ ] Commit messages are clear.
- [ ] Implementation matches the plan.
- [ ] No TODOs without issue numbers.

Test guidelines:

- Test behavior, not implementation.
- One assertion per test when possible.
- Clear test names describing the scenario.
- Use existing test utilities and helpers.
- Tests must be deterministic.
