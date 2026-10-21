#!/usr/bin/env node
// PreToolUse hook: make Claude Code ask the user before running ESP32 commands
// that can't be undone. Reads the tool call as JSON on stdin; prints a decision on stdout.
// Exit 0 with no output = no opinion (normal permission rules apply).

const RULES = [
  [/\bespefuse(\.py)?\b|\bburn[_-](efuse|key|block[_-]?data|bit)\b/i,
   "burns ESP32 eFuses. eFuses are one-time programmable: a wrong value can permanently brick the chip or lock features."],
  [/\b(flash[_-]encryption|secure[_-]boot|digest[_-]sbv2|sign[_-]data|generate[_-]flash[_-]encryption[_-]key)\b|espsecure/i,
   "touches flash encryption or secure boot. Enabling these burns eFuses and cannot be reversed."],
  [/\berase[_-](flash|region)\b|\berase-flash\b/i,
   "erases flash, including NVS (saved Wi-Fi credentials, calibration and pairing data)."],
];

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  let command = "";
  try {
    const data = JSON.parse(input || "{}");
    command = String((data.tool_input && data.tool_input.command) || "");
  } catch {
    process.exit(0); // never block on malformed input
  }
  const hit = RULES.find(([re]) => re.test(command));
  if (!hit) process.exit(0);
  const out = {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: `ws-esp32 safety check: this command ${hit[1]} Confirm only if you intend this.`,
    },
  };
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
});
