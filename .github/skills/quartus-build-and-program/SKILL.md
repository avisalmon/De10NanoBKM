---
name: quartus-build-and-program
description: >
  Compile a DE10-Nano project with Quartus Prime (python scripts/fpga.py build), read what it reports
  (errors, critical warnings, the resources used, timing and the worst slack) and fix what failed; then
  load the .sof into the FPGA through the built-in USB-Blaster II (python scripts/fpga.py program, device
  @2, or by hand in the Quartus Programmer, following the manual), and find out why when programming fails
  or the board does nothing. Also why a design is gone after power-off.
  TRIGGER: "build", "compile", "synthesize", "Quartus", "fpga.py build", "timing failed", "worst slack",
  "slack", "Critical Warning", "Error (", "undefined entity", "program the board", "burn it", "load it",
  "download to the board", "fpga.py program", "quartus_pgm", "Programmer", "Auto Detect", "Hardware Setup",
  "No JTAG hardware available", "cable not found", "jtagconfig", "@2", ".sof", "nothing happens",
  "LEDs don't light", "gone after power off".
---

# Build, then program

The order never changes: **simulation passes** ([simulate-my-design](../simulate-my-design/SKILL.md)) > **build**
(compile, timing met) > **program** > **look at the board** > tick the project README's rows, each with its evidence.

## Build

```powershell
.\env\Scripts\python.exe scripts\fpga.py build my_counter
```

`fpga.py build`:

1. **Simulates first.** A failing testbench stops the build. `--skip-sim` exists; if it is used, the project README
   says why.
2. **Finds a Quartus that can compile for the Cyclone V**: the newest install whose device list includes it. None:
   "no Quartus Prime install that can compile for Cyclone V". Quartus Lite installs device families separately, and
   the Cyclone V package is missing: [setup-my-computer](../setup-my-computer/SKILL.md).
3. **Compiles** with `quartus_sh --flow compile <name>` in the project folder. That takes minutes, not seconds.
   It shows only the `Error` and `Critical Warning` lines, any pin line that names no port, and each step's result.
   Everything Quartus printed is saved in `output_files/build.log`.
4. **Reports** the ALMs, registers, pins and PLLs used, then the timing: `timing met: worst slack +X ns`, or
   `TIMING FAILED`, which stops it.
5. Prints `Bitstream: .../output_files/<name>.sof` and the command that programs it.

Tick "Compiled, timing met" in the project README with the worst slack as its evidence.

### When the compile fails

Read the **first** `Error` line first. It names a file and a line, and later errors often follow from it. These are
the wordings Quartus Prime 17.1 used, checked on small test designs:

