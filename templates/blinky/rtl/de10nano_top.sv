// Top level for the DE10-Nano. The port names are the board's signal names; blinky.qsf ties each
// one to its pin, and docs/de10nano_reference.md says where every pin number comes from.
//
//   KEY0 held  -> the counter resets to 0
//   KEY1 held  -> LED[3:0] show the four slide switches (a quick check that every input works)
//   otherwise  -> LED[7:0] show a binary count, two steps a second
`default_nettype none

module de10nano_top #(
    parameter int CLK_HZ = 50_000_000  // FPGA_CLK1_50 is a 50 MHz clock
) (
    input  wire        FPGA_CLK1_50,
    input  wire  [1:0] KEY,  // push buttons KEY0 and KEY1: 0 while pressed
    input  wire  [3:0] SW,   // slide switches SW0..SW3
    output logic [7:0] LED   // 1 = LED on
);
    wire clk = FPGA_CLK1_50;

    // Buttons and switches change when a person touches them, not in step with the clock.
    // Two flip-flops in a row give a clean copy that changes only on a clock edge.
    logic [1:0] key_meta, key_sync;
    logic [3:0] sw_meta, sw_sync;
    always_ff @(posedge clk) begin
        key_meta <= KEY;
        key_sync <= key_meta;
        sw_meta  <= SW;
        sw_sync  <= sw_meta;
    end

    wire reset = !key_sync[0];
    wire show_switches = !key_sync[1];

    logic [7:0] count;
    blinky #(
        .CLK_HZ (CLK_HZ),
        .STEP_HZ(2)
    ) u_blinky (
        .clk  (clk),
        .reset(reset),
        .count(count)
    );

    assign LED = show_switches ? {4'b0000, sw_sync} : count;
endmodule

`default_nettype wire
