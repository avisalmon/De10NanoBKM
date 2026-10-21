# Instructions for Claude working in this repo

This repo is a **blueprint for FPGA work on the Terasic DE10-Nano** (a Cyclone V SoC: an FPGA and a dual-core ARM
processor on one chip): a known-good starting design, one command for the whole flow (simulate with Icarus Verilog,
compile and program with Quartus Prime Lite), the board's facts with their sources, and the methodology. The person
you are helping is the **owner** of the board and may be new to FPGAs, to the command line, or to both.

## First thing: which situation are you in?

* The owner says anything like **"Tell me what to do"**, "what's next", "continue", "help me build my FPGA project",
  "make the LEDs blink", "get started" (or this is clearly a fresh clone of the blueprint) -> **invoke the
  `build-my-fpga-project` skill** and follow it. It orients from [docs/journey_checklist.md](docs/journey_checklist.md)
  (fresh start, or resume where the last session stopped), guides the whole journey, runs everything it can, and gives
  exact instructions only for what a human must do (plug in a cable, flip a switch, look at the LEDs). The human-only
  setup that comes before this chat is in [docs/get_started.md](docs/get_started.md).
* Something is not installed, "command not found", Quartus does not list the Cyclone V, the computer does not see the
  board -> `setup-my-computer` skill.
* Anything about the board itself (pins, switches, LEDs, which USB port, the JTAG chain, connecting something to a
  header) -> `de10nano-board` skill. The facts are in [docs/de10nano_reference.md](docs/de10nano_reference.md).
* Writing or running a testbench, reading a waveform, a FAIL -> `simulate-my-design` skill.
* Compiling, timing, programming the board, "the board does nothing" -> `quartus-build-and-program` skill.
* The owner asks to *understand* something, wants design advice, or asks "did I do it right?" -> `fpga-mentor` skill.
  **Teach as you build** (rule 9).
* Creating the GitHub repo, `gh` login, pushing, sharing a bitstream -> `publish-to-github` skill (asks before anything
  irreversible or public).
* "Add this to the methodology", "remember this" -> add it to [docs/procedures/gotchas.md](docs/procedures/gotchas.md)
  (or the procedure it belongs to) and [docs/lessons_log.md](docs/lessons_log.md), and confirm what you wrote.

The map of all documentation is [docs/README.md](docs/README.md).

## Standing rules (apply to everything)

0. **Start every session by checking GitHub for updates, and pull them in when it is safe.** Before anything else, run
   `python scripts/check_updates.py` (with the env's Python once it exists). It fetches the **blueprint** (the remote
   `origin` right after cloning, `blueprint` once the owner has their own repository) and the owner's **own**
   repository, and pulls only when the folder has no unsaved changes and the update applies cleanly; a conflict is
   undone and reported, never left half-done; it never pushes. Then tell the owner in one or two plain sentences what
   arrived ("the install guide got clearer; nothing you need to do"), and act on what the script says: **re-read
   `CLAUDE.md` and your skills if they changed**, reinstall the dev requirements if they changed, and run
   `python scripts/fpga.py sim --all` if a design or a script changed. Unsaved changes? Commit them first (with a clear
   message), then run it again. Conflicts? Resolve them with the owner: keep their designs, take the update's fixes.
   No Python yet (very first session)? Do the same with git directly: `git fetch --all`, then `git pull --ff-only` if
   `git status` is clean. Offline? Say so and carry on.
1. **The virtualenv is the folder `env/`**, always: not `.env`, not `venv`/`.venv`. Run Python through it: Windows
   `.\env\Scripts\python.exe`; macOS/Linux `env/bin/python`. Shell state does not persist between commands, so call the
   interpreter explicitly in every command. Quartus and Icarus Verilog are programs, not Python packages:
   [docs/procedures/install_tools.md](docs/procedures/install_tools.md).
2. **`git push` publishes the owner's work** (to everyone, if the repository is public). Commit freely; **push only when
   the owner says** push / publish / share. Never `git add -A` without reading `git status --short` first: build outputs
   (`db/`, `output_files/`, `*.sof`) and `env/` must never appear.
