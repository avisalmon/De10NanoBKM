"""Pin numbers are where a hardware project goes wrong silently: a wrong pin compiles cleanly and
then does nothing, or drives something it should not. So every pin in the template's .qsf must
match docs/de10nano_reference.md (which says where each number comes from), and every port of
the top level must have a pin."""

import re
from pathlib import Path

from scripts import fpga

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "docs" / "de10nano_reference.md"
PIN_ROW = re.compile(
    r"^\|\s*`([A-Za-z0-9_\[\]]+)`\s*\|\s*`(PIN_[A-Z0-9]+)`\s*\|\s*([^|]+?)\s*\|", re.M
)
PORT = re.compile(
    r"^\s*(input|output|inout)\s+(?:wire|logic|reg|\s)*(?:\[(\d+):(\d+)\])?\s*(\w+)", re.M
)


def reference_rows():
    return PIN_ROW.findall(REFERENCE.read_text(encoding="utf-8"))


def template_settings():
    return fpga.load_project(fpga.TEMPLATE).settings()


def test_the_reference_pin_table_is_there_without_duplicates():
    rows = reference_rows()
    signals = [signal for signal, _pin, _io in rows]
    pins = [pin for _signal, pin, _io in rows]
    assert len(rows) >= 15
    assert len(set(signals)) == len(signals), "a signal is listed twice"
    assert len(set(pins)) == len(pins), "two signals claim the same pin"


def test_the_template_targets_the_de10_nano_fpga():
    settings = template_settings()
    assert settings.get("FAMILY") == "Cyclone V"
    assert settings.get("DEVICE") == "5CSEBA6U23I7"
    assert "5CSEBA6U23I7" in REFERENCE.read_text(encoding="utf-8")


def test_every_pin_in_the_template_matches_the_reference():
    reference = {signal: (pin, io) for signal, pin, io in reference_rows()}
    settings = template_settings()
    assert settings.pins, "the template assigns no pins"
    for signal, pin in settings.pins.items():
        assert signal in reference, f"{signal} is in the .qsf but not in {REFERENCE.name}"
        assert pin == reference[signal][0], (
            f"{signal}: .qsf {pin}, reference {reference[signal][0]}"
        )
        assert settings.io_standards.get(signal) == reference[signal][1], f"{signal}: I/O standard"


def top_level_ports(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    header = text[text.index("module de10nano_top") : text.index(");")]
    names = set()
    for _direction, msb, lsb, name in PORT.findall(header):
        if msb:
            low, high = sorted((int(msb), int(lsb)))
            names |= {f"{name}[{i}]" for i in range(low, high + 1)}
        else:
            names.add(name)
    return names


def test_every_port_of_the_top_level_has_a_pin_and_nothing_else_does():
    """Quartus puts an unassigned pin wherever it likes. On a real board that can mean driving a
    pin that something else is driving too."""
    ports = top_level_ports(fpga.TEMPLATE / "rtl" / "de10nano_top.sv")
    assert ports == set(template_settings().pins)


def test_the_clock_constraint_matches_the_50_mhz_clock():
    sdc = (fpga.TEMPLATE / "blinky.sdc").read_text(encoding="utf-8")
    assert re.search(
        r"create_clock\s+-name\s+\S+\s+-period\s+20(\.0+)?\s+\[get_ports\s+\{?FPGA_CLK1_50\}?\]",
        sdc,
    )


def docs_and_skills():
    yield from ROOT.glob("*.md")
    for folder in ("docs", ".claude", "templates", "projects"):
        yield from (ROOT / folder).rglob("*.md")


def test_every_programming_command_in_the_docs_targets_device_2():
    """@1 is the HPS. A .sof sent there fails, and the error does not say why."""
    found = 0
    for path in docs_and_skills():
        for match in re.finditer(r"\.sof@(\d+)", path.read_text(encoding="utf-8")):
            found += 1
            assert match[1] == "2", f"{path.relative_to(ROOT)}: .sof@{match[1]}"
    assert found >= 2


def test_the_reference_says_where_its_facts_come_from():
    text = REFERENCE.read_text(encoding="utf-8")
    assert "## Sources" in text
    assert len(re.findall(r"https://", text[text.index("## Sources") :])) >= 3
