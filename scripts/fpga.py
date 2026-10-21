#!/usr/bin/env python
"""One command for the DE10-Nano flow: check the tools, start a project, simulate, build, program.

    python scripts/fpga.py doctor               # what is installed, and is the board connected?
    python scripts/fpga.py new my_counter       # start projects/my_counter from templates/blinky
    python scripts/fpga.py sim my_counter       # run its self-checking testbenches (Icarus Verilog)
    python scripts/fpga.py sim --all            # ... for the template and every project
    python scripts/fpga.py build my_counter     # simulate, then compile with Quartus, check timing
    python scripts/fpga.py jtag                 # the cables, and the devices on each JTAG chain
    python scripts/fpga.py program my_counter   # load the .sof into the FPGA (device @2)

A project is a folder with one .qpf/.qsf pair, an rtl/ folder and a sim/ folder of tb_*.sv
testbenches. The .qsf is the one list of design files: the simulator compiles exactly the
SYSTEMVERILOG_FILE / VERILOG_FILE lines Quartus does, so the design you simulate is the design
you build.

A testbench passes when the simulator exits cleanly, it printed a line starting with PASS, and it
printed nothing containing FAIL and no line starting with ERROR or FATAL.
"""

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
PROJECTS = ROOT / "projects"
TEMPLATE = TEMPLATES / "blinky"
INSTALL_GUIDE = "docs/procedures/install_tools.md"

FAMILY = "Cyclone V"
DEVICE = "5CSEBA6U23I7"
# The DE10-Nano's JTAG chain holds two devices: @1 is the HPS (the ARM side, SOCVHPS) and @2 is
# the FPGA (5CSEBA6). Program @2. The position is still read from the chain when a board is there.
FPGA_ON_CHAIN = re.compile(r"5CSEBA6", re.I)
FPGA_INDEX = 2

NAME_RULE = re.compile(r"[a-z][a-z0-9_]{0,40}")
INSTALL_FOLDERS = ("intelFPGA_lite", "intelFPGA", "altera_lite", "altera")
BUILD_OUTPUTS = (
    "db",
    "incremental_db",
    "output_files",
    "qdb",
    "sim_build",
    "greybox_tmp",
    "tmp-clearbox",
    "hc_output",
    ".qsys_edit",
    "hps_isw_handoff",
)
SIM_TIMEOUT_S = 120


class UserError(Exception):
    """Something the owner can fix. Printed as one clear message, without a traceback."""


# ---------------------------------------------------------------- small helpers


def run(cmd, cwd=None, timeout=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(part) for part in cmd],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def shown(cmd) -> str:
    """A command as you would type it, quoted where a shell needs quotes."""
    return " ".join(f'"{p}"' if re.search(r"[\s;]", str(p)) else str(p) for p in cmd)


def find_tool(name: str) -> Path | None:
    """A command on PATH, or in the folder its Windows installer uses by default."""
    found = shutil.which(name)
    if found:
        return Path(found)
    if os.name == "nt":
        for folder in (Path("C:/iverilog/bin"), Path("C:/iverilog/gtkwave/bin")):
            if (folder / f"{name}.exe").is_file():
                return folder / f"{name}.exe"
    return None


