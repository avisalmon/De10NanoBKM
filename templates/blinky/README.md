# blinky: the template

The smallest complete DE10-Nano design, and the starting point of every project:
`python scripts/fpga.py new my_counter` copies this folder to `projects/my_counter/` and renames it.

## What it does on the board

| You do | You see |
|---|---|
| Nothing | `LED[7:0]` count up in binary, two steps a second (`LED[0]` blinks once a second) |
| Hold `KEY0` | The count goes back to 0 and stays there while you hold it |
| Hold `KEY1` | `LED[3:0]` show the four slide switches `SW[3:0]`; `LED[7:4]` are off |

Holding `KEY1` and flipping each switch checks every input and the low four LEDs in ten seconds.

## Files

| File | What it is |
|---|---|
| [rtl/blinky.sv](rtl/blinky.sv) | The counter, with the clock frequency as a parameter, so the testbench can run it fast |
| [rtl/de10nano_top.sv](rtl/de10nano_top.sv) | The top level: the board's signal names, input synchronisers, what the LEDs show |
| [sim/tb_blinky.sv](sim/tb_blinky.sv) | The self-checking testbench: 10 checks, prints `PASS` or `FAIL` |
| [blinky.qsf](blinky.qsf) | Device, design files (the one list both Quartus and the simulator use), pins |
| [blinky.sdc](blinky.sdc) | Timing: the 50 MHz clock, and the asynchronous inputs and LEDs |
| [blinky.qpf](blinky.qpf) | Names the Quartus revision |

## Status

| Step | State | Evidence |
|---|---|---|
| Simulated: `python scripts/fpga.py sim blinky` | **done** | `PASS: tb_blinky, 10 checks` with Icarus Verilog 12.0 on Windows and in CI (Ubuntu 24.04) |
| Compiled, timing met: `python scripts/fpga.py build blinky` | not yet | Needs Quartus Prime with the Cyclone V device support, which was not installed where this was written |
| Seen working on the board | not yet | |

The pins are copied from the Terasic golden-top `.qsf` ([docs/de10nano_reference.md](../../docs/de10nano_reference.md)),
so a first compile should only need the tools. Until someone compiles it and sees the LEDs count, it is
"simulated", not "working". If you are that someone, update this table with your evidence.
