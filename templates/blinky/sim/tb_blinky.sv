// Self-checking testbench for the blinky template. It prints PASS or FAIL lines, and
// `python scripts/fpga.py sim blinky` reads them (add --waves for a .vcd to open in GTKWave).
//
// The trick that makes it fast: CLK_HZ is set to 20, so a counter step takes 10 clock cycles
// instead of 25 million. Same design, same logic, a much shorter wait.
`timescale 1ns / 1ps
`default_nettype none

module tb_blinky;
    localparam int CLK_HZ = 20;
    localparam int TICKS = CLK_HZ / 2;  // cycles per counter step (de10nano_top uses STEP_HZ = 2)

    logic       clk = 1'b0;
    logic [1:0] key = 2'b11;  // nothing pressed (a pressed button reads 0)
    logic [3:0] sw = 4'b0000;
    wire  [7:0] led;
    int checks = 0;
    int errors = 0;

    de10nano_top #(.CLK_HZ(CLK_HZ)) dut (
        .FPGA_CLK1_50(clk),
        .KEY(key),
        .SW(sw),
        .LED(led)
    );

    always #10 clk = ~clk;  // 20 ns period: 50 MHz, like the board

    task automatic cycles(input int n);  // wait n rising edges, then let the outputs settle
        repeat (n) @(posedge clk);
        #1;
    endtask

    task automatic expect_led(input logic [7:0] want, input string what);
        checks++;
        if (led !== want) begin
            errors++;
            $display("FAIL: %s: LED = %b, expected %b (at %0d ns)", what, led, want, $time);
        end
    endtask

    initial begin
        if ($test$plusargs("waves")) begin
            $dumpfile("tb_blinky.vcd");
            $dumpvars(0, tb_blinky);
        end

        // 1. Hold KEY0: the counter is held at 0.
        key[0] = 1'b0;
        cycles(5);
        expect_led(8'd0, "KEY0 held (reset)");

        // 2. Let go of KEY0. Two cycles to pass the synchroniser, then one step every TICKS.
        key[0] = 1'b1;
        cycles(2);
        for (int step = 1; step <= 5; step++) begin
            cycles(TICKS);
            expect_led(step[7:0], "counting after reset");
        end

        // 3. Hold KEY1: the LEDs show the switches instead (after the synchroniser's delay).
        sw = 4'b1010;
        key[1] = 1'b0;
        cycles(3);
        expect_led(8'b0000_1010, "KEY1 held, switches 1010");
        sw = 4'b1100;
        cycles(3);
        expect_led(8'b0000_1100, "KEY1 held, switches 1100");

        // 4. Let go of KEY1: back to the count, which kept running underneath.
        key[1] = 1'b1;
        cycles(3);
        expect_led(8'd5, "KEY1 released, count still 5");
        cycles(TICKS);
        expect_led(8'd6, "the count carried on");

        if (errors == 0) $display("PASS: tb_blinky, %0d checks", checks);
        else $display("FAIL: tb_blinky, %0d of %0d checks failed", errors, checks);
        $finish;
    end

    initial begin  // a testbench that hangs has failed
        #1_000_000;
        $display("FAIL: tb_blinky timed out");
        $finish;
    end
endmodule

`default_nettype wire
