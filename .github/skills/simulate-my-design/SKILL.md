---
name: simulate-my-design
description: >
  Simulate a DE10-Nano design on the computer before it goes near the board: write a self-checking
  testbench in the project's sim/ folder, run it with python scripts/fpga.py sim (Icarus Verilog), read
  PASS and FAIL lines, open the waveform in GTKWave with --waves, and find the bug when a check fails.
  The project's .qsf is the one list of design files, so the design simulated is the design built.
  Every design passes simulation before it is compiled.
  TRIGGER: "simulate", "simulation", "testbench", "test bench", "write a test", "tb_", "Icarus",
  "iverilog", "vvp", "waveform", "GTKWave", "vcd", "it FAILs", "PASS", "check my design",
  "does my design work", "fpga.py sim", "sim --all", "no testbench", "timed out", "sorry:".
---

# Simulate before you burn

A simulation runs the design on the computer in seconds, and every signal in it can be looked at. On the board
there are eight LEDs to look at, and each try costs minutes of compiling. So every design has a self-checking
testbench, and `python scripts/fpga.py sim <project>` passes **before** anything is compiled; `fpga.py build`
simulates first and refuses to compile when a testbench fails (CLAUDE.md rule 4).

Say it to the owner like this the first time: *a testbench is a second design that plays the person at the board.
It presses the buttons, watches the LEDs, and says PASS only if every LED was right at every moment it checked.*

## Run it

```powershell
.\env\Scripts\python.exe scripts\fpga.py sim my_counter          # one project
.\env\Scripts\python.exe scripts\fpga.py sim --all               # the template and every project
.\env\Scripts\python.exe scripts\fpga.py sim my_counter --waves  # also save a waveform (.vcd)
```

(macOS/Linux: `env/bin/python scripts/fpga.py ...`.) Icarus Verilog must be installed:
[setup-my-computer](../setup-my-computer/SKILL.md).

For each `sim/tb_*.sv` (or `.v`) file, `fpga.py sim`:

1. compiles it with `iverilog -g2012 -Wall -Wno-timescale -I rtl -s <file name>` together with **every design file
   the `.qsf` lists**, in the `.qsf`'s order;
2. runs it with `vvp -n` inside the project's `sim_build/` folder (a build output: never committed);
3. prints `PASS` or `FAIL` for it, the compiler's warnings, and on a failure the last 25 lines it printed.

**A testbench passes only when** the simulator exits cleanly, it printed a line **starting with `PASS`**, and it
printed nothing containing `FAIL` and no line starting with `ERROR` or `FATAL`. A testbench that prints nothing has
not passed. One that is still running after 120 s has failed.

## Write a testbench

Start from the template's, [templates/blinky/sim/tb_blinky.sv](../../../templates/blinky/sim/tb_blinky.sv) (every
new project gets a copy), and keep its shape:

| Rule | Why |
|---|---|
| The file is `sim/tb_<name>.sv` and **the module is named exactly like the file** (`module tb_<name>;`) | `-s <file name>` tells the simulator which module is the top |
| Never list a testbench in the `.qsf` | Quartus would try to compile it, and the simulator would see the module twice |
| A new **design** file goes into the `.qsf` first (a `SYSTEMVERILOG_FILE` line) | The simulator and Quartus read the same list; a file missing from it is missing from both |
| Drive the inputs the way the board does: buttons are **1 when not pressed, 0 while pressed** | A testbench that presses with 1 tests a different board |
| Check with `!==`, not `!=` | `!==` also fails on `x` (unknown) and `z`; `!=` lets an unknown value slip through |
| Each failed check prints one line starting with `FAIL:`: what, the value seen, the value expected, `$time` | That line is the whole bug report |
| At the end: `PASS: <name>, N checks` if there were no errors, otherwise a `FAIL:` line, then `$finish` | No PASS line, no pass |
| A second `initial` block that prints `FAIL: ... timed out` and calls `$finish` after a fixed time | A testbench that waits for something that never happens must fail, not hang |
| Make time short with parameters: the template simulates `CLK_HZ = 20`, not 50 000 000 | Same logic, 10 cycles per step instead of 25 million |
| `if ($test$plusargs("waves"))` around `$dumpfile` / `$dumpvars` | Waveforms only when asked for: `--waves` |
| Wait for the clock with `@(posedge clk)`, then `#1` before checking | Checks never race the edge that changes the outputs |

What to check: think like the owner at the board. Every button, every switch setting that matters, what happens
right after reset, and what happens after a long time (a counter that wraps, a state that is never left). One
testbench per module is fine: `tb_top.sv` for the whole design, `tb_uart_tx.sv` for one piece.

## When it fails

1. **"did not compile"**: Icarus names a file and a line. Read the first error first; later ones often follow from
   it. Icarus understands most of the SystemVerilog a design needs, not all of it. Concurrent assertions
   (`assert property ...`) are a syntax error in Icarus 12, and a line with `sorry:` means it supports something
   only partly (for `unique case` it says the `unique` is ignored). Write the plainer form; Quartus accepts both.
2. **A `FAIL:` line**: it says what was checked, the value seen, the value expected and when. Run again with
   `--waves`, open the file it names (`gtkwave <path>`; on Windows, if `gtkwave` is not found:
   `C:\iverilog\gtkwave\bin\gtkwave.exe <path>`), go to that time, and follow the signal back: the output, the
   register that drives it, that register's inputs, until something is not what the owner expected.
3. **"still running after 120 s"** or **"timed out"**: the testbench waits for something that never happens, or a
   parameter makes time far too long (`CLK_HZ` left at 50 000 000).
4. **"no testbench"**: the project has no `sim/tb_*.sv`. Write one; `fpga.py build --skip-sim` exists, but say why
   in the project's README if it is used.
5. **Warnings under a PASS line**: read them anyway. A width mismatch or an unconnected port in simulation is often
   the same bug on the board.

Then decide, and say: **is the design wrong, or the testbench?** Fix that one. Never delete or loosen a check just
to get a PASS. Change one thing at a time and run again.

`x` in the waveform means "unknown": usually a register that reset never set, or an input nothing drives. Design so
that reset puts a value into every register that matters.

## What a PASS does not mean

* It checks the logic, not the pins: a design that passes can still have a wrong pin in the `.qsf`
  ([de10nano-board](../de10nano-board/SKILL.md)).
* It does not check timing: only Quartus does ([quartus-build-and-program](../quartus-build-and-program/SKILL.md)).
* Quartus is stricter than Icarus about some code. Icarus 12 accepts an `always_comb` that makes a latch without a
  word; Quartus 17.1 refuses it (`Error (10166)`). The [fpga-mentor](../fpga-mentor/SKILL.md) checklist catches it
  before the build does.
* It checks only what the testbench checks. Ask the owner what they will look for on the board, and make sure the
  testbench checks that.

In the project's README, tick "Simulated" with the evidence: the PASS line, with its number of checks.

## Good to know

* `vvp` runs inside `sim_build/`, so a file the testbench or design opens by a relative path (a `$readmemh` file,
  the `$dumpfile`) is looked for there.
* `python scripts/fpga.py sim --all` is part of the checks before a commit and of CI: the template and every project
  must pass, every time.
