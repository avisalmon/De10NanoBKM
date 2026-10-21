# Installing the tools

What the DE10-Nano flow needs, how to install each tool on Windows, Linux and macOS, and how to check it. The
assistant does most of this itself (the [setup-my-computer](../../.claude/skills/setup-my-computer/SKILL.md) skill);
this page is the step-by-step reference behind it, with its sources, for the assistant and for anyone doing it by
hand. What comes before it (an editor with an AI chat, git, the project cloned) is in
[get_started.md](../get_started.md).

| Tool | What for | Needed by |
|---|---|---|
| Python 3.10 or newer (3.12 is the target; CI uses it) | `scripts/fpga.py`, the repo's tests | everything |
| Icarus Verilog (`iverilog`, `vvp`) | Simulating every design before it is compiled | `fpga.py sim` |
| GTKWave (optional) | Looking at waveforms | `fpga.py sim --waves` |
| Quartus Prime Lite **with the Cyclone V device package** | Compiling; `jtagconfig` and `quartus_pgm` for programming | `fpga.py build`, `jtag`, `program` |
| The USB-Blaster II driver (Windows) or a udev rule (Linux) | The computer talking to the board | `fpga.py jtag`, `program` |

**The order that wastes the least time:** start the Quartus download first (section 3: it is gigabytes). While it
downloads, install Python and Icarus (sections 1 and 2) and simulate the template, which needs neither Quartus nor
the board. Then install Quartus, and do the driver last, with the board plugged in (section 4). Section 5 checks
everything.

> **On a Mac:** Quartus has no macOS version. Sections 1 and 2 work on a Mac, so you can write and simulate every
> design there. To compile and program you need a Windows or Linux computer, or a Linux virtual machine with the
> board's USB passed through to it (the zangman guide in [Sources](#sources) uses Debian in VirtualBox; not tried
> here). Decide this before waiting for a download that will not run.

Keep downloads in an empty folder **outside the project**, for example `C:\fpga\downloads` (macOS and Linux:
`~/fpga/downloads`), so that nothing large or licensed ends up in git.

## 1. Python, and the project's environment `env/`

**Windows** (PowerShell):
```powershell
winget install --id Python.Python.3.12 -e --scope user --silent --accept-package-agreements --accept-source-agreements
py -3.12 --version
```
`--scope user` installs it for you alone, without an administrator prompt. `py -3.12` works at once; `python` works
in a new terminal. Without winget, or if it fails: download the installer from https://www.python.org/downloads/ and
tick **Add python.exe to PATH** on its first page. If typing `python` opens the Microsoft Store, use `py -3.12`, or
turn off the Python entries in Settings > Apps > Advanced app settings > App execution aliases.

