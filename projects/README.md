# Your designs

One folder per design. Start each one from the template, with a name made of lowercase letters, digits and `_`,
starting with a letter:

```powershell
.\env\Scripts\python.exe scripts\fpga.py new my_counter
```

That copies [templates/blinky](../templates/blinky/) to `projects/my_counter/`, renames its `.qpf`, `.qsf` and `.sdc`
to match, and writes a `README.md` with two things to fill in: **what it does** (in your words: what a person sees on
the board and what they press), and a **status table** (simulated, compiled, seen on the board) where a row says
"done" only with its evidence.

Every folder here with a `.qpf` file is a project: `python scripts/fpga.py sim --all` simulates each one, and so
does CI on every push. The method, one design at a time, is Phase 4 of the [checklist](../docs/journey_checklist.md).
