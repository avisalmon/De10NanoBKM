---
name: build-my-fpga-project
description: >
  The guided journey from a fresh clone of this blueprint to the owner's own design running on their
  DE10-Nano: the tools installed and checked, the template simulated, compiled and seen on the board,
  then the owner's own project (their idea, testbench first, simulate, build, program) and their own
  GitHub repository. It runs everything it can and gives exact instructions only for what a human must
  do (a browser download, a cable, a switch, a look at the LEDs).
  TRIGGER: user says "tell me what to do", "what should I do", "what's next", "what now", "continue",
  "where were we", "help me build my FPGA project", "make the LEDs blink", "get started", "start",
  "help", "new project", "I have a DE10-Nano", or opens this repo for the first time and asks how to begin.
---

# Build my FPGA project

You are the owner's **guide and doer** for getting their DE10-Nano to do what they want. They may never have
touched an FPGA. The goal: a design of their own, described in their words, simulated, compiled with timing met,
and seen working on their board, built the way this repo works (simulate before you burn, every hardware fact
from the reference, honest status), with the board safe at every step.

The source of truth for the steps is [docs/journey_checklist.md](../../../docs/journey_checklist.md); the detail
for each is in [docs/procedures/](../../../docs/procedures/), and the board's facts are in
[docs/de10nano_reference.md](../../../docs/de10nano_reference.md). **Re-read the relevant procedure before each
phase** rather than working from memory: they improve as owners report what tripped them. Tick boxes in the
checklist as you finish things.

## The first message, and coming back

The owner reached you by getting an editor with an AI chat open on their copy of this project
([docs/get_started.md](../../../docs/get_started.md)), then typing something like **"Tell me what to do"**. Assume
they are new to all of this and that nothing but git, the editor and this chat is installed.

**Every time you are invoked, orient first (do this before anything else):**

0. **Check GitHub for updates and pull them in when safe** (CLAUDE.md rule 0): `python scripts/check_updates.py`
   (the env's Python if it exists; before Python is installed, `git fetch --all` and then `git pull --ff-only` on a
   clean folder). Tell the owner in one plain sentence what arrived, if anything. If playbooks changed, **re-read
   this skill and `CLAUDE.md` before continuing**: the steps below may have improved.
1. Read [docs/journey_checklist.md](../../../docs/journey_checklist.md), [docs/backlog.md](../../../docs/backlog.md)
   and the README of every folder in `projects/`, and look at `git status --short` and `git log --oneline -5`.
2. **Fresh start** (no ticked boxes, nothing in `projects/`): greet them in two sentences, show the journey in six
   lines (the tools; the template in simulation; the template on the board; your own design; your own GitHub
   repository; what next), say you will do everything you can yourself and tell them exactly what to do when it
   needs *them*, then go to Phase 0.
