---
name: de10nano-board
description: >
  The Terasic DE10-Nano board itself, explained for an owner who is new to it: the FPGA and HPS (ARM)
  halves, which USB port and cable to use, power, the status LEDs (CONF_DONE), the user LEDs, buttons,
  switches and clocks, SW10 (MSEL) and what the board does at power-on, the JTAG chain (the FPGA is @2),
  adding a pin from Terasic's golden-top .qsf, and connecting things to the GPIO and Arduino headers
  safely at 3.3 V. Every fact comes from docs/de10nano_reference.md, never from memory.
  TRIGGER: "which USB port", "which cable", "what does SW10 do", "MSEL", "what pin is", "add a pin",
  "pin assignment", "LED pin", "button", "KEY0", "slide switch", "clock pin", "50 MHz", "GPIO header",
  "Arduino header", "connect a sensor", "5V", "level shifter", "HPS", "ARM side", "what is on the board",
  "which light", "CONF_DONE", "JTAG chain", "@1 or @2", "golden top", "the board does nothing".
---

# The DE10-Nano board

**Every fact here comes from [docs/de10nano_reference.md](../../../docs/de10nano_reference.md)**, where each one
has its source and a tag ([verified], [community], [unverified]). Answer from it. A fact that is not there: find it
in Terasic's user manual or golden-top `.qsf` (both linked in the reference's Sources), add it to the reference with
its source and tag, then answer. Cannot find it: say so. **Never type a pin number from memory**: a wrong pin
compiles without a single error and then does nothing, or fights something else on the board.

Say it to the owner in plain words; the reference has the detail.

## The board in five sentences

1. One chip, two halves: the **FPGA** (the owner's designs; everything in this repo) and the **HPS**, two ARM cores
   with 1 GB of memory that can run Linux (not covered yet: [roadmap](../../../docs/blueprint_roadmap.md)).
2. **Power** always comes from the 5 V adapter in the box; do not rely on USB to power the board.
3. **Three USB ports**: two look alike (Mini-B). One is the built-in **USB-Blaster II**, the one for programming;
   the other is the HPS's serial console (UART). The third (Micro-AB) is USB OTG for the HPS. The Mini-B cable in
   the box goes into the USB-Blaster II port.
4. A design sent over JTAG (a `.sof`) runs **until the power goes off**. Keeping one across power-off means
   writing it to the EPCS64 flash, which this repo does not cover yet.
5. **SW10** decides what the FPGA does at power-on. A new board loads its FPGA from the microSD card through the
   HPS (FPPx32); the other common setting loads it from the flash (AS). Programming over JTAG does not depend on it.

## What the owner sees and touches

| Thing | What it means | Pins |
|---|---|---|
| LED9 (power) | 3.3 V is on. Off: no power, check the adapter | Not for designs |
| **LED10 `CONF_DONE`** | **The FPGA is configured.** After `fpga.py program`, this is the first light to check | Not for designs |
| LED11, LED12 | JTAG traffic (they flicker while programming) | Not for designs |
| `LED[7:0]` | The design's 8 LEDs: **1 = on** | Reference, pin table |
| `KEY[1:0]` | Two push buttons: **0 while pressed**, already debounced on the board | Reference, pin table |
| `SW[3:0]` | Four slide switches: 0 when DOWN (towards the board's edge). **Not** debounced | Reference, pin table |
| `FPGA_CLK1_50` | The 50 MHz clock the template uses. `FPGA_CLK3_50` carries the same signal; `FPGA_CLK2_50` is the second one | Reference, pin table |
| `HPS_LED`, `HPS_KEY`, KEY3, KEY4 | The HPS's LED, button and reset buttons. **Not FPGA pins**: leave them alone | - |

A button or switch changes when a person touches it, not in step with the clock: the template passes each through
two flip-flops (a synchronizer) before using it. Debouncing is a different problem: the buttons are debounced on
the board, the switches are not.

## Adding a pin (a GPIO header pin, the ADC, HDMI...)

1. Find the signal in Terasic's golden-top `.qsf` (the link is in the reference's Sources). Signal names there are
   the board's names, for example `GPIO_0[0]`.
2. Copy its two lines **character for character** into the project's `.qsf`: the `set_location_assignment` and the
   `IO_STANDARD` line, exactly like the template's.
3. Add a port with **exactly that name** to the top level (`rtl/de10nano_top.sv`): `input wire` for an input,
   `output logic` for an output.
4. Add the signal as a row to the reference's pin table, with its source, the first time a design uses it.
5. `fpga.py build` prints any `Critical Warning` about a port without a pin: there must be none.

## Connecting something to the headers

Before the owner wires anything: say **which pins, which direction and which voltage**, and wait for their OK
(CLAUDE.md rule 6). Then:

* The header pins are **3.3 V**. Never connect a 5 V signal (a 5 V Arduino shield's outputs, a 5 V sensor) without
  a level shifter. The reference treats the pins as not 5 V tolerant until a datasheet says otherwise.
* **Power off** while connecting or disconnecting.
* **One driver per pin**: a pin something outside drives must be an `input` in the design.
* The 40-pin headers' supply pins give at most 1 A at 5 V and 1.5 A at 3.3 V: enough for a small sensor, not for a
  motor.
* The board's HDMI chip, ADC and accelerometer are there (the reference's table), but this repo has no tested
  design for them yet. The HDMI chip needs to be set up over I2C before it shows anything.

## SW10 and the JTAG chain

* **Leave SW10 as it is** for JTAG work. To change it: power off, then set it from the reference's SW10 table
  (copied row for row from the manual), and say which setting and why. On SW10, ON means 0.
* The JTAG chain has two devices: **@1 is the HPS, @2 is the FPGA**. `fpga.py program` and `fpga.py jtag` find the
  FPGA by name. By hand: `quartus_pgm -m jtag -c "DE-SoC [USB-1]" -o "p;output_files/blinky.sof@2"` (the cable's
  name comes from `fpga.py jtag`). The DE10-Lite habit of `@1` is wrong here.

## When the board does nothing

Go in this order, and tell the owner what each check means:

1. LED9 on? No: power.
2. `fpga.py jtag` shows `DE-SoC` with two devices? No: the USB-Blaster II port, then the driver
   ([setup-my-computer](../setup-my-computer/SKILL.md)).
3. After programming, is **CONF_DONE (LED10)** on? No: programming failed; read its output.
4. CONF_DONE on, but the design does nothing: the design or its pins. Did it pass simulation? Do its ports and pins
   match the reference? Is a button being held (0 while pressed)? Then
   [quartus-build-and-program](../quartus-build-and-program/SKILL.md) and
   [docs/procedures/gotchas.md](../../../docs/procedures/gotchas.md).

The first time something here is seen on a real board (the chain, CONF_DONE, a pin), write it in the reference and
the [lessons log](../../../docs/lessons_log.md): this repo's facts come from documents until then.
