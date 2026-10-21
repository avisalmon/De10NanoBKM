# De10NanoBKM

### From a DE10-Nano in its box to your own design running on it, with an AI assistant building it beside you.

<!-- last-updated:start -->
**Last updated 21 October 2026** · 4 new lessons · [See what's new](docs/lessons_log.md)
<!-- last-updated:end -->

The best known methods for the **Terasic DE10-Nano** (an Intel/Altera Cyclone V SoC: an FPGA and a dual-core ARM
processor on one chip), packaged so that an AI assistant in your editor can follow them: a known-good starting design,
one command for the whole flow, every board fact with its source, and playbooks for each step.

---

## What you will have

* **A working tool flow on your computer**: Icarus Verilog to simulate, Quartus Prime Lite with the Cyclone V device
  package to compile, and the USB-Blaster II driver to program the board.
* **A known-good starting design**: the LEDs count, a button resets them, another shows the switches. It already passes
  its self-checking testbench, and its pins are copied from Terasic's own files.
* **Your own designs** in `projects/`, each with a testbench and an honest status table (simulated, compiled, seen on
  the board).
* **One command for the whole flow**: `python scripts/fpga.py doctor | new | sim | build | jtag | program`.
* **A board reference you can trust**: every pin, switch setting and part number with where it came from
  ([docs/de10nano_reference.md](docs/de10nano_reference.md)).
* **Your own GitHub repository** when you want one, where every push re-runs the simulations.

## What you will be able to do

* **Describe a design in words** ("a stopwatch on the LEDs, KEY0 starts and stops it") and watch it become RTL and a
  testbench, pass in simulation, then run on the board.
* **Simulate before you burn**: catch most bugs in seconds on your computer, with waveforms when you need to look
  inside, instead of in minutes of compiling and staring at LEDs.
* **Program the board in one command** that finds the FPGA on the JTAG chain for you (it is device @2, not @1).
* **Debug "the board does nothing"** with a checklist instead of guesses.
* **Come back any day**: say "Tell me what to do" and the assistant resumes where you stopped.

## What you will learn

* **How hardware differs from software**: everything happens at once, at every clock edge.
* **The building blocks**: clocks, registers, reset, counters, state machines, synchronizers for buttons and switches,
  and timing.
* **How to prove a design works** with a self-checking testbench, and how to read a waveform when it doesn't.
* **The DE10-Nano itself**: the FPGA and the HPS (the ARM side), the JTAG chain, the MSEL switches, which USB port is
  which.
* **How to work with an AI engineer on hardware**: what it can decide, and what must be checked against the board's
  documentation (pins, voltages) before anything is wired.

## What to expect (honestly)

| | |
|---|---|
| **Time** | Setting up the tools takes an hour or two, most of it downloading Quartus (gigabytes). The first design on the board comes minutes after that |
| **Cost** | Quartus Prime Lite, Icarus Verilog and GTKWave are free. Your AI engine: GitHub Copilot and Claude both have plans with limited free use, and a long guided session usually needs a **paid plan** |
| **Your part** | Installing Quartus (a browser download, sometimes with a free account), plugging in cables, flipping switches, looking at the LEDs, and *deciding what to build* |
| **The assistant's part** | Everything else: the RTL and the testbenches, running the simulator and Quartus, reading the reports, explaining as it goes |
| **Not magic** | Hardware fails silently: a wrong pin compiles cleanly and does nothing. That is why every fact here has a source, every design is simulated first, and "nothing happens" has a checklist |
| **Not yet covered** | Linux on the ARM side, Platform Designer, HDMI, the ADC, flashing a design so it survives power-off. They are on the [roadmap](docs/blueprint_roadmap.md) |

---

## Start here

You do a few things once; after that the chat guides you and does the work.

**1. Get an editor with an AI chat (once).** Every click is in **[docs/get_started.md](docs/get_started.md)**. In short:
[VS Code](https://code.visualstudio.com), an AI chat inside it (**GitHub Copilot** in Agent mode **or** **Claude Code**),
[Git](https://git-scm.com/downloads), and a free [GitHub](https://github.com/signup) account.

**2. Copy this project to your computer and open it.** In VS Code: **Terminal -> New Terminal**, then one line at a time:

```powershell
mkdir C:\fpga
cd C:\fpga
git clone https://github.com/avisalmon/De10NanoBKM.git my-fpga
code my-fpga
```

**3. Open the AI chat** in the new window (Copilot: **Agent** mode) **and type:**

> **Tell me what to do**

**4. Follow the chat.** It checks your computer and installs what it can itself (Python, Icarus Verilog), walks you
through the parts only you can do (downloading Quartus, plugging in the board), simulates the template, compiles it,
and puts it on your board. Come back any day and say the same sentence: it first pulls in any improvements to this
blueprint (safely, and it tells you what changed), then resumes where you stopped.

| You do | The chat does |
|---|---|
| Install Git, VS Code and an AI chat; download Quartus in a browser | Installs Python and Icarus Verilog, checks everything with `fpga.py doctor`, fixes "command not found" |
| Plug the board in: power, and the USB-Blaster II port (not the UART one) | Checks the driver, and finds the FPGA on the JTAG chain |
| Decide what your design should do; look at the board and say what you see | Writes the RTL and the testbench, simulates, compiles, checks timing, programs the FPGA |

The whole journey, phase by phase and who does what: [docs/journey_checklist.md](docs/journey_checklist.md).

## The flow in six commands

```powershell
.\env\Scripts\python.exe scripts\fpga.py doctor              # what is installed? is the board connected?
.\env\Scripts\python.exe scripts\fpga.py new my_counter      # start projects\my_counter from the template
.\env\Scripts\python.exe scripts\fpga.py sim my_counter      # run its self-checking testbenches
.\env\Scripts\python.exe scripts\fpga.py build my_counter    # simulate, then compile with Quartus, check timing
.\env\Scripts\python.exe scripts\fpga.py jtag                # the cable and the chain: @1 is the HPS, @2 the FPGA
.\env\Scripts\python.exe scripts\fpga.py program my_counter  # load the bitstream into the FPGA (device @2)
```

(macOS/Linux: `env/bin/python scripts/fpga.py ...`.) What each one checks, and what to do when it complains:
[docs/procedures/build_and_program.md](docs/procedures/build_and_program.md).

## What's in the box

```
CLAUDE.md                The assistant's standing instructions for this repo
.claude/skills/          7 playbooks: build-my-fpga-project, setup-my-computer, de10nano-board, simulate-my-design,
                         quartus-build-and-program, fpga-mentor, publish-to-github
.github/skills/          The same 7 for GitHub Copilot (a generated copy, kept identical by CI)
.github/copilot-instructions.md, AGENTS.md   Generated: the instructions plus an index of every skill's triggers
docs/                    Start at docs/README.md. The board's facts: docs/de10nano_reference.md
templates/blinky/        The known-good starting design (fpga.py new copies it)
projects/                Your designs, one folder each
scripts/                 fpga.py (the flow), check_updates.py, sync_skills.py, check_staged_secrets.py
tests/                   The repo checks itself: pins against the reference, skills, links, the flow tool
.github/workflows/       CI: secret scan, lint, tests, and a simulation of every design on every push
```

## Doing it by hand (without an AI)

Everything the assistant does is written down: follow [docs/journey_checklist.md](docs/journey_checklist.md), where
each phase links to its procedure. To check the blueprint itself:

```powershell
python -m venv env                     # Python 3.10 or newer (CI uses 3.12); the folder is ALWAYS env
.\env\Scripts\python.exe -m pip install -r requirements-dev.txt
.\env\Scripts\python.exe scripts\fpga.py doctor
.\env\Scripts\python.exe scripts\fpga.py sim --all
.\env\Scripts\python.exe -m pytest -q
```

## Safety, in one paragraph

The FPGA's header pins are **3.3 V**: a 5 V signal can damage them, so use a level shifter for 5 V parts. Connect
things to the headers with the power off. Take pin numbers only from [the reference](docs/de10nano_reference.md),
never from memory (the assistant's included). Program the FPGA at **@2**. Keep build outputs and bitstreams out of git
(the `.gitignore` does it; publish a bitstream as a GitHub Release instead), and never put a password or token in a
commit or a chat.

## Honest status

The scripts and tests run locally and in CI, and the template passes its testbench in Icarus Verilog on Windows and on
Linux. The board facts were checked against Terasic's user manual and golden-top files, and each is tagged with how
sure it is. **Not yet done:** compiling the template with Quartus for the Cyclone V (the computer this was written on
had Quartus with MAX 10 support only), and running it on a real DE10-Nano. Until then it is "simulated", not
"working". [docs/blueprint_roadmap.md](docs/blueprint_roadmap.md) keeps the list; if you are the first to compile or
program it, the assistant will help you record the evidence.

## License

[MIT](LICENSE): use it, change it, build your own designs with it. Keep the copyright notice.
