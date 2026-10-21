# The documentation, and where each thing lives

If you are looking for something and this file does not name it, the file is in the wrong place.

## Start here

| File | What it is |
|---|---|
| [../README.md](../README.md) | How to begin. One page. |
| [get_started.md](get_started.md) | **Start here if you are new**: from zero to an editor with an AI chat, step by step |
| [journey_checklist.md](journey_checklist.md) | The whole journey, phase by phase, with who does what (the assistant / you) |
| [de10nano_reference.md](de10nano_reference.md) | **The board's facts**: pins, switches, the JTAG chain, voltages, part numbers, each with its source and how sure it is |
| [../templates/blinky/README.md](../templates/blinky/README.md) | The known-good starting design: what it does on the board, its files, its status |

## How we build

| File | What it is |
|---|---|
| [../CLAUDE.md](../CLAUDE.md) | The assistant's standing rules (its generated copies for other assistants: [copilot-instructions.md](../.github/copilot-instructions.md), [AGENTS.md](../AGENTS.md)) |
| [lessons_log.md](lessons_log.md) | **What's new**: every lesson added to this blueprint, by date, newest first |
| [backlog.md](backlog.md) | Your designs' backlog (filled in with the assistant) |
| [../projects/README.md](../projects/README.md) | Where your designs live: one folder each |

## Procedures (how to *do* things)

| File | When you need it |
|---|---|
| [install_tools](procedures/install_tools.md) | Python, Icarus Verilog and GTKWave, Quartus Prime Lite with the Cyclone V, the USB-Blaster II driver |
| [simulate](procedures/simulate.md) | Testbenches, `fpga.py sim`, reading a `PASS` or a `FAIL`, waveforms |
| [build_and_program](procedures/build_and_program.md) | Compile, read timing, the JTAG chain, program the FPGA at `@2`, what to look for on the board |
| [gotchas](procedures/gotchas.md) | 19 proven traps, numbered, each with how it is known |

## The playbooks (skills)

The assistant follows these; you can read them too. Each one lives in `.claude/skills/` and is mirrored to
`.github/skills/` for GitHub Copilot.

| Skill | What it covers |
|---|---|
| [build-my-fpga-project](../.claude/skills/build-my-fpga-project/SKILL.md) | The guided journey, from a fresh clone to your own design on the board; "Tell me what to do" starts it |
| [setup-my-computer](../.claude/skills/setup-my-computer/SKILL.md) | Installing and checking the tools, fixing "command not found" |
| [de10nano-board](../.claude/skills/de10nano-board/SKILL.md) | The board itself: ports, cables, switches, LEDs, pins, connecting things safely |
| [simulate-my-design](../.claude/skills/simulate-my-design/SKILL.md) | Writing a self-checking testbench and finding the bug when it fails |
| [quartus-build-and-program](../.claude/skills/quartus-build-and-program/SKILL.md) | Compiling, timing, programming, and "the board does nothing" |
| [fpga-mentor](../.claude/skills/fpga-mentor/SKILL.md) | Teaching the concepts as they come up, and reviewing every design |
| [publish-to-github](../.claude/skills/publish-to-github/SKILL.md) | Your own GitHub repository, pushing safely, sharing a bitstream |

## For the blueprint's maintainer

[blueprint_roadmap.md](blueprint_roadmap.md): what is verified, what is not, and what is not covered yet.

The tooling: [scripts/fpga.py](../scripts/fpga.py) (the whole flow), [scripts/sync_skills.py](../scripts/sync_skills.py)
(mirrors the skills, generates the instructions for other assistants, stamps the README's "Last updated"),
[scripts/check_updates.py](../scripts/check_updates.py) (pulls blueprint updates at the start of a session),
[scripts/check_staged_secrets.py](../scripts/check_staged_secrets.py) (the commit hook), [tests/](../tests/) and
[the CI workflow](../.github/workflows/ci.yml).
