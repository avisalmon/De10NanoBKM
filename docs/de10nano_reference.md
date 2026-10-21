# DE10-Nano reference: the facts, and where each one comes from

Pin numbers, switch settings and device names go wrong silently: a wrong pin compiles cleanly and the board
just does nothing (or fights another driver). So nothing on this page comes from memory. Each fact has a
**source** (see [Sources](#sources) at the end) and a tag:

* **[verified]**: stated in Terasic's own material (the user manual or the golden-top `.qsf`), or measured
  directly, and checked when this page was written.
* **[community]**: from community guides or scripts, or inferred from Terasic's material without being
  stated in it.
* **[unverified]**: written down because it matters, not yet confirmed. Confirm it before relying on it,
  then change the tag and add the source.

**Not yet seen on a real board by this repo.** Everything here comes from documents. The first time a fact
is confirmed on hardware (the JTAG chain, a pin, a switch), say so here and in the
[lessons log](lessons_log.md).

Page numbers ("manual p.12") are PDF page numbers of the Terasic user manual (2023-08-09 edition), which
run one higher than the number printed at the bottom of the page.

## The board in one table

| What | Fact | Tag, source |
|---|---|---|
| FPGA | Cyclone V SE SoC **`5CSEBA6U23I7`** (the `DEVICE` in every `.qsf`; the manual writes `5CSEBA6U23I7NDK`). Not `5CSEMA6U23I7`, which is a different part | [verified] manual p.7-9, golden-top `.qsf` |
| Logic | 110,000 logic elements, 5,570 Kbit of embedded memory, 6 fractional PLLs | [verified] manual p.9 |
| HPS (the ARM side) | Dual-core ARM Cortex-A9, 800 MHz, with **1 GB DDR3** on a 32-bit bus | [verified] manual p.7, 9, 37; `.qsf` |
| Configuration flash | **EPCS64** (the FPGA loads from it at power-on in AS mode) | [verified] manual p.7, 9 |
| Clocks for the FPGA | Three 50 MHz clock pins, `FPGA_CLK1_50`, `FPGA_CLK2_50`, `FPGA_CLK3_50`, from a clock generator. They carry **two** clock signals: the manual says `FPGA_CLK3_50` is "share with FPGA_CLK1_50" | [verified] manual p.21-22 (Table 3-5), `.qsf` |
| Clocks for the HPS | Two 25 MHz (`HPS_CLK1_25`, `HPS_CLK2_25`), used by the HPS only | [verified] manual p.21-22 |
| User I/O on the FPGA | 8 LEDs `LED[7:0]`, 2 push buttons `KEY[1:0]`, 4 slide switches `SW[3:0]`. A button reads **0 while pressed** and is debounced on the board (a Schmitt trigger); a switch reads 0 when DOWN (towards the board's edge) and is **not** debounced; an LED lights when its pin is driven 1 | [verified] manual p.23-25; `.qsf` |
| User I/O on the HPS | 1 LED `HPS_LED`, 1 button `HPS_KEY`, and two reset buttons for the HPS: KEY4 `HPS_RESET_N` (cold reset) and KEY3 `HPS_WARM_RST_N` (warm reset) | [verified] `.qsf` (LED, key); manual p.8, 19-20 (reset buttons) |
| Expansion | Two 40-pin GPIO headers (`GPIO_0[35:0]`, `GPIO_1[35:0]`, 36 signals each) and an Arduino Uno R3 header (`ARDUINO_IO[15:0]`, `ARDUINO_RESET_N`). The 40-pin headers also supply power: 5 V (at most 1 A, "depend on the power adapter") and 3.3 V (at most 1.5 A) | [verified] `.qsf`; manual p.27 (Table 3-9) |
| ADC | LTC2308: 12-bit, 8 channels, 500 ksps, on the FPGA side (`ADC_CONVST`, `ADC_SCK`, `ADC_SDI`, `ADC_SDO`). The Arduino header's six analog inputs (`ADC_IN0` to `ADC_IN5`) go to it; the board also has a 10-pin ADC header | [verified] manual p.9, 30; `.qsf` |
| HDMI output | ADV7513 transmitter on the FPGA side: 24-bit video `HDMI_TX_D[23:0]`, sync and clock, I2S audio, and an **I2C bus from the FPGA that controls the chip**. A design must set the chip up over I2C before it shows anything | [verified] manual p.32, `.qsf`; "set it up first" [community] |
| Accelerometer | ADXL345 on the HPS's I2C0, interrupt on `HPS_GSENSOR_INT` | [verified] manual p.41-42, `.qsf` |
| Ethernet | Gigabit, KSZ9031RN PHY, on the HPS (RGMII) | [verified] manual p.35, `.qsf` |
| microSD | Holds the HPS's boot loader and Linux | [verified] manual p.7, 9 |
| Programming | **USB-Blaster II built in**: a Mini-B USB port, **J13** | [verified] manual p.9 (port); J13 [community] |
| Serial console | A separate Mini-B USB port with an FT232R UART bridge, wired to the HPS | [verified] manual p.9, 36 |
| USB OTG | A third USB port, **Micro-AB**: USB 2.0 OTG for the HPS. Not for programming | [verified] manual p.8-9 |
| Board status LEDs | Not for designs; they show the board's state. **LED10 `CONF_DONE` lights when the FPGA is configured**; LED9 the 3.3 V power; LED11 and LED12 JTAG traffic; TXD and RXD UART traffic | [verified] manual p.18-19 (Table 3-3) |
| External JTAG header | J8, 2x5, **not fitted**: solder a 2.54 mm header to use an external blaster. Not needed with the built-in USB-Blaster II | [verified] manual p.13 |
| In the box | The board, a USB Type-A to Mini-B cable ("for FPGA programming or UART control"), a Type-A to Micro-B cable (OTG), a 5 V DC power adapter, a microSD card (already in its socket), four footstands | [verified] manual p.5 |
| Power | 5 V DC input, from the adapter in the box. Do not rely on the USB ports to power the board | [verified] manual p.5, 10; USB advice [community] |

## Pins for the FPGA's user I/O

Copied character for character from the Terasic golden-top `DE10_Nano_golden_top.qsf` (built with Quartus
16.0.2), which matches the manual's pin tables. [verified] `tests/test_board_facts.py` fails if the
template's `.qsf` ever disagrees with this table.

| Signal | Pin | I/O standard | What it is |
|---|---|---|---|
| `FPGA_CLK1_50` | `PIN_V11` | 3.3-V LVTTL | 50 MHz clock 1 (the one the template uses) |
| `FPGA_CLK2_50` | `PIN_Y13` | 3.3-V LVTTL | 50 MHz clock 2 |
| `FPGA_CLK3_50` | `PIN_E11` | 3.3-V LVTTL | 50 MHz clock 3 |
| `KEY[0]` | `PIN_AH17` | 3.3-V LVTTL | Push button KEY0, **0 while pressed** |
| `KEY[1]` | `PIN_AH16` | 3.3-V LVTTL | Push button KEY1, 0 while pressed |
| `LED[0]` | `PIN_W15` | 3.3-V LVTTL | LED0, 1 = on |
| `LED[1]` | `PIN_AA24` | 3.3-V LVTTL | LED1 |
| `LED[2]` | `PIN_V16` | 3.3-V LVTTL | LED2 |
| `LED[3]` | `PIN_V15` | 3.3-V LVTTL | LED3 |
| `LED[4]` | `PIN_AF26` | 3.3-V LVTTL | LED4 |
| `LED[5]` | `PIN_AE26` | 3.3-V LVTTL | LED5 |
| `LED[6]` | `PIN_Y16` | 3.3-V LVTTL | LED6 |
| `LED[7]` | `PIN_AA23` | 3.3-V LVTTL | LED7 |
| `SW[0]` | `PIN_Y24` | 3.3-V LVTTL | Slide switch SW0, 0 when DOWN (towards the board's edge) |
| `SW[1]` | `PIN_W24` | 3.3-V LVTTL | Slide switch SW1 |
| `SW[2]` | `PIN_W21` | 3.3-V LVTTL | Slide switch SW2 |
| `SW[3]` | `PIN_W20` | 3.3-V LVTTL | Slide switch SW3 |

**Everything else** (the GPIO headers, the Arduino header, HDMI, the ADC): copy the two lines per signal
(`set_location_assignment` and `IO_STANDARD`) from the golden-top `.qsf` linked in [Sources](#sources), and add
a row here with the source when a design first uses it. All of them are `3.3-V LVTTL` there. [verified]

**The `HPS_*` signals are not FPGA pins.** They belong to the ARM side; a design reaches them through the HPS
component in Platform Designer, which this repo does not cover yet ([roadmap](blueprint_roadmap.md)).
Their I/O standards differ too (the DDR3 pins are `SSTL-15 CLASS I`). [verified] `.qsf`

## Electrical rules that protect the board

* FPGA I/O on the headers is **3.3 V** (`3.3-V LVTTL`). Never connect a 5 V signal to it (a 5 V Arduino
  shield's outputs, for example) without a level shifter. [verified] for the I/O standard; "not 5 V tolerant"
  is the standing assumption of this repo until a datasheet line is cited here. [unverified]
* Wire or unwire anything on the headers with the **power off**.
* The 40-pin headers' supply pins give at most 1 A at 5 V ("depend on the power adapter specification") and
  1.5 A at 3.3 V. [verified] manual p.27 (Table 3-9)
* Never give a pin two drivers: if something outside drives a header pin, the design must leave that pin as
  an input.
* Every port of the top level needs a pin assignment. Quartus places a port without one wherever it likes,
  which can be a pin something else on the board drives; it says so in a `Critical Warning` that
  `fpga.py build` prints. `tests/test_board_facts.py` checks the template's ports.

## The JTAG chain: program the FPGA at @2

The built-in USB-Blaster II sees **two devices**. [verified] manual p.13; order [community], two guides agree.

| Position | Device | What it is |
|---|---|---|
| @1 | `SOCVHPS` | The HPS's debug port (the ARM side). A `.sof` cannot go here |
| **@2** | `5CSEBA6` | **The FPGA. Program this one** |

The Quartus Programmer calls the cable **`DE-SoC`**: the manual shows `DE-SoC [USB-1]`. [verified] manual
p.14. The number in the brackets can differ on your computer, which is why `fpga.py` reads the name from
`jtagconfig` instead of assuming it. From the command line:

```text
jtagconfig                                                   (lists the cable and the two devices)
quartus_pgm -m jtag -c "DE-SoC [USB-1]" -o "p;output_files/blinky.sof@2"
```

`python scripts/fpga.py program <project>` does this for you: it reads the chain, finds the `5CSEBA6`, and
sends the `.sof` to its position. The DE10-Lite habit of `@1` is wrong on this board. [community] zangman guide

The manual's own steps in the Programmer window: **Hardware Setup** > `DE-SoC [USB-1]` > Close > **Auto
Detect** > choose **`5CSEBA6`** when it asks which device > right-click the FPGA (the second device) and pick
the `.sof` > tick **Program/Configure** > **Start**. [verified] manual p.13-17

A `.sof` loaded over JTAG lives only in the FPGA's memory: it is gone at power-off. [verified] manual p.12-13
To keep a design, it goes into the EPCS64 instead, through the Serial Flash Loader (the manual's chapter 8);
this repo does not cover that yet ([roadmap](blueprint_roadmap.md)). [verified] manual p.13, 17

## SW10: the MSEL switches (what the FPGA does at power-on)

SW10 is a **6-pin** DIP switch: switches 1 to 5 set `MSEL[0]` to `MSEL[4]`, switch 6 is not used, and **ON
means 0**. `MSEL[4:0]` chooses how the FPGA configures **itself at power-on**. [verified] manual p.11-12,
Tables 3-1 and 3-2, copied here row for row:

| Mode | `MSEL[4:0]` | SW10 switches 1 to 5 | At power-on the FPGA... |
|---|---|---|---|
| AS (Active Serial) | `10010` | ON, OFF, ON, ON, OFF | loads itself from the EPCS64 flash, which comes "pre-programmed with the default code" |
| **FPPx32, the factory setting** | `01010` | ON, OFF, ON, OFF, ON | is loaded by the HPS: U-Boot loads it from an image on the microSD card |
| FPPx16 | `00000` | ON, ON, ON, ON, ON | is loaded by the HPS, the same way (16 bits wide, no compression) |

* **A new board is in FPPx32**: the manual's default. [verified] manual p.11-12
* The manual: *"If developers using the 'Linux LXDE Desktop' SD Card image, the MSEL[4:0] needs to be set to
  '01010' before the board is powered on."* A wrong SW10 for the SD-card image is the classic "the board won't
  boot". [verified] manual p.12
* **JTAG works whatever SW10 says**: MSEL only chooses the power-on source, and the manual describes JTAG as a
  separate programming method with no MSEL condition. [community] inferred from the manual's structure. Some
  guides set AS for FPGA-only work, so that the board starts from the known design in the flash.
* Set SW10 with the power off: the FPGA reads it when the board is powered on. [verified] manual p.12

## Quartus Prime and the Cyclone V

* **Quartus Prime Lite (free) supports the Cyclone V** as a separate **device package**: every Lite release
  checked has one (13.1, 17.0, 17.1, 18.1, 19.1, 20.1, 21.1, 22.1, 23.1, 24.1 and 25.1). [community] install
  scripts that download each version's package, and guides
* **A Quartus install only knows the families whose device packages were installed.** The computer this repo
  was written on had Quartus Prime Lite 17.1 with MAX 10 only (`quartus_sh --tcl_eval get_family_list`
  answered `{MAX 10}`). It cannot compile for the DE10-Nano until the Cyclone V package is added, and its
  programmer folder had no Cyclone V data either. `python scripts/fpga.py doctor` asks every install it finds.
  [verified] on that computer
* The Cyclone V package for 17.1 is **`cyclonev-17.1.0.590.qdz`**, SHA1
  `392eebbc61e041be7abd1034de16323a414428e7`, MD5 `747202966905f7917fb3b8f95228e026`. [verified] four
  independent copies agree. Its size: [unverified]
* Adding it to an existing install: Quartus **Tools > Install Devices...**, or the **Device Installer** in the
  Start menu, pointed at the folder holding the `.qdz`. [community] the exact menu wording varies by version.
  Step by step: [install_tools.md](procedures/install_tools.md)

## USB-Blaster II driver (Windows)

The driver ships inside Quartus: `<Quartus folder>\drivers\usb-blaster-ii` (for example
`C:\intelFPGA_lite\17.1\quartus\drivers\usb-blaster-ii`, which holds `usbblasterii.inf`). Install it from
Device Manager. [verified] an archived copy of Intel's instructions and two other guides, and the folder
exists in a 17.1 install. Steps: [install_tools.md](procedures/install_tools.md#4-the-usb-blaster-ii-driver)

Linux needs udev rules for USB vendor `09fb` instead of a driver. [community]

## Linux on the HPS (not covered by this repo yet)

* Terasic's SD-card images (Linux Console, LXDE Desktop, Xfce Desktop) are on the board's Resources page.
  [verified] fetched 2026-10
* Linux on the HPS can reload the FPGA at runtime with the kernel's `fpga_manager` and device-tree overlays.
  [community]
* Altera's boot loader and kernel moved from `github.com/altera-opensource` to
  **`github.com/altera-fpga`** (`u-boot-socfpga`, `linux-socfpga`); old links redirect. [verified] 2026-10
* Current community guides build with the Arm GNU Toolchain directly; the older SoC EDS no longer appears in
  them. When or whether SoC EDS was discontinued: [unverified]

## Places that are wrong, or will trip you

* **RocketBoards' DE10-Nano wiki page** gives the FPGA as `5CSEMA6U23I7N` and the flash as EPCS128. Terasic's
  manual and golden-top `.qsf` say `5CSEBA6U23I7` and EPCS64; trust Terasic. That wiki is read-only and says it
  will be deleted on 1 October 2027. [verified] 2026-10
* `software.intel.com` links in older guides are dead. Download sites for Quartus refuse scripted downloads
  (HTTP 403): download in a browser, sometimes signed in. [verified] 2026-10

## Sources

* Terasic DE10-Nano User Manual, 2023-08-09:
  https://www.terasic.com.tw/attachment/archive/1046/DE10-Nano_User_manual.pdf
* Terasic DE10-Nano Resources (manual, CD, SD-card images); the short link `http://de10-nano.terasic.com/cd`
  leads there: https://www.terasic.com.tw/cgi-bin/page/archive.pl?Language=English&CategoryNo=205&No=1046&PartNo=4
* Terasic golden-top `.qsf`, from the DE10-Nano System CD (mirror):
  https://raw.githubusercontent.com/Liangqiufenghong/Avalon-bus/master/IntelFPGA/Board/DE10_NANO/Demonstrations/FPGA/Golden_top/DE10_Nano_golden_top.qsf
  (the matching `.v` is next to it; a second mirror, `dsohnaka/PTSG-Core`, agrees)
* JTAG chain and `quartus_pgm ... @2`: https://github.com/zangman/de10-nano (docs/Setting-up-the-Development-Environment.md)
  and https://github.com/raetro/sdk-docker-fpga (docs/programmer-remote-jtag.md)
* Cyclone V device packages per Quartus version: https://github.com/raetro/sdk-docker-fpga (build.sh)
* Quartus 17.1 with the Cyclone V package, and the Linux udev rules:
  https://github.com/Insper/404/blob/master/elementos/Guia_Instalacao_Quartus17.01_CycloneV_ModelSim.md
* Altera's U-Boot and Linux: https://github.com/altera-fpga/u-boot-socfpga and https://github.com/altera-fpga/linux-socfpga
* RocketBoards (being retired): https://rocketboards.org/foswiki/Documentation/DE10NanoDevelopmentBoard