def first_line(cmd) -> str | None:
    """The first line a tool prints about itself, or None if it is not installed."""
    try:
        done = run(cmd, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = (done.stdout + done.stderr).strip().splitlines()
    return lines[0].strip() if lines else ""


# ---------------------------------------------------------------- Quartus installs


@dataclass
class Quartus:
    bin: Path
    version: str
    families: list[str] | None = None  # filled on first use: asking quartus_sh takes a second

    def tool(self, name: str) -> Path:
        return self.bin / (f"{name}.exe" if os.name == "nt" else name)


def version_key(version: str) -> tuple[int, ...]:
    """'23.1std' -> (23, 1), so 9.1 < 17.1 < 23.1std. 'unknown' -> () sorts oldest."""
    return tuple(int(n) for n in re.findall(r"\d+", version))


def version_from_path(bin_dir: Path) -> str:
    """C:/intelFPGA_lite/17.1/quartus/bin64 -> '17.1'; .../altera_lite/25.1std/... -> '25.1std'."""
    for part in reversed(bin_dir.parts):
        if re.fullmatch(r"\d+\.\d+[\w.]*", part):
            return part
    return "unknown"


def quartus_bin_dirs() -> list[Path]:
    """Every folder that might hold quartus_sh: the overrides first, then the usual places."""
    dirs: list[Path] = []
    if os.environ.get("QUARTUS_BIN"):
        dirs.append(Path(os.environ["QUARTUS_BIN"]))
    if os.environ.get("QUARTUS_ROOTDIR"):
        root = Path(os.environ["QUARTUS_ROOTDIR"])
        dirs += [root / "bin64", root / "bin"]
    on_path = shutil.which("quartus_sh")
    if on_path:
        dirs.append(Path(on_path).parent)
    if os.name == "nt":
        bases = [Path("C:/") / name for name in INSTALL_FOLDERS]
    else:
        bases = [Path.home() / name for name in INSTALL_FOLDERS]
        bases += [Path("/opt") / name for name in INSTALL_FOLDERS]
    for base in bases:
        if base.is_dir():
            for version_dir in sorted(base.iterdir()):
                dirs += [version_dir / "quartus" / "bin64", version_dir / "quartus" / "bin"]
    return dirs


def find_quartus_installs() -> list[Quartus]:
    """Every Quartus install found, newest first."""
    exe = "quartus_sh.exe" if os.name == "nt" else "quartus_sh"
    seen: set[str] = set()
    installs = []
    for folder in quartus_bin_dirs():
        if not (folder / exe).is_file():
            continue
        key = os.path.normcase(str(folder.resolve()))
        if key not in seen:
            seen.add(key)
            installs.append(Quartus(folder, version_from_path(folder)))
    return sorted(installs, key=lambda q: version_key(q.version), reverse=True)


def parse_family_list(text: str) -> list[str]:
    """quartus_sh answers with a Tcl list: '{Cyclone V} {MAX 10}' -> ['Cyclone V', 'MAX 10']."""
    return [braced or bare for braced, bare in re.findall(r"\{([^}]*)\}|(\S+)", text.strip())]


def installed_families(quartus: Quartus) -> list[str]:
    """The device families this install can compile for (Quartus Lite installs them one by one)."""
    if quartus.families is None:
        quartus.families = []
        try:
            done = run([quartus.tool("quartus_sh"), "--tcl_eval", "get_family_list"], timeout=300)
        except (OSError, subprocess.TimeoutExpired):
            return quartus.families
        lines = [line for line in done.stdout.splitlines() if line.strip()]
        if done.returncode == 0 and lines:
            quartus.families = parse_family_list(lines[-1])
    return quartus.families


def choose_quartus(installs: list[Quartus], families=installed_families) -> Quartus | None:
    """The newest install that can compile for the DE10-Nano's FPGA family, or None."""
    for quartus in installs:  # newest first
        if FAMILY in families(quartus):
            return quartus
    return None


# ---------------------------------------------------------------- JTAG


@dataclass
class Cable:
    number: int
    name: str
    devices: list[tuple[str, str]] = field(default_factory=list)  # (IDCODE, name), chain order

    def fpga_index(self) -> int | None:
        for index, (_idcode, name) in enumerate(self.devices, start=1):
            if FPGA_ON_CHAIN.search(name):
                return index
        return None


def parse_jtagconfig(text: str) -> list[Cable]:
    """`jtagconfig` output -> cables, each with its devices in chain order (@1, @2, ...)."""
    cables: list[Cable] = []
    for line in text.splitlines():
        if match := re.match(r"^\s*(\d+)\)\s+(.+?)\s*$", line):
            cables.append(Cable(int(match[1]), match[2]))
        elif (match := re.match(r"^\s+([0-9A-Fa-f]{8})\s+(.+?)\s*$", line)) and cables:
            cables[-1].devices.append((match[1].upper(), match[2]))
    return cables


def jtagconfig_path(installs: list[Quartus]) -> Path | None:
    exe = "jtagconfig.exe" if os.name == "nt" else "jtagconfig"
    for quartus in installs:
        if (quartus.bin / exe).is_file():
            return quartus.bin / exe
    found = shutil.which("jtagconfig")
    return Path(found) if found else None


def scan_jtag(installs: list[Quartus]) -> tuple[list[Cable], str]:
    tool = jtagconfig_path(installs)
    if tool is None:
        raise UserError(f"jtagconfig not found. It comes with Quartus Prime: see {INSTALL_GUIDE}")
    try:
        done = run([tool], timeout=60)
    except subprocess.TimeoutExpired as error:
        raise UserError(
            "jtagconfig did not answer in 60 s. Unplug the USB cable, wait, replug."
        ) from error
    text = done.stdout + done.stderr
    return parse_jtagconfig(text), text


def program_command(pgm, sof: str, cable: str | None, index: int) -> list[str]:
    """quartus_pgm -m jtag [-c CABLE] -o "p;<sof>@<index>": p = program, @index = which device."""
    cmd = [str(pgm), "-m", "jtag"]
    if cable:
        cmd += ["-c", cable]
    return cmd + ["-o", f"p;{sof}@{index}"]


# ---------------------------------------------------------------- projects and their .qsf


TOKEN = re.compile(r'"([^"]*)"|\{([^}]*)\}|(\S+)')


def tcl_words(line: str) -> list[str]:
    return [quoted or braced or bare for quoted, braced, bare in TOKEN.findall(line)]


def split_options(words: list[str]) -> tuple[dict[str, str], list[str]]:
    """['-name', 'FAMILY', 'Cyclone V'] -> ({'-name': 'FAMILY'}, ['Cyclone V'])."""
    options: dict[str, str] = {}
    positional: list[str] = []
    i = 0
    while i < len(words):
        word = words[i]
        if word.startswith("-") and not re.fullmatch(r"-[\d.]+", word) and i + 1 < len(words):
            options[word] = words[i + 1]
            i += 2
        else:
            positional.append(word)
            i += 1
    return options, positional


@dataclass
class Settings:
    """What a .qsf says: global assignments in file order, pin locations and I/O standards."""

    assignments: list[tuple[str, str]] = field(default_factory=list)
    pins: dict[str, str] = field(default_factory=dict)  # signal -> PIN_xx
    io_standards: dict[str, str] = field(default_factory=dict)  # signal -> "3.3-V LVTTL"

    def get(self, name: str) -> str | None:
        return next((value for key, value in self.assignments if key == name), None)

    def all(self, name: str) -> list[str]:
        return [value for key, value in self.assignments if key == name]


def read_qsf(path: Path) -> Settings:
    settings = Settings()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        words = tcl_words(line)
        if not words or words[0].startswith("#"):
            continue
        options, positional = split_options(words[1:])
        if not positional:
            continue
        if words[0] == "set_global_assignment" and "-name" in options:
            settings.assignments.append((options["-name"], positional[0]))
        elif words[0] == "set_location_assignment" and "-to" in options:
            settings.pins[options["-to"]] = positional[0]
        elif words[0] == "set_instance_assignment" and options.get("-name") == "IO_STANDARD":
            if "-to" in options:
                settings.io_standards[options["-to"]] = positional[0]
    return settings


@dataclass
class Project:
    dir: Path
    revision: str

    @property
    def qsf(self) -> Path:
        return self.dir / f"{self.revision}.qsf"

    def settings(self) -> Settings:
        return read_qsf(self.qsf)

    def sources(self) -> list[str]:
        """The design files in compile order, exactly as the .qsf lists them."""
        kinds = ("SYSTEMVERILOG_FILE", "VERILOG_FILE")
        return [value for key, value in self.settings().assignments if key in kinds]

    def testbenches(self) -> list[Path]:
        sim = self.dir / "sim"
        return sorted(sim.glob("tb_*.sv")) + sorted(sim.glob("tb_*.v"))

    @property
    def sof(self) -> Path:
        out = self.settings().get("PROJECT_OUTPUT_DIRECTORY") or "."
        return self.dir / out / f"{self.revision}.sof"


def load_project(folder: Path) -> Project:
    qpfs = sorted(folder.glob("*.qpf"))
    if len(qpfs) != 1:
        raise UserError(f"{rel(folder)}: expected one .qpf file, found {len(qpfs)}")
    text = qpfs[0].read_text(encoding="utf-8", errors="replace")
    match = re.search(r'^\s*PROJECT_REVISION\s*=\s*"([^"]+)"', text, re.M)
    project = Project(folder.resolve(), match[1] if match else qpfs[0].stem)
    if not project.qsf.is_file():
        raise UserError(f"{rel(folder)}: {project.qsf.name} is missing")
    return project


def resolve_project(name: str) -> Project:
    for folder in (Path(name), PROJECTS / name, TEMPLATES / name):
        if folder.is_dir() and any(folder.glob("*.qpf")):
            return load_project(folder)
    raise UserError(
        f"no project called {name!r} in projects/ or templates/"
        " (a project is a folder with a .qpf file)"
    )


def all_projects() -> list[Project]:
    found = []
    for base in (TEMPLATES, PROJECTS):
        if base.is_dir():
            for folder in sorted(p for p in base.iterdir() if p.is_dir()):
                if any(folder.glob("*.qpf")):
                    found.append(load_project(folder))
    return found


PROJECT_README = """# {name}

Started from `templates/blinky` with `python scripts/fpga.py new {name}`.

## What it does

(One or two sentences: what should a person see on the board, and what do they press?)

## Status

| Step | State | Evidence |
|---|---|---|
| Simulated: `python scripts/fpga.py sim {name}` | not yet | |
| Compiled, timing met: `python scripts/fpga.py build {name}` | not yet | |
| Seen working on the board: `python scripts/fpga.py program {name}` | not yet | |

Only write "done" next to a step with its evidence: the PASS line, the worst slack, what you saw
on the board. Simulated is not compiled, and compiled is not working.
"""


def edit(path: Path, change) -> None:
    path.write_text(change(path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")


def new_project(name: str, template: Path = TEMPLATE, dest_root: Path = PROJECTS) -> Path:
    if not NAME_RULE.fullmatch(name):
        raise UserError(
            f"{name!r} can't be a project name: start with a lowercase letter, then use only"
            " lowercase letters, digits and _ (at most 41 characters). Example: my_counter"
        )
    dest = dest_root / name
    if dest.exists():
        raise UserError(f"{rel(dest)} already exists. Pick another name.")
    old = load_project(template).revision
    ignore = shutil.ignore_patterns(*BUILD_OUTPUTS, "*.qws", "README.md")
    shutil.copytree(template, dest, ignore=ignore)
    for suffix in (".qpf", ".qsf", ".sdc"):
        if (dest / f"{old}{suffix}").exists():
            (dest / f"{old}{suffix}").rename(dest / f"{name}{suffix}")
    edit(
        dest / f"{name}.qpf",
        lambda text: re.sub(r'(PROJECT_REVISION\s*=\s*)"[^"]*"', rf'\1"{name}"', text),
    )
    edit(dest / f"{name}.qsf", lambda text: text.replace(f"{old}.sdc", f"{name}.sdc"))
    readme = PROJECT_README.format(name=name)
    (dest / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    return dest


# ---------------------------------------------------------------- simulation


@dataclass
class SimResult:
    project: Project
    testbench: str
    passed: bool
    log: str
    warnings: str
    seconds: float


PASS_LINE = re.compile(r"^PASS\b", re.M)
FAIL_MARK = re.compile(r"FAIL|^(ERROR|FATAL)\b", re.M)


def verdict(returncode: int, output: str) -> bool:
    return returncode == 0 and bool(PASS_LINE.search(output)) and not FAIL_MARK.search(output)


def sim_tools() -> tuple[Path, Path]:
    iverilog, vvp = find_tool("iverilog"), find_tool("vvp")
    if not iverilog or not vvp:
        raise UserError(
            "Icarus Verilog (iverilog and vvp) is not installed, or not on PATH."
            f" Install it: {INSTALL_GUIDE}"
        )
    return iverilog, vvp


def simulate(project: Project, waves=False, timeout=SIM_TIMEOUT_S) -> list[SimResult]:
    iverilog, vvp = sim_tools()
    sources = project.sources()
    (project.dir / "sim_build").mkdir(exist_ok=True)
    results = []
    for tb in project.testbenches():
        name, start = tb.stem, time.monotonic()
        compile_cmd = [iverilog, "-g2012", "-Wall", "-Wno-timescale", "-I", "rtl"]
        compile_cmd += ["-o", f"sim_build/{name}.vvp", "-s", name, *sources]
        compile_cmd.append(tb.relative_to(project.dir).as_posix())
        built = run(compile_cmd, cwd=project.dir)
        notes = (built.stdout + built.stderr).strip()
        if built.returncode != 0:
            log = f"FAIL: {name} did not compile:\n{notes}"
            results.append(SimResult(project, name, False, log, "", time.monotonic() - start))
            continue
        plusargs = ["+waves"] if waves else []
        try:
            ran = run(
                [vvp, "-n", f"{name}.vvp", *plusargs],
                cwd=project.dir / "sim_build",
                timeout=timeout,
            )
            log = ran.stdout + ran.stderr
            passed = verdict(ran.returncode, log)
        except subprocess.TimeoutExpired:
            log = f"FAIL: {name} still running after {timeout} s. Does it end with $finish?"
            passed = False
        results.append(SimResult(project, name, passed, log, notes, time.monotonic() - start))
    return results


def report(results: list[SimResult]) -> int:
    """Print one line per testbench (and the evidence when it failed). Returns the failures."""
    failed = 0
    for result in results:
        mark = "PASS" if result.passed else "FAIL"
        where = f"{rel(result.project.dir)}/sim/{result.testbench}"
        print(f"  {mark}  {where}  ({result.seconds:.1f} s)")
        if result.warnings:
            print("\n".join(f"        {line}" for line in result.warnings.splitlines()[:20]))
        if not result.passed:
            failed += 1
            tail = result.log.strip().splitlines()[-25:]
            print("\n".join(f"        {line}" for line in tail))
    return failed


# ---------------------------------------------------------------- Quartus reports


def parse_summary(text: str) -> dict[str, str]:
    """A Quartus *.summary file: 'Key : value' lines."""
    found = {}
    for line in text.splitlines():
        key, sep, value = line.partition(" : ")
        if sep:
            found[key.strip()] = value.strip()
    return found


def parse_slacks(text: str) -> list[tuple[str, float]]:
    """The .sta.summary: 'Type : <corner> <analysis> <clock>' then 'Slack : <ns>' per check."""
    slacks, kind = [], None
    for line in text.splitlines():
        if match := re.match(r"^Type\s*:\s*(.+?)\s*$", line):
            kind = match[1]
        elif (match := re.match(r"^Slack\s*:\s*(-?\d+(?:\.\d+)?)", line)) and kind:
            slacks.append((kind, float(match[1])))
    return slacks


def read_if_there(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


IMPORTANT = re.compile(
    r"^\s*(Error|Critical Warning)|does not exist in design|Info: Command: "
    r"|Quartus Prime .+ was (successful|unsuccessful)"
)
# On a failure Quartus also prints its bookkeeping as "Error: Peak virtual memory: ...": not news.
BOOKKEEPING = re.compile(
    r"^Error: (Peak virtual memory|Processing ended|Elapsed time|Total CPU time)"
)


def worth_showing(line: str) -> bool:
    """Errors, critical warnings, a pin line naming no port, and each step's result."""
    return bool(IMPORTANT.search(line)) and not BOOKKEEPING.match(line)


def compile_with_quartus(quartus: Quartus, project: Project, log_path: Path) -> int:
    """quartus_sh --flow compile, every line saved to log_path, the important ones shown."""
    cmd = [str(quartus.tool("quartus_sh")), "--flow", "compile", project.revision]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  {shown(cmd)}")
    with (
        open(log_path, "w", encoding="utf-8") as log,
        subprocess.Popen(
            cmd,
            cwd=project.dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ) as proc,
    ):
        for line in proc.stdout:
            log.write(line)
            if worth_showing(line):
                print(f"  {line.rstrip()}")
        return proc.wait()


# ---------------------------------------------------------------- commands


def cmd_new(args) -> int:
    dest = new_project(args.name)
    print(f"Created {rel(dest)} from {rel(TEMPLATE)}.")
    print(
        f"Next: describe it in {rel(dest)}/README.md, then: python scripts/fpga.py sim {args.name}"
    )
    return 0


def cmd_sim(args) -> int:
    if args.all:
        projects = all_projects()
    elif args.project:
        projects = [resolve_project(args.project)]
    else:
        raise UserError("which project? python scripts/fpga.py sim <project>   (or: sim --all)")
    sim_tools()
    failed = total = 0
    for project in projects:
        print(f"{rel(project.dir)}:")
        results = simulate(project, waves=args.waves)
        if not results:
            print(
                "  FAIL  no testbench: every project needs sim/tb_<name>.sv (copy the template's)"
            )
            failed, total = failed + 1, total + 1
            continue
        failed += report(results)
        total += len(results)
        if args.waves:
            for vcd in sorted((project.dir / "sim_build").glob("*.vcd")):
                print(f"  waveform: {rel(vcd)}   (open it: gtkwave {rel(vcd)})")
    print(f"{total - failed} of {total} testbenches passed.")
    return 1 if failed else 0


def cmd_build(args) -> int:
    project = resolve_project(args.project)
    if args.skip_sim:
        print("Skipping simulation (--skip-sim). Say why in the project README.")
    else:
        print(f"Simulating {rel(project.dir)} first: simulate before you burn.")
        try:
            results = simulate(project)
        except UserError as error:
            raise UserError(f"{error}\n(or build without simulating: --skip-sim)") from error
        if not results:
            raise UserError("no testbench in sim/: write one, or build anyway with --skip-sim")
        if report(results):
            print("A testbench failed, so nothing was compiled. Fix the design (or the testbench).")
            return 1
    quartus = choose_quartus(find_quartus_installs())
    if quartus is None:
        raise UserError(
            f"no Quartus Prime install that can compile for {FAMILY} was found. Quartus Lite"
            f" installs device families separately; you need the Cyclone V one: {INSTALL_GUIDE}"
        )
    print(f"Compiling with Quartus {quartus.version} ({quartus.bin}). This takes a few minutes.")
    log_path = project.sof.parent / "build.log"
    if compile_with_quartus(quartus, project, log_path) != 0:
        print(f"Compile FAILED. The full log: {rel(log_path)}. Read the first Error line first.")
        return 1
    out = project.sof.parent
    fit = parse_summary(read_if_there(out / f"{project.revision}.fit.summary"))
    for key in ("Logic utilization (in ALMs)", "Total registers", "Total pins", "Total PLLs"):
        if key in fit:
            print(f"  {key}: {fit[key]}")
    slacks = parse_slacks(read_if_there(out / f"{project.revision}.sta.summary"))
    if not slacks:
        print("  timing: no timing summary found; look in output_files/*.sta.rpt")
    else:
        kind, worst = min(slacks, key=lambda item: item[1])
        if worst < 0:
            print(f"  TIMING FAILED: worst slack {worst:+.3f} ns ({kind}).")
            print(
                "  The board may work today and fail when warm."
                " See the quartus-build-and-program skill."
            )
            return 1
        print(f"  timing met: worst slack {worst:+.3f} ns ({kind})")
    if not project.sof.is_file():
        print(f"Compile finished but {rel(project.sof)} is missing. Read {rel(log_path)}.")
        return 1
    print(f"Bitstream: {rel(project.sof)}")
    print(f"Next: python scripts/fpga.py program {args.project}")
    return 0


def describe_chain(cable: Cable) -> None:
    print(f"{cable.number}) {cable.name}")
    if not cable.devices:
        print("     (no devices: the board may be off, or the cable is not talking to it)")
    for index, (idcode, name) in enumerate(cable.devices, start=1):
        if FPGA_ON_CHAIN.search(name):
            role = "   <- the FPGA: program this one"
        elif "SOCVHPS" in name.upper():
            role = "   <- the HPS (the ARM processors); not programmed with a .sof"
        else:
            role = ""
        print(f"     @{index}  {idcode}  {name}{role}")


NO_CABLE_HINT = (
    "No JTAG cable found. Check, in this order: the board has power; the USB cable is in the"
    " board's USB-Blaster II port (not the UART or OTG port); the USB-Blaster II driver is"
    f" installed ({INSTALL_GUIDE})."
)


def cmd_jtag(args) -> int:
    cables, raw = scan_jtag(find_quartus_installs())
    if not cables:
        print(raw.strip() or "(jtagconfig printed nothing)")
        print(NO_CABLE_HINT)
        return 1
    for cable in cables:
        describe_chain(cable)
    return 0


def pick_cable(cables: list[Cable], wanted: str | None) -> Cable:
    if not cables:
        raise UserError(NO_CABLE_HINT)
    if wanted:
        for cable in cables:
            if wanted == str(cable.number) or wanted.lower() in cable.name.lower():
                return cable
        raise UserError(
            f"no cable matches {wanted!r}: run python scripts/fpga.py jtag to list them"
        )
    with_fpga = [cable for cable in cables if cable.fpga_index()]
    if len(with_fpga) == 1:
        return with_fpga[0]
    if len(cables) == 1:
        return cables[0]
    raise UserError(
        "more than one cable: choose one with --cable (python scripts/fpga.py jtag lists them)"
    )


def cmd_program(args) -> int:
    project = resolve_project(args.project)
    sof = project.sof
    if not sof.is_file():
        raise UserError(
            f"{rel(sof)} does not exist yet."
            f" Build first: python scripts/fpga.py build {args.project}"
        )
    newer = [
        s for s in project.sources() if (project.dir / s).stat().st_mtime > sof.stat().st_mtime
    ]
    if newer:
        print(f"warning: changed since the last build: {', '.join(newer)}.")
        print("         The board will get the OLD design. Build again to include the change.")
    installs = find_quartus_installs()
    cable_name, index = args.cable, args.index
    if args.dry_run:
        index = index or FPGA_INDEX
    elif cable_name is None or index is None:
        cables, _raw = scan_jtag(installs)
        cable = pick_cable(cables, cable_name)
        describe_chain(cable)
        cable_name = cable.name
        index = index or cable.fpga_index()
        if index is None:
            raise UserError(
                f"no {DEVICE[:7]} on {cable.name}'s chain."
                " Is this a DE10-Nano? (--index N to force)"
            )
        if index != FPGA_INDEX:
            print(
                f"note: the FPGA is @{index} on this chain"
                f" (on a DE10-Nano it is normally @{FPGA_INDEX})."
            )
    quartus = choose_quartus(installs) or (installs[0] if installs else None)
    if quartus:
        pgm = quartus.tool("quartus_pgm")
    elif args.dry_run:
        pgm = "quartus_pgm"
    else:
        raise UserError(f"Quartus Prime not found (quartus_pgm comes with it): {INSTALL_GUIDE}")
    sof_name = sof.relative_to(project.dir).as_posix()
    cmd = program_command(pgm, sof_name, cable_name, index)
    print(f"Programming device @{index}: {shown(cmd)}")
    if args.dry_run:
        print("(--dry-run: nothing was sent to the board)")
        return 0
    if subprocess.run(cmd, cwd=project.dir).returncode != 0:
        print("Programming FAILED. Run python scripts/fpga.py jtag and read the gotchas in")
        print("docs/procedures/gotchas.md (the USB port, the driver, the device index).")
        return 1
    print("Done. The design runs until the power goes off: a .sof only lives in the FPGA's memory.")
    return 0


def cmd_doctor(args) -> int:
    missing: list[str] = []

    def show(state, what: str, fix: str = "") -> None:
        tag = {True: " ok ", False: "MISS", None: " -- "}[state]
        print(f"  [{tag}] {what}")
        if state is False:
            missing.append(what.split(":")[0])
            if fix:
                print(f"         fix: {fix}")

    print("Tools for the DE10-Nano flow ([ ok ] found, [MISS] needed, [ -- ] optional)\n")
    py_ok = sys.version_info >= (3, 10)
    show(py_ok, f"Python {platform.python_version()}", "install Python 3.12")
    git = first_line(["git", "--version"])
    show(bool(git), f"git: {git or 'not found'}", "install Git")
    gh = first_line(["gh", "--version"])
    show(True if gh else None, f"GitHub CLI: {gh or 'not found (only needed to publish)'}")

    for name in ("iverilog", "vvp"):
        tool = find_tool(name)
        line = first_line([tool, "-V"]) if tool else None
        version = re.search(r"version\s+(\S+)", line or "")
        label = f"Icarus Verilog {version[1]}" if version else "not found"
        show(bool(tool), f"{name}: {label}", f"install Icarus Verilog ({INSTALL_GUIDE})")
    gtkwave = find_tool("gtkwave")
    show(True if gtkwave else None, f"GTKWave (waveform viewer): {gtkwave or 'not found'}")

    installs = find_quartus_installs()
    if not installs:
        print("  [ -- ] Quartus Prime: no install found")
    for quartus in installs:
        families = installed_families(quartus)
        has = FAMILY in families
        listed = ", ".join(families) if families else "could not ask it"
        print(
            f"  [{' ok ' if has else ' -- '}] Quartus {quartus.version} at {quartus.bin}: {listed}"
        )
    chosen = choose_quartus(installs)
    show(
        bool(chosen),
        f"Quartus with {FAMILY}: " + (f"{chosen.version}" if chosen else "none"),
        f"install Quartus Prime Lite with the Cyclone V device package ({INSTALL_GUIDE})",
    )

    if installs and jtagconfig_path(installs):
        try:
            cables, _raw = scan_jtag(installs)
        except UserError as error:
            cables = []
            print(f"  [ -- ] JTAG: {error}")
        boards = [cable for cable in cables if cable.fpga_index()]
        if boards:
            for cable in boards:
                show(True, f"Board: {cable.name}, FPGA at @{cable.fpga_index()}")
        else:
            show(None, "Board: not seen on JTAG (fine if it is not plugged in now)")
    print()
    if missing:
        print(f"Missing: {', '.join(missing)}. Step by step: {INSTALL_GUIDE}")
        return 1
    print("Everything needed is installed.")
    return 0


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(
        prog="fpga.py",
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")
    sub.add_parser("doctor", help="check the tools and the board connection")
    p = sub.add_parser("new", help="start projects/<name> from templates/blinky")
    p.add_argument("name")
    p = sub.add_parser("sim", help="run a project's self-checking testbenches")
    p.add_argument("project", nargs="?")
    p.add_argument("--all", action="store_true", help="every template and every project")
    p.add_argument("--waves", action="store_true", help="also write a .vcd waveform per testbench")
    p = sub.add_parser("build", help="simulate, then compile with Quartus and check timing")
    p.add_argument("project")
    p.add_argument(
        "--skip-sim", action="store_true", help="compile without running the testbenches"
    )
    sub.add_parser("jtag", help="list the JTAG cables and the devices on each chain")
    p = sub.add_parser("program", help="load the project's .sof into the FPGA over JTAG")
    p.add_argument("project")
    p.add_argument("--cable", help="cable number or name, from: fpga.py jtag")
    p.add_argument(
        "--index", type=int, help=f"device position on the chain (DE10-Nano: {FPGA_INDEX})"
    )
    p.add_argument("--dry-run", action="store_true", help="show the command, do not run it")
    args = parser.parse_args(argv)
    handlers = {
        "doctor": cmd_doctor,
        "new": cmd_new,
        "sim": cmd_sim,
        "build": cmd_build,
        "jtag": cmd_jtag,
        "program": cmd_program,
    }
    try:
        return handlers[args.command](args)
    except UserError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
