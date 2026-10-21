---
name: setup-my-computer
description: >
  Get the owner's computer ready for the DE10-Nano flow: run fpga.py doctor, install Python 3.12 and
  Icarus Verilog (with GTKWave where it exists) without admin rights where possible, build the env/
  virtualenv, guide the Quartus Prime Lite install with the Cyclone V device package (or add the
  package to a Quartus that has only MAX 10), install the USB-Blaster II driver, and fix PATH and
  "command not found" problems on Windows, macOS and Linux.
  TRIGGER: "set up my computer", "install the tools", "what do I need to install", "prerequisites",
  "python not found", "iverilog not found", "command not found", "not recognized", "install quartus",
  "quartus doesn't list cyclone v", "device package", "install devices", "usb blaster driver",
  "unknown device", "the computer doesn't see the board", "no JTAG hardware", "doctor says MISS",
  "venv", "pip install fails".
---

# Set up my computer

The owner has an editor with an AI chat open on this project, and git; nothing else is guaranteed. Your job: find out
what is installed, **install what you can yourself**, guide the owner through the parts only they can do, and say in
plain words what you did. The step-by-step reference for every tool, with its sources, is
[docs/procedures/install_tools.md](../../../docs/procedures/install_tools.md); the human part that comes before this
chat is [docs/get_started.md](../../../docs/get_started.md). The journey continues in
[build-my-fpga-project](../build-my-fpga-project/SKILL.md).

## What is needed, and who installs it

| Tool | What for | Who |
|---|---|---|
| Python 3.10+ (3.12 is the target; CI uses it) | `fpga.py`, the tests | You |
| Icarus Verilog (`iverilog`, `vvp`) | Simulation: every design, before it is compiled | You (a Windows permission prompt may need the owner) |
| GTKWave (optional) | Looking at waveforms | You, with Icarus on Windows |
| Quartus Prime Lite **with the Cyclone V device package** | Compiling, and `quartus_pgm` / `jtagconfig` for programming | **The owner** downloads it in a browser; you guide |
| USB-Blaster II driver (Windows) | The computer talking to the board | The owner clicks through Device Manager; you guide |
| GitHub CLI `gh` (optional) | Publishing, later | `publish-to-github` |

## Principles

1. **Look before you install.** Run the checks, show the owner the table, then fix only what is missing or wrong.
2. **No admin rights where possible.** Prefer per-user installs. Say plainly before anything that may show a Windows
   "allow changes?" prompt; it can hide behind the editor (look in the taskbar).
3. **Time-box every install** (about 2 minutes; run it in the background and check on it). An installer waiting on a
   hidden permission window waits forever. Stuck: ask the owner to look for the prompt; still stuck, stop it and use
   the fallback.
4. **Verify what you download** against the publisher's checksum, into an empty scratch folder, never into the project.
5. **Change nothing you don't need to** (no global PATH edits, no uninstalls). Say what changed.
6. **A new terminal sees a new PATH; the current one may not.** Re-check with the full path, or open a new terminal.
   `fpga.py` also finds Icarus in `C:\iverilog\bin` and Quartus in its usual folders without PATH.
7. The virtualenv is the folder `env/`. Run Python through it explicitly.

## 1. Detect

Before Python exists, PowerShell (macOS/Linux in brackets):
```powershell
python --version; py -3.12 --version     # [python3 --version]
git --version
winget --version                          # [brew --version / apt --version]
```
Once Python works, `fpga.py doctor` checks everything else (Python, git, gh, Icarus, GTKWave, every Quartus install
and the device families it can compile for, and the board on JTAG):
```powershell
.\env\Scripts\python.exe scripts\fpga.py doctor     # [env/bin/python scripts/fpga.py doctor]
```
`[ ok ]` found, `[MISS]` needed (with a `fix:` line), `[ -- ]` optional or informational. It ends with
`Everything needed is installed.` or `Missing: ...`. Show the owner the table before and after.

## 2. Python

