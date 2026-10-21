# Security

Report vulnerabilities through GitHub's **private vulnerability reporting** (Security tab > Report a vulnerability). Please don't open a public issue.

In scope:
- Scripts in `skills/waveshare-esp32/scripts/` doing something unexpected (writing outside the output folder, running commands other than tool version checks).
- Skill instructions that could lead an agent to take destructive actions (erasing flash, burning eFuses) without asking the user.

Out of scope: bugs in ESP-IDF, Arduino-ESP32, PlatformIO or Waveshare's demo code. Report those upstream.
