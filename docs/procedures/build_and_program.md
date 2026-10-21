# Build and program: from a passing simulation to the board

The order never changes: **simulate, build, program, look.** Each is one command; this page says what each does,
what it prints, and what a person does in between. The error-by-error table, the timing method and the "nothing
happens" checklist are in the
[quartus-build-and-program](../../.claude/skills/quartus-build-and-program/SKILL.md) skill; the board's facts are in
[the reference](../de10nano_reference.md). Commands are shown for Windows; on Linux use `env/bin/python` and `/`.

## 1. Simulate

```powershell
.\env\Scripts\python.exe scripts\fpga.py sim blinky
```
Every testbench of the project prints `PASS`, or nothing else happens: [simulate.md](simulate.md). `build` runs the
testbenches again anyway.

## 2. Build

```powershell
.\env\Scripts\python.exe scripts\fpga.py build blinky
```
It needs Quartus with the Cyclone V ([install_tools.md](install_tools.md), section 3) and no board. In order, it:

1. **simulates** the project (`Simulating templates/blinky first: simulate before you burn.`) and stops if a
   testbench fails (`A testbench failed, so nothing was compiled.`);
2. **picks the newest Quartus that can compile for the Cyclone V** and says which
   (`Compiling with Quartus 17.1 (...). This takes a few minutes.`);
3. **compiles**: `quartus_sh --flow compile <revision>` in the project folder, which runs synthesis, the fitter
   (placing and routing), the assembler (the bitstream) and timing analysis. It shows only the `Error` and
   `Critical Warning` lines, any pin line that names no port, and each step's result; every line Quartus printed is
   saved in `output_files/build.log`;
4. **reports** the resources used (`Logic utilization (in ALMs)`, `Total registers`, `Total pins`, `Total PLLs`)
   and the **worst slack** of all the timing checks;
5. ends with `Bitstream: templates/blinky/output_files/blinky.sof` and the command that programs it.

| It prints | It means | Next |
|---|---|---|
| `timing met: worst slack +X.XXX ns (...)` | Every signal arrives within its clock cycle, with X ns to spare | Program it |
| `TIMING FAILED: worst slack -X.XXX ns (...)` | Some signal can arrive too late: the board may work today and fail when warm | The skill's timing method. Don't program it as if it were fine |
| `Compile FAILED. The full log: ...` | Quartus stopped on an error | Read the **first** `Error` line first; the skill's error table |
| `Critical Warning (169085): No exact pin location assignment(s) ...` | Some ports have no pin, and Quartus chose pins for them | **Don't program it.** Give every port its pin (the `de10nano-board` skill) |
| `timing: no timing summary found` | The timing report is not where expected | Look in `output_files/*.sta.rpt` |
| `no Quartus Prime install that can compile for Cyclone V was found` | No Quartus, or none with the Cyclone V package | [install_tools.md](install_tools.md), section 3 |

`--skip-sim` compiles without simulating. Use it only with a reason, written in the project's README, and never to
get past a failing testbench.

What a build leaves in the project folder: `db/`, `incremental_db/` and `output_files/` (the `.sof`, the reports
`*.rpt` and `*.summary`, and `build.log`). All of it is ignored by git: build outputs are never committed. To share
a bitstream, attach it to a GitHub Release ([publish-to-github](../../.claude/skills/publish-to-github/SKILL.md)).

Record the result in the project's README: tick "Compiled, timing met" with the worst slack as its evidence.

## 3. Connect the board (a person does this)

1. Nothing connected to the GPIO or Arduino headers that the design does not expect. The FPGA's pins are 3.3 V:
   wire things only with the power off ([de10nano-board](../../.claude/skills/de10nano-board/SKILL.md)).
2. The 5 V power adapter from the box into the board's power jack. LED9 (3.3 V power) lights.
3. The Mini-B USB cable from the box, from the computer to the board's **USB-Blaster II** port: not the other
   Mini-B port (the UART), and not the Micro-AB port (USB OTG).
4. On Windows, the first time: the driver ([install_tools.md](install_tools.md#4-the-usb-blaster-ii-driver)). On
   Linux: the udev rule, in the same section.

SW10 should not matter for programming over JTAG: it chooses what the FPGA loads by itself at power-on, and the
manual sets no SW10 condition for JTAG (an inference, tagged [community] in
[the reference](../de10nano_reference.md#sw10-the-msel-switches-what-the-fpga-does-at-power-on)).

## 4. See the chain

```powershell
.\env\Scripts\python.exe scripts\fpga.py jtag
```
On a DE10-Nano it should list one cable with two devices: the manual shows the two, and two community guides give
this order (this repo has not yet seen it on a board):
```text
1) DE-SoC [USB-1]
     @1  ...  SOCVHPS   <- the HPS (the ARM processors); not programmed with a .sof
     @2  ...  5CSEBA6...   <- the FPGA: program this one
```
`No JTAG cable found`: check, in this order, the power (LED9), the USB-Blaster II port, the driver, and another
cable or USB port.

## 5. Program

```powershell
.\env\Scripts\python.exe scripts\fpga.py program blinky
```
It reads the chain, finds the FPGA (normally `@2`), prints the exact command and runs it. For the template that is:
```text
quartus_pgm -m jtag -c "DE-SoC [USB-1]" -o "p;output_files/blinky.sof@2"
```
It takes seconds and ends with `Done. The design runs until the power goes off: a .sof only lives in the FPGA's
memory.`

| Option | What it does |
|---|---|
| `--dry-run` | Prints the command; sends nothing to the board |
| `--cable N` | Chooses the cable by its number or name (from `fpga.py jtag`), when there is more than one |
| `--index N` | Forces the device position. On a DE10-Nano the FPGA is `@2`; the DE10-Lite habit of `@1` is wrong here |

`warning: changed since the last build` means the board would get the **old** design: build again first.
`Programming FAILED`: read the last lines `quartus_pgm` printed, run `fpga.py jtag`, and see [gotchas.md](gotchas.md).

## 6. Look

1. **LED10 (`CONF_DONE`)** lights when the FPGA is configured.
2. Do what the project's README says the design does, and check that it does it. For the template
   ([its README](../../templates/blinky/README.md)): LED0 to LED7 count in binary and LED0 blinks once a second;
   holding KEY0 holds the count at 0; holding KEY1 shows the switches SW0 to SW3 on LED0 to LED3 (flip each one)
   while LED4 to LED7 go dark.
3. Only then tick "Seen working on the board" in the README, saying what was seen. Something is off, or nothing
   happens: the skill's "nothing happens" checklist.

## By hand, without `fpga.py`

From the project folder, with Quartus's `bin64` folder on PATH (or the tools called by their full path):
```powershell
quartus_sh --flow compile blinky
jtagconfig
quartus_pgm -m jtag -c "DE-SoC [USB-1]" -o "p;output_files/blinky.sof@2"
```
In the Quartus Programmer, the manual's steps (p.13-17): **Hardware Setup** > choose `DE-SoC [USB-1]` > Close >
**Auto Detect** > when it asks which device, choose `5CSEBA6` > OK. Two devices appear, the HPS and the FPGA.
Right-click the **FPGA** > open the `.sof` > tick **Program/Configure** > **Start**.

## After a power-off

The design is gone: a `.sof` lives only in the FPGA's memory, so program it again. At power-on the FPGA loads
whatever SW10 chooses (a new board: the image on the microSD card). Keeping a design across power-off means writing
it to the EPCS64 flash through the Serial Flash Loader (the manual's chapter 8); this repo has not done that yet
([roadmap](../blueprint_roadmap.md)).