**Windows:** `winget install --id Python.Python.3.12 -e --scope user --silent --accept-package-agreements --accept-source-agreements`
(time-boxed). Verify with a new terminal or `py -3.12 --version`. Fallback: the owner downloads the installer from
https://www.python.org/downloads/ and ticks **"Add python.exe to PATH"**. If `python` opens the Microsoft Store, use
`py -3.12`, or have the owner turn off the Python entries in Settings > Apps > Advanced app settings > App execution
aliases.
**macOS:** `brew install python@3.12` (Homebrew from https://brew.sh). **Debian/Ubuntu:**
`sudo apt install python3 python3-venv python3-pip` (`sudo` asks for the owner's password: theirs to type).

Then the project's environment:
```powershell
py -3.12 -m venv env                                          # [macOS: python3.12 -m venv env; Linux: python3 -m venv env]
.\env\Scripts\python.exe -m pip install -r requirements-dev.txt   # [env/bin/python -m pip install -r ...]
.\env\Scripts\python.exe -m pre_commit install                # the commit hook that refuses secrets and bitstreams
```

## 3. Icarus Verilog and GTKWave

* **Windows:** `winget install --id Icarus.Verilog -e --silent --accept-package-agreements --accept-source-agreements`.
  That package downloads the installer from https://bleyer.org/icarus/ (Icarus 12); it installs to `C:\iverilog`, with
  GTKWave in `C:\iverilog\gtkwave\bin` when that part is included, and it may show a permission prompt. Fallback: the
  owner downloads the same installer from that page in a browser and runs it. **A `403 Forbidden` is often the
  network, not the site**: on the company network this blueprint was written on, a web filter blocked bleyer.org for
  winget and curl alike. Read the error page (a filter names itself: "Blocked by ..."), then use another network or
  ask IT; another source of Icarus and GTKWave, OSS CAD Suite, is in install_tools.md (not yet tried here).
* **macOS:** `brew install icarus-verilog`. Homebrew's GTKWave package is discontinued, so waveforms on a Mac need
  another viewer for `.vcd` files; simulation itself needs only Icarus.
* **Debian/Ubuntu:** `sudo apt install iverilog gtkwave` (CI installs `iverilog` the same way).

Check: `fpga.py doctor` shows `iverilog` and `vvp`; then `fpga.py sim blinky` prints `PASS`.

## 4. Quartus Prime Lite with the Cyclone V

Quartus Lite is free; it installs **each device family as a separate package**, and an install compiles only for the
families it has. The DE10-Nano needs **Cyclone V**. Facts and sources: the Quartus section of
[docs/de10nano_reference.md](../../../docs/de10nano_reference.md); the clicks: [install_tools.md](../../../docs/procedures/install_tools.md).

1. **Is there a Quartus already?** `doctor` lists every install with its families. One that lists `Cyclone V` is
   enough: skip to the driver.
2. **A Quartus without Cyclone V** (common: one installed for a DE10-Lite has `MAX 10` only): add the Cyclone V package
   **of the same version** (for 17.1 it is `cyclonev-17.1.0.590.qdz`; check its SHA1 with
   `Get-FileHash -Algorithm SHA1 <file>` against the reference), then Quartus **Tools > Install Devices...** or the
   Start-menu **Device Installer** (for 17.1: *Intel FPGA 17.1.0.590 Lite Edition > Quartus Prime Lite Edition
   17.1.0.590 > Device Installer (Quartus Prime 17.1)*), pointed at the folder holding the `.qdz`.
3. **No Quartus**: the owner downloads the current Quartus Prime Lite for their system from Altera's download
   center, in a browser (a free account may be needed; scripts are refused), **and its Cyclone V device package
   into the same folder**, then runs the installer, which installs the packages it finds next to it. The simulator
   the installer also offers (17.1 offers ModelSim) can be left out: this repo simulates with Icarus. Quartus is a
   download of gigabytes: start it early.
4. **Check**: `doctor` shows `Quartus with Cyclone V: <version>`. Quartus installed somewhere unusual: set
   `QUARTUS_ROOTDIR` to its `quartus` folder (the one that holds `bin64`), for this command or for good.

**macOS:** Quartus has no macOS version. A Mac owner can simulate everything here; to compile and program they need a
Windows or Linux computer, or a Linux virtual machine with USB passed through (the zangman guide uses Debian in
VirtualBox). Say this early, before they wait for downloads that will not run.

## 5. The USB-Blaster II driver

**Windows** (the owner clicks; you say each step): board powered, USB cable in its **USB-Blaster II** port. Device
Manager > **Other devices** > the **Unknown device** > Update driver > **Browse my computer for drivers** > the
folder `<Quartus>\drivers\usb-blaster-ii` (for example `C:\intelFPGA_lite\17.1\quartus\drivers\usb-blaster-ii`;
**not** the `usb-blaster` folder next to it, which is the older cable) > Next. Then `fpga.py jtag` lists
`DE-SoC` with two devices. Every step: [install_tools.md](../../../docs/procedures/install_tools.md#4-the-usb-blaster-ii-driver).

**Linux:** no driver; a udev rule gives a normal user access (vendor `09fb`). The rule and the source are in
[install_tools.md](../../../docs/procedures/install_tools.md#4-the-usb-blaster-ii-driver).

## 6. Things that go wrong (fix, then say what you changed)

| Symptom | Likely cause and fix |
|---|---|
| `'python' is not recognized` right after installing | Old PATH in this terminal: open a new one, or use `py -3.12` / the full path |
| `python` opens the Microsoft Store | The App execution alias: use `py -3.12`, or the owner turns the alias off |
| `running scripts is disabled on this system` | Don't change the policy: call `.\env\Scripts\python.exe` directly, never `Activate.ps1` |
| `iverilog` not found after installing | New terminal; `fpga.py` itself looks in `C:\iverilog\bin` |
| `winget` or a download fails with `403 Forbidden` | Read the page it got: a company web filter names itself ("Blocked by ..."). Another network, IT, or the other source in install_tools.md |
| `doctor`: a Quartus is found, but no `Quartus with Cyclone V` | That install lacks the Cyclone V package: section 4, step 2 |
| `doctor`: Quartus shows `could not ask it` | `quartus_sh` failed to start: run `<Quartus>\quartus\bin64\quartus_sh --version` and read the error |
| `fpga.py jtag`: no cable | In order: power, the USB-Blaster II port (not the UART one), the driver, another USB cable or port |
| The driver step finds nothing | The wrong folder (`usb-blaster` instead of `usb-blaster-ii`), or the board is not powered |
| Errors about long paths, or files locked while Quartus writes them | Keep the project short and outside OneDrive, like `C:\fpga\my-fpga` |
| `pip` cannot install something | The wrong Python: rebuild `env/` with 3.12 |
| Antivirus quarantines a tool | Tell the owner what and why; don't disable the antivirus |

## 7. Finish

Re-run `fpga.py doctor` and show the owner the result. Tick Phase 0 in
[docs/journey_checklist.md](../../../docs/journey_checklist.md) for what is done (Quartus can still be downloading),
then continue with [build-my-fpga-project](../build-my-fpga-project/SKILL.md) Phase 1. Be honest about anything you
could not fix: say what, why, and the one thing the owner can do.