3. **Never invent a hardware fact.** Pin numbers, I/O standards, voltages, switch settings, part numbers and JTAG
   positions come from [docs/de10nano_reference.md](docs/de10nano_reference.md), where each one has its source. A fact
   that is not there: find it in Terasic's user manual or golden-top `.qsf`, add it to the reference with its source
   and tag, then use it. Cannot find it? Say so; never guess. A wrong pin compiles without a single error and then does
   nothing, or fights another driver.
4. **Simulate before you burn.** Every design has a self-checking testbench in `sim/` that prints `PASS` and never
   `FAIL`, and `python scripts/fpga.py sim <project>` passes before anything is compiled (`fpga.py build` refuses
   otherwise). A testbench that prints nothing has not passed. The project's `.qsf` is the one list of design files:
   the simulator compiles exactly the files Quartus does, so a new file goes into the `.qsf` first.
5. **The FPGA is device @2 on the JTAG chain** (@1 is the HPS, the ARM side). `python scripts/fpga.py program <project>`
   reads the chain and finds it; by hand it is `quartus_pgm -m jtag -c "DE-SoC [USB-1]" -o "p;output_files/<name>.sof@2"`.
   The DE10-Lite habit of `@1` is wrong on this board. A `.sof` lives only in the FPGA's memory: it is gone at power-off.
6. **Protect the board.** The FPGA's header pins are **3.3 V**: never connect a 5 V signal to them without a level
   shifter. Connect and disconnect things on the headers with the power off. Every port of the top-level design has a
   pin in the `.qsf`, and no pin has two drivers. Before the owner wires anything, say which pins, which direction and
   which voltage, and wait for their OK.
7. **Check before you commit.** The blueprint's own tooling is in `requirements-dev.txt`. Before a commit run
   `pytest -q`, `ruff check .`, `python scripts/fpga.py sim --all` and `python scripts/sync_skills.py --check`; CI runs
   the same on every push.
8. **Tell the truth about status**: say what exists, not what you intend. Each project's README has three rows
   (simulated, compiled, on the board): tick one only when it was done and seen, and say how. Say plainly when
   something is unverified: [docs/blueprint_roadmap.md](docs/blueprint_roadmap.md) lists what this blueprint has not
   yet checked on a real board.
9. **Mentor, don't just build.** The owner may be new to this. At each decision say *why* in a sentence, introduce a
   concept when it first matters (clock, register, reset, synchronizer, timing), and review each design with the
   `fpga-mentor` checklist (at most three ranked suggestions). Before a design goes on the board, ask the owner to
   explain what it should do; that is how both of you know what to look for.
10. **Everything this repo knows how to do is a skill.** Skills live in `.claude/skills/` (Claude Code) and are
    mirrored to `.github/skills/` (GitHub Copilot) by `python scripts/sync_skills.py`; `.github/copilot-instructions.md`
    and `AGENTS.md` are generated too. Edit only `.claude/skills/` and `CLAUDE.md`, then run the sync (CI and a test
    fail if the copies drift). New knowledge becomes a new or updated skill, with the detail in `docs/`. When something
    goes wrong, the owner corrects you, or you find a better way: do a short post-mortem (what happened, why the way we
    work let it, the rule that prevents it) and land it in [docs/procedures/gotchas.md](docs/procedures/gotchas.md), the
    skill that covers it, and [docs/lessons_log.md](docs/lessons_log.md).

## Layout in one glance

`templates/blinky/` the known-good starting design (`fpga.py new` copies it) · `projects/` the owner's designs, one
folder each · `scripts/` (`fpga.py` the whole flow, `check_updates.py`, `sync_skills.py`, `check_staged_secrets.py`) ·
`docs/` (the board reference, the journey checklist, procedures, lessons) · `tests/` (the repo checks itself) ·
`.github/workflows/` (CI simulates every design on every push) · `.claude/skills/` (your playbooks).
