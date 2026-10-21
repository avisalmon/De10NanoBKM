# Blueprint roadmap and known limits

For whoever maintains the blueprint itself (not for owners who cloned it to build their own designs). Rule 8 of
[CLAUDE.md](../CLAUDE.md) applies here first: a box is ticked only when the thing was done and seen, and the line says
how.

## Verified here

* **The repo checks itself** (`pytest -q`, on Windows with Python 3.12): every pin in the template's `.qsf` against
  [the reference](de10nano_reference.md); the skills, their mirror in `.github/skills/` and the generated
  instructions; every relative link in the docs; `fpga.py`'s logic against sample Quartus answers and reports (which
  Quartus is chosen, which device on the chain is the FPGA, how the reports are read); the simulation flow with the
  real Icarus Verilog (a failing, a silent and a never-ending testbench all count as failures); the secret and
  bitstream checks; the update check; the "Last updated" mark.
* **Simulation on Windows**: the template passes its 10-check testbench with Icarus Verilog 12.0
  (`fpga.py sim --all`), and `--waves` writes its waveform file.
* **CI on GitHub**: the first push (21 October 2026) was green: gitleaks over the full history (`no leaks found`),
  ruff, all 107 tests, the template's testbench and the skills check, on Ubuntu 24.04, where `apt` installs Icarus
  Verilog 12.0, the same version as on Windows. `ubuntu-latest` is moving to Ubuntu 26 from 19 October 2026; the log
  prints `iverilog -V`, so a new Icarus version will show there.
* **Every `#section` link in the docs** leads to a real heading in GitHub's rendering of the target page (checked
  after the first push: 19 links). The repo's own link test checks the files, not the sections.
* **`fpga.py doctor` on a real computer**: it found Python, Git, the GitHub CLI, Icarus and GTKWave, found Quartus
  17.1, saw that it had the MAX 10 only, and said what to install.
* **The Quartus messages the docs quote** (the error and warning numbers in [gotchas.md](procedures/gotchas.md) and
  the `quartus-build-and-program` skill, and the exit codes) were produced with Quartus 17.1 on small test designs for
  the MAX 10, the only family it had. The same messages are expected for the Cyclone V, but have not been seen for it.
* **The board's facts** were checked against Terasic's user manual and golden-top `.qsf`, and each is tagged
  `[verified]`, `[community]` or `[unverified]` in [the reference](de10nano_reference.md).

## NOT yet verified

Written from Terasic's and Intel's documents, community guides, or the code's own logic, but not yet run for real.
The first person to do each one should record the evidence here and in the template's README, and fix whatever was
wrong:

- [ ] **Compiling the template for the Cyclone V** (`5CSEBA6U23I7`) with Quartus Prime Lite: the computer this was
      written on had no Cyclone V device package
- [ ] **Timing met** at 50 MHz with the template's `.sdc`, and `fpga.py build` reading the worst slack from a real
      Cyclone V report
- [ ] **The resource line** `fpga.py build` prints: it reads `Logic utilization (in ALMs)` from the `.fit.summary`,
      the Cyclone V wording (the MAX 10 says `Total logic elements`)
- [ ] **Programming a real DE10-Nano**: `fpga.py jtag` and `fpga.py program`, the cable name `DE-SoC [USB-1]`, and the
      chain's order (two devices is in the manual; the HPS at `@1` and the FPGA at `@2` comes from community guides)
- [ ] **What the chain shows when Quartus has no Cyclone V package** (perhaps unnamed devices; `--index 2` forces the
      position)
- [ ] **The template on the board**: the LEDs count, `KEY0` holds the count at 0, `KEY1` shows the switches
- [ ] **The USB-Blaster II driver** steps on Windows, and whether the Quartus installer offers to install it
- [ ] **Adding the Cyclone V package** with the Device Installer (its screens and the `.qdz` size come from Intel's
      documents)
- [ ] **macOS and Linux**: every step on this blueprint was run on Windows only; the others are from the vendors'
      documents
- [ ] **OSS CAD Suite** as the other source of Icarus Verilog and GTKWave
- [ ] **GTKWave's screens** as [simulate.md](procedures/simulate.md) describes them
- [ ] **Sharing a bitstream as a GitHub Release** (the `publish-to-github` skill's `gh release create` step)
- [ ] **`pre-commit install`** and the local `no-secrets` hook on a newcomer's computer
- [ ] **The journey in a fresh clone**: "Tell me what to do" triggers the `build-my-fpga-project` skill in Claude Code
      **and** in GitHub Copilot's agent mode, it resumes from [the checklist](journey_checklist.md) in a later session,
      and it carries a newcomer from no tools to their own design on the board
- [ ] **GitHub Copilot finding the skills** in `.github/skills/` (the generated `.github/copilot-instructions.md` and
      `AGENTS.md` index every skill's triggers, as a fallback)

## Not covered yet

New ground for this blueprint. Each one starts with research: its facts go into the reference, with sources, before
anything is built on them, and what is learnt becomes a procedure and a skill (CLAUDE.md, rule 10).

* **Keeping a design after power-off**: the EPCS64 flash through the Serial Flash Loader, or the FPGA image on the
  microSD card
* **Linux on the HPS**, and the bridges between the ARM side and the FPGA (Platform Designer)
* **HDMI out**: the ADV7513 transmitter must be configured over I2C before it shows anything
* **The ADC** (LTC2308, 8 channels, on the FPGA side)
* **The GPIO and Arduino headers** beyond the safety rules: no example design uses them yet
* **Other simulators** (Questa, Verilator): `fpga.py` runs Icarus Verilog only

## Known limits of what was built

* Icarus Verilog supports SystemVerilog only in part, so the designs keep to what both Icarus and Quartus accept
  ([gotcha 10](procedures/gotchas.md)).
* Three board facts are not from Terasic's documents: the USB-Blaster II port's name `J13`, the chain's order, and
  "the pins are not 5 V tolerant" (this repo's standing assumption, which only makes it more careful). See the tags in
  [the reference](de10nano_reference.md).
* Licensed MIT (2026, Avi Salmon). Owners who start from the blueprint inherit the [LICENSE](../LICENSE) file and may
  replace it in their own repository.