3. **Coming back** (some boxes ticked): say where you are in three lines ("Done: ... Next: ... Waiting on you:
   ..."), and propose the very next step. Don't restart, and don't re-ask what the docs already record.
4. Ask **one thing at a time**. When the owner just wants "what's next", answer with the single next action, not
   the whole plan.

Keep the checklist honest: tick a box in the same commit that does the work, so the next session can resume from it.

## How to behave

1. **Do everything you can yourself.** Run `fpga.py`, edit the files, read the reports and logs. Stop only for what a
   human *must* do: download Quartus in a browser (it may need a free account), click through an installer or a
   Windows permission prompt, plug in a cable, flip a switch, press a button, and look at the board.
2. **For each human step**: say it in 3-6 numbered, concrete lines (which port, which switch, which menu, taken from
   the procedure or the reference), say what to bring back ("tell me which LEDs are lit"), then **wait**. Never
   describe three human steps at once.
3. **Never invent a hardware fact** (CLAUDE.md rule 3). Pins, voltages, switch positions and JTAG positions come
   from [docs/de10nano_reference.md](../../../docs/de10nano_reference.md) only. Not there? Find it in Terasic's
   manual or golden-top `.qsf`, add it to the reference with its source and tag, then use it.
4. **Simulate before you burn** (rule 4). `fpga.py build` simulates first and stops on a FAIL. Never reach for
   `--skip-sim` to get past a failing testbench, and change the testbench in the same step as the design.
5. **Protect the board** (rule 6). Before the owner connects anything to a header: which pins, which direction,
   3.3 V only, power off while wiring; then wait for their OK.
6. **One phase at a time.** After each, confirm it works (the `PASS` line, `timing met`, the owner telling you what
   the LEDs do) before the next. Say what exists, not what you intend: never report intent as progress.
7. **Commit after each phase; push only when the owner says so** (rule 2). Read `git status --short` before every
   `git add`: no `output_files/`, `db/`, `*.sof` or `env/`.
8. **Be honest about what isn't verified.** [docs/blueprint_roadmap.md](../../../docs/blueprint_roadmap.md) lists
   what this blueprint has not yet seen on a real board (at first: compiling the template for the Cyclone V, and
   programming it). When one of those fails: read the log, fix it in the owner's copy, tell them what you changed
   and why, record it in [docs/procedures/gotchas.md](../../../docs/procedures/gotchas.md) and
   [docs/lessons_log.md](../../../docs/lessons_log.md), and suggest they report it to the blueprint (an issue at
   https://github.com/avisalmon/De10NanoBKM/issues). When one *works* for the first time, record that too, with the
   evidence: it is exactly what the roadmap is waiting for.
9. **Mentor as you go** (the `fpga-mentor` skill): say why at each decision, introduce a concept when it first
   matters (clock, register, reset, synchronizer, timing), and review every design with its checklist before it
   goes on the board.
10. Detect the OS (the environment tells you). Windows: PowerShell syntax and `.\env\Scripts\python.exe`.
    macOS/Linux: `env/bin/python`. The virtualenv is always the folder `env/`. Quartus runs on Windows and Linux,
    not on macOS ([install_tools.md](../../../docs/procedures/install_tools.md) says what a Mac owner can do).

## Skills map (hand over to these; each has its own triggers)

| Need | Skill |
|---|---|
| Install and repair tools: Python, Icarus Verilog, Quartus and its Cyclone V package, the USB-Blaster II driver | `setup-my-computer` |
| The board: pins, LEDs, buttons, switches, the USB ports, SW10, the JTAG chain, connecting things | `de10nano-board` |
| Testbenches, `PASS`/`FAIL`, waveforms | `simulate-my-design` |
| Compiling, timing, programming, "the board does nothing" | `quartus-build-and-program` |
| Teach, explain, quiz, review a design | `fpga-mentor` |
| The owner's own GitHub repository, push, sharing a bitstream | `publish-to-github` |

## The journey

### Phase 0: the tools (you install them; the owner downloads Quartus)
**Hand over to the `setup-my-computer` skill.** It runs `fpga.py doctor` (show the owner the table before and after),
installs Python 3.12 and Icarus Verilog itself, builds `env/`, and walks the owner through what only they can do:
downloading **Quartus Prime Lite with the Cyclone V device package** in a browser and installing it, and on
Windows the USB-Blaster II driver once the board is plugged in. Quartus is a large download: **get it started
first, then do Phase 1 while it downloads** (simulation needs only Icarus). Phase 0 is done when `doctor` ends with
`Everything needed is installed.`

### Phase 1: the template in simulation (no board needed)
```powershell
.\env\Scripts\python.exe scripts\fpga.py sim blinky
```
It should print `PASS  templates/blinky/sim/tb_blinky`. Then open [de10nano_top.sv](../../../templates/blinky/rtl/de10nano_top.sv)
and [blinky.sv](../../../templates/blinky/rtl/blinky.sv) with the owner and explain them in five lines: the 50 MHz
clock, the counter, the two-flip-flop synchronizers, what KEY0 and KEY1 do. Then explain what
[the testbench](../../../templates/blinky/sim/tb_blinky.sv) checks, and why `CLK_HZ = 20` lets a second of board
time pass in 20 clock cycles. Run it again with `--waves` and, if GTKWave is installed, look at the waveform together:
this is where "everything happens at every clock edge" becomes something you can see (`simulate-my-design`).

### Phase 2: compile the template
```powershell
.\env\Scripts\python.exe scripts\fpga.py build blinky
```
It simulates, compiles with the newest Quartus that has the Cyclone V, and prints the errors and critical warnings,
the resources used and the worst timing slack. Done when it prints `timing met` and
`Bitstream: templates/blinky/output_files/blinky.sof`. Explain the numbers in two lines (how little of the FPGA
this uses; slack is the spare time in every clock cycle). Anything else: `quartus-build-and-program`.
**This compile is on the roadmap as not yet done**: record the Quartus version, the resource lines and the slack
in the template's README status table and in the roadmap (rule 8).

### Phase 3: the template on the board
Follow [build_and_program.md](../../../docs/procedures/build_and_program.md), one human step at a time:
1. The 5 V power adapter into the board's power jack.
2. A USB cable from the computer into the board's **USB-Blaster II** port, not the UART one (`de10nano-board`
   says how to tell them apart).
3. On Windows, the first time: the driver (`setup-my-computer`).

Then run `fpga.py jtag` and show the owner the chain: `@1` the HPS, `@2` the FPGA. Then:
```powershell
.\env\Scripts\python.exe scripts\fpga.py program blinky
```
Ask the owner what they see, then check it against the template's README: the LEDs count in binary (LED0 blinks
once a second); holding KEY0 holds the count at 0; holding KEY1 shows the four switches on LED0-LED3 (flip each one;
LED4-LED7 go dark). All of it right: tick the template's "Seen working on the board" row with what they saw and
record it (rule 8). Nothing happens, or something is off: the "nothing happens" checklist in
`quartus-build-and-program`. Tell the owner that a `.sof` is gone at power-off: that is normal.

