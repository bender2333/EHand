`timescale 1ns/1ps

module ap_top_tb;
    reg i_clk = 1'b0;
    reg i_rst_n = 1'b0;

    ap_top dut (
        .i_clk(i_clk),
        .i_rst_n(i_rst_n)
    );

    always #5 i_clk = ~i_clk;

    initial begin
        #20 i_rst_n = 1'b1;
        #40;
        $display("AP_TOP_SMOKE_PASS");
        $finish;
    end
endmodule
