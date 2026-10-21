# Timing constraints for the Quartus Timing Analyzer.

# FPGA_CLK1_50 (PIN_V11) is a 50 MHz clock input: one cycle every 20 ns. Without this line Quartus
# assumes 1 GHz and reports failures that are not real, or checks nothing at all.
create_clock -name FPGA_CLK1_50 -period 20.000 [get_ports {FPGA_CLK1_50}]

# Clocks made by PLLs (none yet) and the clock's own jitter.
derive_pll_clocks
derive_clock_uncertainty

# Buttons and switches change whenever a person touches them; the RTL passes them through two
# flip-flops before using them. The LEDs are read by eyes. No timing relationship to check.
set_false_path -from [get_ports {KEY[*] SW[*]}]
set_false_path -to [get_ports {LED[*]}]