| Quartus says | What it means | Fix |
|---|---|---|
| `Error (10170): Verilog HDL syntax error at top.sv(3) near text: ...` | A typo at or just before that line: often a missing `;` or `end` | Fix the line; simulate again |
| `Error (12006): Node instance "u_sub" instantiates undefined entity "sub"` | Quartus never saw module `sub`: its file is not in the `.qsf`, or the name is misspelt | Add a `SYSTEMVERILOG_FILE` line to the `.qsf` (the simulator reads the same list) |
| `Error (12007): Top-level design entity "x" is undefined` | `TOP_LEVEL_ENTITY` in the `.qsf` names a module that does not exist | Make it the top module's name (`de10nano_top` in the template) |
| `Error (10166): SystemVerilog RTL Coding error at ...: always_comb construct does not infer purely combinational logic` | An `always_comb` leaves an output without a value on some path, which makes a latch. Icarus accepts this silently, so it passed simulation | Give every output a value on every path: a default at the top of the block |
| `Error (10161): Verilog HDL error at ...: object "x" is not declared` | A name used but never declared: usually a typo | Fix the name; simulate again |
| `Critical Warning (169085): No exact pin location assignment(s) for N pins of M total pins` | **N ports have no pin**: Quartus put them on pins of its choice, which can be pins something else on the board drives | **Do not program this.** Give every port its pin ([de10nano-board](../de10nano-board/SKILL.md)) |
| `Warning (15706): Node "ledx[0]" is assigned to location or region, but does not exist in design` | A `.qsf` pin line names a signal the design does not have: the names differ (often case, or brackets) | Make the `.qsf` name and the port name identical. It usually comes with the 169085 warning above |
| `Critical Warning (332012): Synopsys Design Constraints File file not found` and `Timing requirements not met` | The `.sdc` is missing, or the `.qsf`'s `SDC_FILE` line names the wrong file. Without it Quartus checks a made-up clock | Keep the project's `.sdc` (the template's defines the 50 MHz clock) and its `SDC_FILE` line |

An error not in this table: quote it to the owner exactly, explain it, and add it here once it is solved.

### When timing fails

**Slack** is the time to spare, in nanoseconds, on the slowest path from one flip-flop to the next within one clock
cycle (20 ns at 50 MHz). Positive: every signal arrives in time. **Negative: some signal can arrive too late**, and
the board may work at room temperature and fail when warm, or fail at random. Never program a design that failed
timing as if it were fine.

1. Is the clock right? The `.sdc` needs a `create_clock` for every clock the design uses, with its real period:
   `-period 20.000` for the 50 MHz `FPGA_CLK1_50`.
2. Which path? `output_files/<name>.sta.rpt` has the summary per clock. The Timing Analyzer (Quartus's Tools menu;
   Quartus 17.1 calls it the TimeQuest Timing Analyzer) shows the failing paths: its *Report Top Failing Paths*
   task names the flip-flop each path starts from and ends at.
3. Shorten that path. Usual causes in a first design: a `/` or `%` by a number that is not a constant (a very long
   chain of logic), a long chain of `if`/`else` or additions in one cycle, or a clock made from logic. Split the
   work over two clock cycles (a register in the middle), and use one clock with an enable instead of a home-made
   clock (as `blinky.sv` does with its tick counter).
4. A new input or output pin: give it a line in the `.sdc` like the template's for `KEY`, `SW` and `LED`: a
   `set_false_path` for a person's button or an LED. A real interface (HDMI, the ADC) needs real constraints: look
   them up, do not guess.

## Program

```powershell
.\env\Scripts\python.exe scripts\fpga.py program my_counter
```

Before: the board has power (LED9 is on), and the USB cable is in the **USB-Blaster II** port
([de10nano-board](../de10nano-board/SKILL.md)). `fpga.py program`:

1. needs the `.sof` from a build ("Build first" otherwise), and warns when a source file changed after the build:
   the board would get the **old** design;
2. reads the JTAG chain (`jtagconfig`), picks the cable that has the FPGA on it, and shows the chain: `@1` the HPS,
   `@2` the FPGA, marked "program this one";
3. prints the exact command and runs it: `quartus_pgm -m jtag -c "<cable>" -o "p;output_files/<name>.sof@2"`;
4. ends with "Done. The design runs until the power goes off".

`--dry-run` prints the command without touching the board. `--cable` and `--index` choose by hand; `fpga.py jtag`
lists the cables and their chains.

**After programming, look:** LED10 (`CONF_DONE`) lights when the FPGA is configured. Then do what the owner said
the design should do (ask them before programming), and check that it does. Only then tick "Seen working on the
board" in the README, saying what was seen.

### By hand, in the Quartus Programmer

The manual's steps (p.13-17): open the Programmer (Quartus: **Tools > Programmer**; or the Programmer's own entry
in the Start menu) > **Hardware Setup** > choose **`DE-SoC [USB-1]`** > Close > **Auto Detect** > when it asks
which device, choose **`5CSEBA6`** > OK. Two devices appear, the HPS and the FPGA. Right-click the **FPGA** and open
the `.sof` > tick **Program/Configure** > **Start**.

## When programming fails, or the board does nothing

| What you see | Check |
|---|---|
| `No JTAG hardware available`, or `fpga.py`: "No JTAG cable found" | Power (LED9); the cable in the **USB-Blaster II** port, not the UART or OTG port; the driver ([install_tools.md](../../../docs/procedures/install_tools.md#4-the-usb-blaster-ii-driver); on Linux the udev rule in the same file) |
| The cable appears with no devices | The board is off, or try another cable and USB port |
| "no 5CSEBA6 on ...'s chain" | Not a DE10-Nano, or another blaster is plugged in: `fpga.py jtag` lists what is there. If the chain shows two devices without that name, the Quartus install may not know the Cyclone V by name; install its device package, or force the position with `--index 2` |
| "Programming FAILED" | Read the last lines `quartus_pgm` printed. An error that it *expected* one JTAG ID and *found* another means the wrong position: the FPGA is @2 |
| Programmed, **CONF_DONE off** | The FPGA is not configured: program again and read the output |
| Programmed, CONF_DONE on, the design does nothing | The design or its pins. Did it pass simulation? Did the build warn about pins (169085, 15706)? Is a button held (a pressed button reads 0)? Was the program warning about an old `.sof` ignored? |
| It worked, and after a power-off it is gone | Normal: a `.sof` lives only in the FPGA's memory. At power-on the FPGA loads whatever SW10 says (the microSD image or the flash) |

Keeping a design across power-off means writing it to the EPCS64 flash through the Serial Flash Loader (the manual's
chapter 8). This repo has not done that on a board yet: [docs/blueprint_roadmap.md](../../../docs/blueprint_roadmap.md).

Something new went wrong and was solved: add it to [docs/procedures/gotchas.md](../../../docs/procedures/gotchas.md)
and the [lessons log](../../../docs/lessons_log.md).
