"""scripts/fpga.py drives the whole flow. These tests pin down the parts that are easy to get
subtly wrong: which Quartus gets used, which device on the JTAG chain gets the bitstream, what
the .qsf says, and whether a failing testbench is really reported as a failure."""

import os
from pathlib import Path

import pytest

from scripts import fpga

HAVE_ICARUS = bool(fpga.find_tool("iverilog") and fpga.find_tool("vvp"))
# Skipped on a computer without Icarus Verilog, but never in CI: there a skip would hide a gap.
needs_icarus = pytest.mark.skipif(
    not HAVE_ICARUS and not os.environ.get("CI"), reason="Icarus Verilog is not installed"
)

# The shape of what `jtagconfig` prints with a DE10-Nano plugged in: the HPS first, the FPGA
# second (the order community guides show). The IDCODEs are placeholders in the right format,
# not values read from a board; the parser only needs the names.
DE10_NANO_CHAIN = """\
1) DE-SoC [USB-1]
  4BA00477   SOCVHPS
  02D020DD   5CSEBA6(.|ES)/5CSEBA6ES/..

"""


# ---------------------------------------------------------------- choosing Quartus


def test_versions_sort_by_number_not_alphabetically():
    versions = ["9.1", "23.1std", "17.1", "unknown", "24.1std"]
    assert sorted(versions, key=fpga.version_key) == [
        "unknown",
        "9.1",
        "17.1",
        "23.1std",
        "24.1std",
    ]


@pytest.mark.parametrize(
    "path, version",
    [
        ("C:/intelFPGA_lite/17.1/quartus/bin64", "17.1"),
        ("/home/me/altera_lite/25.1std/quartus/bin", "25.1std"),
        ("/usr/local/bin", "unknown"),
    ],
)
def test_the_version_is_read_from_the_install_folder(path, version):
    assert fpga.version_from_path(Path(path)) == version


def test_the_family_list_is_read_from_the_tcl_answer():
    assert fpga.parse_family_list("{Cyclone V} {MAX 10} Arria\n") == [
        "Cyclone V",
        "MAX 10",
        "Arria",
    ]
    assert fpga.parse_family_list("{MAX 10}") == ["MAX 10"]


def installs(*specs):
    found = [fpga.Quartus(Path(f"/fake/{v}/quartus/bin"), v, families) for v, families in specs]
    return sorted(found, key=lambda q: fpga.version_key(q.version), reverse=True)


def test_the_newest_quartus_that_knows_cyclone_v_is_chosen():
    found = installs(
        ("17.1", ["MAX 10"]), ("23.1std", ["Cyclone V", "MAX 10"]), ("24.1std", ["MAX 10"])
    )
    assert fpga.choose_quartus(found).version == "23.1std"


def test_a_quartus_without_cyclone_v_is_never_chosen():
    """The owner's own computer had exactly this: Quartus 17.1 Lite with only MAX 10 installed."""
    assert fpga.choose_quartus(installs(("17.1", ["MAX 10"]))) is None
    assert fpga.choose_quartus([]) is None


# ---------------------------------------------------------------- JTAG and programming


def test_the_fpga_is_device_2_on_the_de10_nano_chain():
    (cable,) = fpga.parse_jtagconfig(DE10_NANO_CHAIN)
    assert cable.name == "DE-SoC [USB-1]"
    assert cable.devices[0] == ("4BA00477", "SOCVHPS")
    assert cable.fpga_index() == 2 == fpga.FPGA_INDEX


def test_no_hardware_means_no_cables():
    assert fpga.parse_jtagconfig("No JTAG hardware available\n") == []


def test_a_chain_without_the_fpga_has_no_fpga_index():
    (cable,) = fpga.parse_jtagconfig("1) USB-Blaster [USB-0]\n  031050DD   10M50DA(.|ES)/10M50DC\n")
    assert cable.fpga_index() is None


def test_the_program_command_sends_the_sof_to_device_2():
    cmd = fpga.program_command("quartus_pgm", "output_files/blinky.sof", "DE-SoC [USB-1]", 2)
    assert cmd == [
        "quartus_pgm", "-m", "jtag", "-c", "DE-SoC [USB-1]", "-o", "p;output_files/blinky.sof@2"
    ]  # fmt: skip


def test_program_refuses_without_a_bitstream(tmp_path, capsys):
    project = fpga.new_project("unbuilt", dest_root=tmp_path)
    assert fpga.main(["program", str(project), "--dry-run"]) == 1
    assert "Build first" in capsys.readouterr().err


