// blinky: an 8-bit counter that steps STEP_HZ times a second.
// Shown on the LEDs it is a binary count: LED[0] changes every step, LED[1] every two steps, ...
`default_nettype none

module blinky #(
    parameter int CLK_HZ  = 50_000_000,  // the frequency of clk
    parameter int STEP_HZ = 2            // counter steps per second
) (
    input  wire        clk,
    input  wire        reset,  // synchronous, active high: count goes back to 0
    output logic [7:0] count
);
    localparam int TICKS = CLK_HZ / STEP_HZ;  // clock cycles per step
    localparam int W = $clog2(TICKS + 1);     // bits needed to count to TICKS - 1

    logic [W-1:0] ticks;

    always_ff @(posedge clk) begin
        if (reset) begin
            ticks <= '0;
            count <= '0;
        end else if (ticks == TICKS - 1) begin
            ticks <= '0;
            count <= count + 8'd1;
        end else begin
            ticks <= ticks + 1'b1;
        end
    end
endmodule

`default_nettype wire
