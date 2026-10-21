# Instructions for AI agents

## Using the skill (any agent)

For Waveshare ESP32 firmware work, read `skills/waveshare-esp32/SKILL.md` first and follow its ground rules:

- Get pins from `skills/waveshare-esp32/data/boards/*.json` (or `python skills/waveshare-esp32/scripts/wsesp.py show <board>`), never from memory.
- Run `wsesp.py pins` before suggesting wiring.
- Ask before erasing flash, burning eFuses, or enabling flash encryption or secure boot.

## Working on this repository

- Python 3.9+, standard library only, in `skills/waveshare-esp32/scripts/`. Don't add runtime dependencies (pyserial stays optional).
- Run `python -m pytest` and `python skills/waveshare-esp32/scripts/wsesp.py validate-data` before committing.
- Every board pin needs a source URL in `verification.sources`. Unknown pins stay `null` and the profile stays `partial`. Never fill gaps from other boards.
- Keep `SKILL.md` short. Detailed material goes in `references/`.
- Keep the version in `.claude-plugin/plugin.json` and `scripts/wslib/__init__.py` in sync, and update `CHANGELOG.md`.
