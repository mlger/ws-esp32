# Contributing

Thanks for helping. The most useful contributions are, in order:

1. **Hardware test reports.** Flash the starter project on your board and confirm the display, touch and LED work. Then raise the profile to `hardware-tested` and note the board revision.
2. **Filling in `partial` profiles** from the schematic or demo source.
3. **New board profiles.** Follow [add-board.md](skills/ws-esp32/references/workflows/add-board.md).
4. Fixes to workflows, templates and the CLI.

## Ground rules for board data

- Every pin must be traceable to a source URL (wiki/docs page, schematic PDF, or Waveshare demo code).
- Unknown means `null` and `partial`. Don't copy pins from a "similar" board.
- When Waveshare's own docs contradict each other, write that down in `warnings`.

## Workflow

```bash
git clone https://github.com/mlger/ws-esp32 && cd ws-esp32
python -m pip install pytest
python -m pytest
python skills/ws-esp32/scripts/wsesp.py validate-data
```

For template or profile changes, also build the generated project locally if you can:

```bash
python skills/ws-esp32/scripts/wsesp.py new <board> --framework idf --name t --out /tmp/t
cd /tmp/t && idf.py build
```

CI does the same for every board, using both ESP-IDF and Arduino.

## Pull requests

- One board or one topic per PR.
- Fill in the PR template checklist.
- Use clear commit messages, for example `boards: add esp32-s3-touch-lcd-2.8 (wiki)`.
- If the change affects users, add a line to `CHANGELOG.md` under "Unreleased".

## Code of conduct

This project follows the [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). Report problems to the maintainers through a private GitHub security advisory or by email.
