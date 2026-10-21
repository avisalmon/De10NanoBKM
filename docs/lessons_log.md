# What we learned, by date

The short version of every lesson in this blueprint, newest first, so you can see what changed since you last looked.
Each line points to where the full rule lives. Most of them came from something going wrong, or from checking a
"well-known fact" and finding that it was not quite true.

## 2026-10-21

- **A `403` can be your own network, not the site.** A company web filter blocked the Icarus Verilog installer's
  site, and `winget` only said `Forbidden (403)`. Open the address in a browser and read the page before blaming the
  site. [gotcha 17](procedures/gotchas.md)
- **Bitstreams and build folders never go into git.** `.gitignore` leaves them out, and the pre-commit check refuses
  `.sof`, `.pof`, `.jic`, `.rbf`, `db/`, `output_files/` and `sim_build/` by name even if they are forced in. Share a
  bitstream as a GitHub Release instead. [scripts/check_staged_secrets.py](../scripts/check_staged_secrets.py) ·
  [publish-to-github](../.claude/skills/publish-to-github/SKILL.md)
- **A version number written from memory is a guess.** Before the first push, every pinned version in CI (the
  checkout and setup-python actions, the gitleaks release and its checksum file) was checked to exist on GitHub.
  [ci.yml](../.github/workflows/ci.yml)
- **Quote the tool, don't paraphrase it.** Every message the procedures quote was checked against `fpga.py`, and the
  sample outputs are real runs, so what you read is what you will see.
  [build_and_program.md](procedures/build_and_program.md) · [simulate.md](procedures/simulate.md)

## 2026-10-20

- **On the DE10-Nano the FPGA is `@2`, not `@1`.** The JTAG chain has the HPS (the ARM side) and the FPGA; the
  DE10-Lite habit of `@1` aims at the wrong device. `fpga.py program` finds the FPGA by name, and a test refuses any
  other position in the docs. [gotcha 1](procedures/gotchas.md) ·
  [the reference](de10nano_reference.md#the-jtag-chain-program-the-fpga-at-2)
- **Quartus installed is not Quartus ready.** The computer this blueprint was written on had Quartus 17.1 with the
  MAX 10 only, which cannot compile for this board. `fpga.py doctor` asks every Quartus it finds for its device
  families. [gotcha 4](procedures/gotchas.md)
- **A popular wiki can be wrong about the board.** RocketBoards gives a different FPGA part and a bigger flash than
  Terasic's manual and files. Board facts come from Terasic, each tagged with its source.
  [gotcha 15](procedures/gotchas.md) · [the reference](de10nano_reference.md#places-that-are-wrong-or-will-trip-you)
- **Read the manual itself, not a summary of it.** Terasic's manual corrected our first draft in three places: SW10
  has six switches and ON means 0, the factory setting is FPPx32 (`01010`, for the microSD card's image), and the
  three 50 MHz clock pins carry only two clock signals.
  [the reference](de10nano_reference.md#sw10-the-msel-switches-what-the-fpga-does-at-power-on)
- **A testbench that says nothing has not passed.** `fpga.py sim` needs a line starting `PASS` and no `FAIL`
  anywhere. [gotcha 14](procedures/gotchas.md) · [simulate.md](procedures/simulate.md#when-it-passes)
- **The `.qsf` is the one list of design files.** The simulator compiles exactly the files Quartus compiles, so the
  design you simulate is the design you build.
  [simulate.md](procedures/simulate.md#the-qsf-is-the-one-list-of-design-files)
- **Intel's download site refuses scripts.** Download Quartus and the device packages in a browser, then check the
  file's SHA1. [gotcha 16](procedures/gotchas.md)
- **A PASS in simulation does not mean Quartus will accept the design.** Icarus accepted a latch in `always_comb`
  that Quartus refused with `Error (10166)`. Give every output a default at the top of the block.
  [gotcha 8](procedures/gotchas.md)
- **A misspelt pin name compiles.** Quartus only warns (`15706`), then picks a pin of its own (`Critical Warning
  (169085)`). Never program a build that printed 169085. [gotcha 7](procedures/gotchas.md)
- **`` `default_nettype none `` turns a typo into an error** in both tools, instead of a new wire stuck at 0.
  [gotcha 9](procedures/gotchas.md)
- **Icarus says `sorry:` and still passes.** It ignores what it supports only in part and exits 0: read the warnings
  under a `PASS`. [gotcha 10](procedures/gotchas.md)
- **Test the folklore before it becomes a rule.** A common warning says `input logic` ports fail under
  `` `default_nettype none ``. Icarus 12 and Quartus 17.1 both accept them, so this blueprint has no such rule (other
  tools may differ). [gotcha 9](procedures/gotchas.md)
