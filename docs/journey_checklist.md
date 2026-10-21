# From a fresh clone to your own design on the board: the checklist

The `build-my-fpga-project` skill walks you through this. Once your editor and AI chat are open on your copy of
the project ([get_started.md](get_started.md)), type **"Tell me what to do"**: the assistant does every step
marked **Assistant** itself, and stops with exact instructions for each **You** step. Say it again in any later
session and it resumes from the first unticked box. The assistant ticks the boxes as things get done, in the same
commit as the work, so this file becomes the log of your journey.

Legend: **Assistant** = the AI does it, you watch. **You** = only a person can do it: a download in a browser, an
installer, a cable, a switch, a button, a look at the board.

## Before the chat (You, once per computer): [get_started.md](get_started.md)

- [ ] A GitHub account, with two-factor authentication on
- [ ] VS Code installed, with GitHub Copilot (Agent mode) **or** Claude Code, signed in, and it answers `hello`
- [ ] Git installed (`git --version` works in a VS Code terminal)
- [ ] The project cloned into a short folder outside OneDrive (`C:\fpga\my-fpga`, or `~/fpga/my-fpga`), opened in
      VS Code and trusted
- [ ] You typed **"Tell me what to do"** in the chat, and it answered

## Phase 0: the tools ([install_tools.md](procedures/install_tools.md); the `setup-my-computer` skill)

- [ ] **Assistant:** `fpga.py doctor` run, and its table shown to you
- [ ] **Assistant:** Python 3.12 installed, the `env/` folder built, the dev requirements installed
- [ ] **Assistant:** Icarus Verilog installed (GTKWave too, where it exists), and `doctor` finds `iverilog` and `vvp`
- [ ] **You:** Quartus Prime Lite **with the Cyclone V device package** downloaded in a browser. It is large:
      start it first, and do Phase 1 while it downloads
- [ ] **You:** Quartus installed (or the Cyclone V package added to a Quartus you already have)
- [ ] **Assistant:** `doctor` ends with `Everything needed is installed.`

## Phase 1: the template in simulation (no board needed)

- [ ] **Assistant:** `fpga.py sim blinky` prints `PASS  templates/blinky/sim/tb_blinky`
- [ ] **Assistant:** the template explained in five lines: the 50 MHz clock, the counter, the synchronizers, what
      KEY0 and KEY1 do; and what the testbench checks
- [ ] **You and the assistant:** the waveform opened (`fpga.py sim blinky --waves`, then GTKWave) and looked at
      together

## Phase 2: compile the template ([build_and_program.md](procedures/build_and_program.md))

- [ ] **Assistant:** `fpga.py build blinky` prints `timing met` and
      `Bitstream: templates/blinky/output_files/blinky.sof`
- [ ] **Assistant:** the Quartus version, the resources used and the worst slack recorded in the template's
      [README](../templates/blinky/README.md) and in the [roadmap](blueprint_roadmap.md): a first for this blueprint

## Phase 3: the template on the board

- [ ] **You:** the 5 V power adapter plugged into the board; LED9 lights
- [ ] **You:** the Mini-B USB cable from the computer to the board's **USB-Blaster II** port (not the UART port)
- [ ] **You** (Windows, the first time): the USB-Blaster II driver installed, following the assistant's steps
- [ ] **Assistant:** `fpga.py jtag` shows the chain: `@1` the HPS, `@2` the FPGA
- [ ] **Assistant:** `fpga.py program blinky` ends with `Done.`
- [ ] **You:** LED10 (`CONF_DONE`) is lit; the LEDs count in binary (LED0 blinks once a second); holding KEY0 holds
      the count at 0; holding KEY1 shows the four switches on LED0 to LED3 while LED4 to LED7 go dark
- [ ] **Assistant:** the template's "Seen working on the board" row ticked with what you saw, and the roadmap updated

## Phase 4: your first design

- [ ] **You:** your idea, in a few sentences: what a person sees on the board, and what they press or flip
- [ ] **Assistant:** `fpga.py new <name>`; "What it does" written in your words in `projects/<name>/README.md`,
      and **you** said it is right
- [ ] **Assistant:** the testbench first: `sim/tb_<name>.sv` checks what the README promises, and fails before
      the design is changed
- [ ] **Assistant:** the design in `rtl/`, until `fpga.py sim <name>` prints `PASS`
- [ ] **Assistant:** reviewed with the `fpga-mentor` checklist (at most three suggestions)
- [ ] **You:** you explained what it will do on the board, in your own words
- [ ] **Assistant:** `fpga.py build <name>`: timing met
- [ ] **You:** after `fpga.py program <name>`, you saw it do what the README says
- [ ] **Assistant:** the project README's status table filled in, each row with its evidence

## Phase 5: your own GitHub repository (optional; the `publish-to-github` skill)

- [ ] **You:** logged in to GitHub once in the browser (`gh auth login`)
- [ ] **You:** decided: a private or a public repository
- [ ] **Assistant:** a privacy-safe commit email set, and the check before pushing is clean
- [ ] **Assistant:** your repository created as `origin`, with the blueprint kept as the remote `blueprint`
- [ ] **Assistant:** pushed, after **you** said so, and the first CI run is green

## Phase 6: what next

- [ ] **You:** picked the next step: a second design, something on a GPIO header (3.3 V only), keeping a design in
      the flash, HDMI, the ADC, or Linux on the HPS
- [ ] **Assistant:** whatever was learnt landed in the reference, a procedure and a skill

## Graduation

- [ ] Your design passes `fpga.py sim`, built with timing met, and you saw it work on the board
- [ ] You can explain in your own words why the buttons go through a synchronizer, and what your testbench proves
- [ ] (Optional) The repository made yours: your own `README.md`, your choice of `LICENSE`, the `blueprint` remote
      kept or removed