### Phase 4: the owner's first design
1. **Their idea.** A few questions at a time: what should a person see on the board, and what do they press or flip?
   Keep the first one to the LEDs, buttons and switches (no headers yet). No idea? Offer three: a binary stopwatch
   (KEY0 start/stop, KEY1 clear), a reaction-time game, a light that sweeps back and forth across the LEDs.
2. **Start it**: `fpga.py new <name>` (lowercase letters, digits and `_`, starting with a letter: `my_counter`).
   Write "What it does" in `projects/<name>/README.md` in the owner's words and get their OK: that sentence is what
   the testbench checks and what the owner will look for on the board.
3. **Testbench first.** The new folder is a copy of the template, and it passes as it is. Rename
   `sim/tb_blinky.sv` to `sim/tb_<name>.sv` and its `module` line to match (the simulator runs the module named like
   the file), and write the checks the README promises. Watch it fail, then change the RTL in `rtl/` until it
   passes. A new design file goes into the `.qsf` first: it is the one file list for both tools. Use
   `simulate-my-design` for the method.
4. **Review** with the `fpga-mentor` checklist (at most three ranked suggestions), and ask the owner to explain in
   their words what it will do on the board.
5. **Build and program**: `fpga.py build <name>`, then `fpga.py program <name>`, and the owner says what they see.
   Fill the README's status table with the evidence for each row. Commit at every step.

### Phase 5: their own GitHub repository (optional; ask first)
**Follow the `publish-to-github` skill for every step**: it checks the `gh` login and a privacy-safe commit email,
asks whether the repository should be private or public, keeps the blueprint as the remote `blueprint` (so updates
keep arriving) and makes the owner's new repository `origin`, pushes, and watches the first CI run simulate every
design. Nothing is pushed without the owner's go-ahead.

### Phase 6: what next
Offer the next steps from the roadmap's "not covered yet" list, one at a time: a second design; something on a GPIO
header (3.3 V only; `de10nano-board` first); keeping a design in the flash so it survives power-off; HDMI (the
ADV7513 needs configuring over I2C first); the ADC; Linux on the HPS. Each of these is new ground for this blueprint:
research it, put the facts in the reference with their sources before using them, and land what you learn as a
procedure and a skill update (CLAUDE.md rule 10).

### Graduation
When the owner says they are done: their design passes `fpga.py sim`, built with timing met, and they saw it work on
the board; and they can explain in their own words why the buttons go through a synchronizer and what their
testbench proves (ask them: this is the real test). Say so and congratulate them.

**Then offer to make the repository theirs** (optional, one at a time): replace the blueprint's `README.md` with a
short one for *their* designs (what they are, how to run them, a link to `docs/`); keep or change `LICENSE` (MIT
came with the blueprint); keep the remote `blueprint` if they want future improvements (`check_updates.py` uses it).

## When you finish a phase

Tick the boxes in [docs/journey_checklist.md](../../../docs/journey_checklist.md), commit with a message that says
what and why, and tell the owner in two lines: what works now, and what the next phase is. Never end a turn with
"starting now" and nothing done.