def test_program_dry_run_shows_the_command_and_touches_nothing(tmp_path, capsys):
    project = fpga.new_project("built", dest_root=tmp_path)
    (project / "output_files").mkdir()
    (project / "output_files" / "built.sof").write_bytes(b"not a real bitstream")
    assert fpga.main(["program", str(project), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "p;output_files/built.sof@2" in out and "nothing was sent" in out


# ---------------------------------------------------------------- the .qsf and the reports


def test_the_template_qsf_is_read():
    project = fpga.load_project(fpga.TEMPLATE)
    settings = project.settings()
    assert project.revision == "blinky"
    assert settings.get("FAMILY") == fpga.FAMILY
    assert settings.get("DEVICE") == fpga.DEVICE
    assert settings.get("TOP_LEVEL_ENTITY") == "de10nano_top"
    assert project.sources() == ["rtl/blinky.sv", "rtl/de10nano_top.sv"]
    assert all((project.dir / source).is_file() for source in project.sources())
    assert project.sof == project.dir / "output_files" / "blinky.sof"


def test_qsf_lines_are_read_the_way_quartus_writes_them(tmp_path):
    qsf = tmp_path / "x.qsf"
    qsf.write_text(
        "# a comment\n"
        'set_global_assignment -name FAMILY "Cyclone V"\n'
        "set_global_assignment -name PARTITION_COLOR 16764057 -section_id Top\n"
        'set_global_assignment -name MIN_CORE_JUNCTION_TEMP "-40"\n'
        "set_location_assignment PIN_W15 -to LED[0]\n"
        'set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to "LED[0]"\n',
        encoding="utf-8",
    )
    settings = fpga.read_qsf(qsf)
    assert settings.get("FAMILY") == "Cyclone V"
    assert settings.get("PARTITION_COLOR") == "16764057"
    assert settings.get("MIN_CORE_JUNCTION_TEMP") == "-40"
    assert settings.pins == {"LED[0]": "PIN_W15"}
    assert settings.io_standards == {"LED[0]": "3.3-V LVTTL"}


STA_SUMMARY = """\
------------------------------------------------------------
Timing Analyzer Summary
------------------------------------------------------------

Type  : Slow 1100mV 85C Model Setup 'FPGA_CLK1_50'
Slack : 15.441
TNS   : 0.000

Type  : Slow 1100mV 85C Model Hold 'FPGA_CLK1_50'
Slack : 0.347
TNS   : 0.000

Type  : Fast 1100mV 0C Model Setup 'FPGA_CLK1_50'
Slack : -0.125
TNS   : -0.250
"""


def test_the_worst_slack_is_found_in_the_timing_summary():
    slacks = fpga.parse_slacks(STA_SUMMARY)
    assert len(slacks) == 3
    assert min(slacks, key=lambda item: item[1]) == (
        "Fast 1100mV 0C Model Setup 'FPGA_CLK1_50'",
        -0.125,
    )


def test_the_fit_summary_is_read():
    text = (
        "Fitter Status : Successful - Tue Oct 20 10:00:00 2026\n"
        "Family : Cyclone V\n"
        "Total pins : 15 / 314 ( 5 % )\n"
    )
    summary = fpga.parse_summary(text)
    assert summary["Fitter Status"].startswith("Successful")
    assert summary["Total pins"] == "15 / 314 ( 5 % )"


# Lines Quartus Prime 17.1 printed while compiling small test designs.
QUARTUS_LINES_SHOWN = [
    'Error (12006): Node instance "u_sub" instantiates undefined entity "sub".',
    "Critical Warning (169085): No exact pin location assignment(s) for 2 pins of 5 total pins.",
    '    Warning (15706): Node "ledx[0]" is assigned to location or region,'
    " but does not exist in design",
    "Error: Quartus Prime Analysis & Synthesis was unsuccessful. 1 error, 1 warning",
    "Info: Quartus Prime Fitter was successful. 0 errors, 8 warnings",
]
QUARTUS_LINES_HIDDEN = [
    "Error: Peak virtual memory: 4711 megabytes",
    "Error: Processing ended: Tue Oct 20 16:53:35 2026",
    "Error: Elapsed time: 00:00:12",
    "Error: Total CPU time (on all processors): 00:00:22",
    "Info (170137): Fitter placement was successful",
    "Warning (18236): Number of processors has not been specified",
]


def test_the_build_shows_errors_and_misnamed_pins_but_not_bookkeeping():
    assert all(fpga.worth_showing(line) for line in QUARTUS_LINES_SHOWN)
    assert not any(fpga.worth_showing(line) for line in QUARTUS_LINES_HIDDEN)


# ---------------------------------------------------------------- new projects


def test_a_new_project_is_a_renamed_copy_of_the_template(tmp_path):
    dest = fpga.new_project("my_counter", dest_root=tmp_path)
    names = {p.name for p in dest.iterdir()}
    assert {
        "my_counter.qpf",
        "my_counter.qsf",
        "my_counter.sdc",
        "rtl",
        "sim",
        "README.md",
    } <= names
    assert not any(name.startswith("blinky.") for name in names)
    assert "sim_build" not in names and "output_files" not in names
    project = fpga.load_project(dest)
    assert project.revision == "my_counter"
    assert project.settings().get("SDC_FILE") == "my_counter.sdc"
    assert project.sources() == fpga.load_project(fpga.TEMPLATE).sources()
    assert "my_counter" in (dest / "README.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "bad", ["", "My_Project", "1st", "my project", "../escape", "blinky-2", "a" * 42]
)
def test_unusable_project_names_are_refused(tmp_path, bad):
    with pytest.raises(fpga.UserError):
        fpga.new_project(bad, dest_root=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_an_existing_project_is_never_overwritten(tmp_path):
    fpga.new_project("mine", dest_root=tmp_path)
    work = tmp_path / "mine" / "rtl" / "blinky.sv"
    work.write_text("my work", encoding="utf-8")
    with pytest.raises(fpga.UserError):
        fpga.new_project("mine", dest_root=tmp_path)
    assert work.read_text(encoding="utf-8") == "my work"


# ---------------------------------------------------------------- simulation


@needs_icarus
def test_the_template_passes_its_own_testbench():
    results = fpga.simulate(fpga.load_project(fpga.TEMPLATE))
    assert results and all(result.passed for result in results), [r.log for r in results]


@needs_icarus
def test_the_sim_command_reports_pass_for_the_template(capsys):
    assert fpga.main(["sim", "blinky"]) == 0
    assert "PASS  templates/blinky/sim/tb_blinky" in capsys.readouterr().out


def project_with_testbench(tmp_path, name, body):
    dest = fpga.new_project("victim", dest_root=tmp_path)
    for tb in (dest / "sim").glob("tb_*.sv"):
        tb.unlink()
    (dest / "sim" / f"{name}.sv").write_text(body + "\n", encoding="utf-8")
    return fpga.load_project(dest)


@needs_icarus
@pytest.mark.parametrize(
    "body",
    [
        'module tb_bad; initial begin $display("FAIL: on purpose"); $finish; end endmodule',
        'module tb_bad; initial begin $display("PASS"); $display("FAIL: late"); $finish; end'
        " endmodule",
        "module tb_bad; initial $finish; endmodule",
        'module tb_bad; initial begin $display("PASS") $finish; end endmodule',
    ],
    ids=["prints-fail", "fail-after-pass", "says-nothing", "does-not-compile"],
)
def test_a_failing_testbench_is_reported_as_failing(tmp_path, body):
    (result,) = fpga.simulate(project_with_testbench(tmp_path, "tb_bad", body))
    assert not result.passed, result.log


@needs_icarus
def test_a_testbench_that_never_finishes_is_stopped(tmp_path):
    body = "module tb_hang; reg c = 0; always #5 c = ~c; endmodule"
    (result,) = fpga.simulate(project_with_testbench(tmp_path, "tb_hang", body), timeout=3)
    assert not result.passed and "still running" in result.log


@needs_icarus
def test_a_project_without_a_testbench_fails_the_sim_command(tmp_path, capsys):
    dest = fpga.new_project("untested", dest_root=tmp_path)
    for tb in (dest / "sim").glob("tb_*.sv"):
        tb.unlink()
    assert fpga.main(["sim", str(dest)]) == 1
    assert "no testbench" in capsys.readouterr().out


def test_doctor_runs_to_the_end_on_any_computer(capsys):
    assert fpga.main(["doctor"]) in (0, 1)
    out = capsys.readouterr().out
    assert "Quartus" in out and ("Everything needed is installed." in out or "Missing:" in out)
