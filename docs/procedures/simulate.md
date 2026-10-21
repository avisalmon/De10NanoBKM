# Simulate: check the design on the computer first

A simulation runs the design on the computer in a second, with every signal visible. On the board there are eight
LEDs to look at, and every try costs minutes of compiling. So every design has a **self-checking testbench**, and it
passes before anything is compiled: `fpga.py build` simulates first and refuses to compile when a testbench fails.

How to write a testbench (the rules and why), and how to find the bug when a check fails, are in the
[simulate-my-design](../../.claude/skills/simulate-my-design/SKILL.md) skill. This page is the procedure. Commands
are shown for Windows; on macOS and Linux use `env/bin/python` and `/`.

## The commands

```powershell
.\env\Scripts\python.exe scripts\fpga.py sim blinky            # one design, by its folder name
.\env\Scripts\python.exe scripts\fpga.py sim --all             # the template and every project
.\env\Scripts\python.exe scripts\fpga.py sim blinky --waves    # also save a waveform to look at
```
A design is named by its folder: `blinky` is the template in `templates/`, your own designs are in `projects/`. A
path to the folder works too. Icarus Verilog must be installed ([install_tools.md](install_tools.md), section 2).

What it printed for the template, with `--waves`, on Windows:
```text
templates/blinky:
  PASS  templates/blinky/sim/tb_blinky  (0.2 s)
  waveform: templates/blinky/sim_build/tb_blinky.vcd   (open it: gtkwave templates/blinky/sim_build/tb_blinky.vcd)
1 of 1 testbenches passed.
```
Compiler warnings are shown indented under their testbench's line: read them even under a `PASS`. A `FAIL` line is
followed by the last 25 lines the testbench printed, which name the check that failed.

## What it does

For every `sim/tb_*.sv` file of the design (then `sim/tb_*.v`):

1. reads the design files from the project's `.qsf`: its `SYSTEMVERILOG_FILE` and `VERILOG_FILE` lines, in order,
   which is exactly the list Quartus compiles;
2. compiles them with the testbench:
   `iverilog -g2012 -Wall -Wno-timescale -I rtl -o sim_build/tb_x.vvp -s tb_x <design files> sim/tb_x.sv`.
   `-s tb_x` makes the module named like the file the top of the simulation, so the module and the file must have
   the same name;
3. runs it inside the project's `sim_build/` folder: `vvp -n tb_x.vvp`, with `+waves` added by `--waves`.
   `sim_build/` is a build output: git ignores it.

## When it passes

A testbench passes only when all three are true:

* the simulator ends without an error;
* it printed a line **starting with `PASS`**;
* it printed nothing containing `FAIL`, and no line starting with `ERROR` or `FATAL`.

**A testbench that prints nothing has not passed.** One still running after 120 seconds has failed (it waits for
something that never happens: the template's has a second `initial` block that ends it with a `FAIL` first). A
design with no testbench fails too: `FAIL  no testbench`.

## The `.qsf` is the one list of design files

A new design file goes into the project's `.qsf` **first**, as a line like
`set_global_assignment -name SYSTEMVERILOG_FILE rtl/uart_tx.sv`, in the order the files should be read (a
`package` before the files that import it). The simulator and Quartus then read the same list, so the design you
simulated is the design you build: a file left out is missing from both, and the simulation says so at once.

Never list a testbench in the `.qsf`: Quartus would try to compile it.

## Waveforms

`--waves` hands `+waves` to the simulation, and a testbench that asks for it (the template's does, with
`$test$plusargs("waves")`) writes a `.vcd` file into `sim_build/`. `fpga.py` prints its path and the command that
opens it:

```powershell
gtkwave templates/blinky/sim_build/tb_blinky.vcd
```
On Windows, if `gtkwave` is not found, use its full path: `C:\iverilog\gtkwave\bin\gtkwave.exe` (the Icarus
installer puts it there). On macOS there is no Homebrew formula for GTKWave: see
[install_tools.md](install_tools.md), section 2.

In GTKWave: pick the testbench in the tree at the top left, select signals in the list below it, click **Append**,
then zoom to fit the whole run. Find the moment a `FAIL` line names (its time is in ns) and follow the signal back:
the output, the register that drives it, that register's inputs, until something is not what you expected.

## Before every commit, and in CI

`python scripts/fpga.py sim --all` is one of the checks before a commit (with `pytest -q`, `ruff check .` and
`python scripts/sync_skills.py --check`). GitHub runs the same on every push to `main` and every pull request, on
Ubuntu with Icarus Verilog from its package manager: [.github/workflows/ci.yml](../../.github/workflows/ci.yml).
A red CI on a design: run the same command on your computer and read the `FAIL` lines.

## What a PASS does not tell you

It checks the logic only as far as the testbench looks. It does not check the pins (a wrong pin in the `.qsf`
still simulates fine) or the timing (only Quartus does), and Quartus refuses some code Icarus accepts (a latch in an
`always_comb`: [gotchas.md](gotchas.md)). That is why the board step still exists:
[build_and_program.md](build_and_program.md).