**macOS:** install Homebrew (https://brew.sh), then `brew install python@3.12`.
**Debian or Ubuntu:** `sudo apt install python3 python3-venv python3-pip` (`python3 --version` must say 3.10 or
newer).

Then, in the project folder, the project's own environment. It is always the folder `env/`:
```powershell
py -3.12 -m venv env
.\env\Scripts\python.exe -m pip install -r requirements-dev.txt
.\env\Scripts\python.exe -m pre_commit install
```
macOS: `python3.12 -m venv env`; Linux: `python3 -m venv env`; then `env/bin/python -m pip install -r
requirements-dev.txt` and `env/bin/python -m pre_commit install`. The last line installs the commit check that
refuses secrets, licence files and bitstreams.

Call the env's Python by its path in every command, as above. Don't "activate" it: on Windows `Activate.ps1` is
often refused (`running scripts is disabled on this system`), and there is no need to change that policy.

## 2. Icarus Verilog, and GTKWave

**Windows:**
```powershell
winget install --id Icarus.Verilog -e --silent --accept-package-agreements --accept-source-agreements
```
The package downloads the Icarus Verilog 12 installer from https://bleyer.org/icarus/
(`iverilog-v12-20220611-x64_setup.exe`; winget checks it against SHA256
`a614057374dfaed5da0fe454cdeb410e54981fd85dbd28bd472f4ccb765deb84`). It installs to `C:\iverilog`, with GTKWave in
`C:\iverilog\gtkwave\bin` when that part is ticked, and it may ask "Do you want to allow this app to make changes?"
(the prompt can hide behind the editor: look in the taskbar). `fpga.py` finds both folders even before PATH does.

Without winget: open https://bleyer.org/icarus/ in a browser, download the same installer, check it with
`Get-FileHash <file>` (it prints the SHA256 above, in capitals), run it, and keep the GTKWave part ticked.

**A `403 Forbidden` is often the network, not the site.** On the company network this blueprint was written on, a
web filter blocked bleyer.org: winget stopped with `0x80190193 : Forbidden (403)`, and the page curl received began
"Blocked by ... categorized as ...". Read the page you got: a filter names itself. Then use another network, or ask
IT to allow the site. Another source with Icarus and GTKWave for Windows, macOS and Linux is **OSS CAD Suite**
(https://github.com/YosysHQ/oss-cad-suite-build, on GitHub's releases page; its README says how to put its `bin`
folder on PATH). It is not yet tried with this repo: if you use it, check with `fpga.py doctor` and tell the
blueprint.

**macOS:** `brew install icarus-verilog`. Homebrew's GTKWave package was deprecated in 2024 and disabled in 2025
(https://formulae.brew.sh/cask/gtkwave), so for waveforms use another `.vcd` viewer (OSS CAD Suite's macOS build
includes GTKWave, by its README), or skip them: the `PASS` and `FAIL` lines do not need a viewer.

**Debian or Ubuntu:** `sudo apt install iverilog gtkwave` (CI installs `iverilog` the same way).

**Check:** `fpga.py doctor` shows `[ ok ]` on the `iverilog` and `vvp` lines (this repo was checked with
`Icarus Verilog version 12.0 (devel)` on Windows), and then this prints a `PASS` line for `tb_blinky`:
```powershell
.\env\Scripts\python.exe scripts\fpga.py sim blinky
```

## 3. Quartus Prime Lite, with the Cyclone V

Quartus Prime Lite is the free edition of Altera's FPGA software (older guides and folder names say "Intel FPGA").
It installs **each device family as a separate package**, and an install compiles only for the families it has. The
DE10-Nano's FPGA is a **Cyclone V** (`5CSEBA6U23I7`), so the install needs the Cyclone V package. A Quartus put in
for a DE10-Lite usually has `MAX 10` only: the computer this repo was written on had exactly that. The facts and
their sources: [the reference](../de10nano_reference.md#quartus-prime-and-the-cyclone-v).

### 3a. Is there one already?

Run `fpga.py doctor`. It asks every Quartus it finds which families it can compile for, one line each, then says
which one it will use:
```text
  [ -- ] Quartus 17.1 at C:\intelFPGA_lite\17.1\quartus\bin64: MAX 10
  [MISS] Quartus with Cyclone V: none
         fix: install Quartus Prime Lite with the Cyclone V device package (docs/procedures/install_tools.md)
```
(That is the computer described above.) A line that lists `Cyclone V` means you are done here: go to section 4.
Only other families: 3b. No Quartus at all: 3c.

### 3b. Add the Cyclone V to a Quartus you already have

1. **Find its exact version.** `doctor` says `Quartus 17.1`; the full number is in the Start-menu folder name, for
   example *Intel FPGA 17.1.0.590 Lite Edition*.
2. **Download the Cyclone V device package of exactly that version** from Altera's website
   (https://www.altera.com), in a browser: the download page of Quartus Prime Lite for that version lists each
   device family as its own file. A free account may be needed, and the site refuses scripted downloads (HTTP 403),
   so this step is a human's. For 17.1 the file is **`cyclonev-17.1.0.590.qdz`**.
3. **Check the file** before using it:
   ```powershell
   Get-FileHash -Algorithm SHA1 C:\fpga\downloads\cyclonev-17.1.0.590.qdz
   ```
   It must print `392EEBBC61E041BE7ABD1034DE16323A414428E7` (PowerShell prints capitals; the reference has the same
   value in lower case). macOS: `shasum -a 1 <file>`; Linux: `sha1sum <file>`.
4. **Install it.** In Quartus: **Tools > Install Devices...**; or the **Device Installer** in the Start menu (for 17.1:
   *Intel FPGA 17.1.0.590 Lite Edition > Quartus Prime Lite Edition 17.1.0.590 > Device Installer (Quartus Prime
   17.1)*, which runs `C:\intelFPGA_lite\17.1\quartus\common\devinfo\dev_install\dev_install.exe`). Point it at the
   folder that holds the `.qdz`, select Cyclone V, and let it finish. The menu wording varies between versions, and
   this repo has not yet clicked through the wizard (see the [roadmap](../blueprint_roadmap.md)).
5. **Check:** `fpga.py doctor` now lists `Cyclone V` for that install.

### 3c. A fresh install

1. On Altera's website (https://www.altera.com), in a browser, open the download page of **Quartus Prime Lite
   Edition** for your system (Windows or Linux). The newest version is fine: every Lite version from 13.1 to 25.1 has
   a Cyclone V package (the reference lists them). A free account may be needed.
2. Download two things **into the same empty folder**: the Quartus Prime Lite installer, and the **Cyclone V device
   package** (`.qdz`) of the same version. Leave out the other device families and the simulator it offers
   (ModelSim or Questa): this repo simulates with Icarus.
3. Run the installer. It installs the device packages it finds in its own folder. If its last page offers to
   install the USB-Blaster II driver, accept.
   * **Windows:** `fpga.py` looks in `C:\intelFPGA_lite`, `C:\intelFPGA`, `C:\altera_lite` and `C:\altera`.
   * **Linux:** `chmod +x QuartusLiteSetup-<version>-linux.run`, then `./QuartusLiteSetup-<version>-linux.run`. It
     installs into your home folder by default (`~/intelFPGA_lite/17.1` for 17.1); `fpga.py` looks under `~/` and
     `/opt/` for the same folder names.
4. Check with `fpga.py doctor` (section 5).

### 3d. Quartus in an unusual folder

Tell `fpga.py` where it is with `QUARTUS_ROOTDIR`, the `quartus` folder that holds `bin64`:
```powershell
$env:QUARTUS_ROOTDIR = 'D:\tools\intelFPGA_lite\17.1\quartus'          # this terminal only
[Environment]::SetEnvironmentVariable('QUARTUS_ROOTDIR', 'D:\tools\intelFPGA_lite\17.1\quartus', 'User')   # new terminals
```
Linux: `export QUARTUS_ROOTDIR=~/tools/intelFPGA_lite/17.1/quartus` (add it to `~/.bashrc` to keep it).
`QUARTUS_BIN` (the `bin64` folder itself) works too. An old `QUARTUS_ROOTDIR` left behind by a Quartus that was
uninstalled does no harm: `fpga.py` skips any folder without `quartus_sh` in it.

## 4. The USB-Blaster II driver

The DE10-Nano has its programming cable built in: a **USB-Blaster II** behind one of its Mini-B USB ports. Use the
Mini-B cable from the box, in the **USB-Blaster II** port. The other Mini-B port is the HPS's serial console (UART)
and the Micro-AB port is USB OTG; neither programs the FPGA. How to tell them apart:
[de10nano-board](../../.claude/skills/de10nano-board/SKILL.md).

### Windows (once per computer)

The driver comes with Quartus, in `<Quartus folder>\drivers\usb-blaster-ii`.

1. Power the board with its 5 V adapter, and connect the USB cable from the computer to the board's
   **USB-Blaster II** port.
2. Open Device Manager (right-click the Start button > **Device Manager**). Under **Other devices**, find the
   **Unknown device** that appeared when you plugged in the cable (or a device with a yellow warning sign).
3. Right-click it > **Update driver** > **Browse my computer for drivers** (older Windows: "Browse my computer for
   driver software").
4. Choose the folder `<Quartus folder>\drivers\usb-blaster-ii`, for example
   `C:\intelFPGA_lite\17.1\quartus\drivers\usb-blaster-ii` (it holds `usbblasterii.inf`). **Not** the `usb-blaster`
   folder beside it: that one is for the older, separate cable. Keep **Include subfolders** ticked, then **Next**.
5. If Windows asks whether to install this device software: **Install**.
6. If another unknown device appears afterwards, do the same for it.
7. **Check:** `fpga.py jtag` lists a cable `DE-SoC [USB-1]` with two devices: `@1` the HPS (`SOCVHPS`) and `@2` the
   FPGA (`5CSEBA6...`).

The same drivers also come with the stand-alone Quartus Prime Programmer, for a computer that only programs boards.

### Linux

There is no driver to install; a udev rule lets a normal user use the cable (USB vendor `09fb`). As root, create
`/etc/udev/rules.d/51-altera-usb-blaster.rules` with these lines:
```text
SUBSYSTEM=="usb", ATTR{idVendor}=="09fb", ATTR{idProduct}=="6001", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="09fb", ATTR{idProduct}=="6002", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="09fb", ATTR{idProduct}=="6003", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="09fb", ATTR{idProduct}=="6010", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="09fb", ATTR{idProduct}=="6810", MODE="0666"
```
Then `sudo service udev restart`, and unplug and replug the cable (the Insper guide reboots instead). Check with
`fpga.py jtag`. The same guide, on Ubuntu 18.04 with Quartus 17.1, also needed these two lines; try them only if
`jtagconfig` still cannot see the cable:
```bash
sudo apt-get install libudev1:i386
sudo ln -sf /lib/x86_64-linux-gnu/libudev.so.1 /lib/x86_64-linux-gnu/libudev.so.0
```

## 5. Check everything

```powershell
.\env\Scripts\python.exe scripts\fpga.py doctor        # macOS/Linux: env/bin/python scripts/fpga.py doctor
```
`[ ok ]` found, `[MISS]` needed (with a `fix:` line under it), `[ -- ]` optional or for information. With the board
plugged in, a line says `Board: DE-SoC [USB-1], FPGA at @2`. Done when it ends with:
```text
Everything needed is installed.
```

## When something goes wrong

| Symptom | Cause and fix |
|---|---|
| `'python' is not recognized` right after installing | This terminal has the old PATH: open a new one, or use `py -3.12` |
| `python` opens the Microsoft Store | The App execution alias: use `py -3.12`, or turn the alias off (section 1) |
| `running scripts is disabled on this system` | Something tried to activate `env/`. Don't change the policy: call `.\env\Scripts\python.exe` directly |
| `pip` cannot install something | `env/` was made with the wrong Python: delete the folder and make it again with 3.12 |
| winget stops with `0x80190193 : Forbidden (403)`, or a page says "Blocked by ..." | A web filter on your network (section 2). Another network, IT, or another source |
| `iverilog` not found after installing | A new terminal; `fpga.py` itself also looks in `C:\iverilog\bin` |
| `doctor` finds a Quartus but says `Quartus with Cyclone V: none` | That install lacks the Cyclone V package: 3b |
| `doctor` says `could not ask it` for a Quartus | `quartus_sh` did not start: run `<Quartus folder>\bin64\quartus_sh --version` and read its error |
| The Device Installer finds nothing to install | The wrong folder, or a `.qdz` of another Quartus version (they must match) |
| `fpga.py jtag`: `No JTAG cable found` | In this order: the board's power (LED9 on); the USB-Blaster II port, not the UART one; the driver (section 4); another cable or USB port |
| The driver step finds nothing | The `usb-blaster` folder instead of `usb-blaster-ii`, or the board is not powered |
| Linux: no cable, or a permissions error | The udev rule (section 4), then replug |
| Errors about long paths, or files locked while Quartus writes them | Keep the project short and outside OneDrive, like `C:\fpga\my-fpga` |
| Antivirus quarantines a tool | Find out what and why; don't turn the antivirus off |

## Sources

* Python: https://www.python.org/downloads/ (winget id `Python.Python.3.12`). Homebrew: https://brew.sh
* Icarus Verilog for Windows: https://bleyer.org/icarus/ (winget id `Icarus.Verilog`, version 12.2022.06.11, its
  manifest names the installer URL and SHA256 above). Homebrew: https://formulae.brew.sh/formula/icarus-verilog.
  GTKWave's Homebrew status: https://formulae.brew.sh/cask/gtkwave
* OSS CAD Suite: https://github.com/YosysHQ/oss-cad-suite-build (its README lists `iverilog` and GTKWave)
* Quartus 17.1 with the Cyclone V package on Linux, and the udev rules:
  https://github.com/Insper/404/blob/master/elementos/Guia_Instalacao_Quartus17.01_CycloneV_ModelSim.md
* Cyclone V device packages for each Quartus version: https://github.com/raetro/sdk-docker-fpga (build.sh)
* Install Devices and the Device Installer: https://github.com/yuri-panchul/basics-graphics-music and
  https://github.com/robseb/NIOSII_EclipseCompProject
* The USB-Blaster II driver: an archived copy of Intel's instructions in https://github.com/brijesh4224/intel-website
  (`USB_Blaster_Driver_for_Windows_7_and_Windows_Vista2.html`); the full folder path in
  https://github.com/tttjjjzzz/OscilloscopeProject; the drivers in the Programmer-only install in
  https://github.com/drandyhaas/HaasoscopePro
* A Mac with a Linux virtual machine: https://github.com/zangman/de10-nano
* Checked on the computer this repo was written on (2026-10): the Start-menu entries and the `drivers` folder of
  Quartus Lite 17.1, its family list, the Icarus version, and the 403s (altera.com's own "Access Denied";
  bleyer.org's from the network's web filter)
