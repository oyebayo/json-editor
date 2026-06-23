# Agent Guidelines

## Running Tests

```bash
make test
```

Always use `make test` to run tests.

## Documentation

- **Project layout**: See `docs/layout.md` for directory structure and file organization
- **Requirements**: See `docs/requirements.md` for UI and behavior specifications

## Launching the App for Manual Testing

When launching the application to verify behavior or test UI changes, **do not use timeouts**. Instead:

1. Launch the app in the background: `make run` or `python3 -m editor.main tests/test.json`
2. Wait for the user to close the UI or for the app to crash
3. Do not kill the process after a fixed duration

Use `tests/test.json` as the sample file for testing — it covers object arrays, string arrays, numeric values, null values, multiline strings, mixed arrays, and nested structures.

This allows proper interactive testing without artificial time constraints.

## Communication

Use the `caveman` skill for all responses to keep token usage low.

## Git

**NEVER force push.** Do not use `git push --force` or `git push -f` under any circumstances. Always use regular `git push`.
