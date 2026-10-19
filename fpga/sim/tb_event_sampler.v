`timescale 1ns / 1ps

module tb_event_sampler;

    reg clk;
    reg rst_n;
    reg [19:0] gpio_pin_in;
    wire [19:0] gpio_pin_out;
    wire [19:0] gpio_pin_oe;

    reg [7:0] reg_addr;
    reg reg_wr_en;
    reg [31:0] reg_wr_data;
    reg reg_rd_en;
    wire [31:0] reg_rd_data;
    wire irq_out;

    // Instantiate Unit Under Test
    event_sampler #(
        .CLK_FREQ_HZ(25_000_000),
        .PRESCALE_DIV(25),
        .NUM_CHANNELS(20),
        .FIFO_DEPTH(2048),
        .FIFO_AWIDTH(11)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .gpio_pin_in(gpio_pin_in),
        .gpio_pin_out(gpio_pin_out),
        .gpio_pin_oe(gpio_pin_oe),
        .reg_addr(reg_addr),
        .reg_wr_en(reg_wr_en),
        .reg_wr_data(reg_wr_data),
        .reg_rd_en(reg_rd_en),
        .reg_rd_data(reg_rd_data),
        .irq_out(irq_out)
    );

    // 25MHz Clock generator (period = 40ns, 20ns high / 20ns low)
    always #20 clk = ~clk;

    // Bus read helper task
    task bus_read(input [7:0] addr, output [31:0] data);
        begin
            @(posedge clk);
            reg_addr <= addr;
            reg_rd_en <= 1'b1;
            reg_wr_en <= 1'b0;
            @(posedge clk);
            #1;
            data = reg_rd_data;
            reg_rd_en <= 1'b0;
        end
    endtask

    // Bus write helper task
    task bus_write(input [7:0] addr, input [31:0] data);
        begin
            @(posedge clk);
            reg_addr <= addr;
            reg_wr_data <= data;
            reg_wr_en <= 1'b1;
            reg_rd_en <= 1'b0;
            @(posedge clk);
            reg_wr_en <= 1'b0;
        end
    endtask

    reg [31:0] rdata;
    reg [31:0] rdata_hi;

    initial begin
        $display("=== STARTING EVENT_SAMPLER SIMULATION ===");
        clk = 0;
        rst_n = 0;
        gpio_pin_in = 20'b0;
        reg_addr = 8'b0;
        reg_wr_en = 0;
        reg_wr_data = 32'b0;
        reg_rd_en = 0;

        // Reset pulse
        #100;
        rst_n = 1;
        #100;

        // 1. Check Magic & Version registers
        bus_read(8'h00, rdata);
        $display("[SIM] Read Magic 0x00: 0x%08X", rdata);
        if (rdata !== 32'h4548414E) begin
            $display("ERROR: Magic mismatch! Expected 0x4548414E, got 0x%08X", rdata);
            $fatal(1);
        end

        bus_read(8'h04, rdata);
        $display("[SIM] Read Version 0x04: 0x%08X", rdata);
        if (rdata !== 32'h00010014) begin
            $display("ERROR: Version mismatch! Expected 0x00010014, got 0x%08X", rdata);
            $fatal(1);
        end

        // 2. Wait for 5 us (5 * 25 = 125 clock cycles = 5000ns)
        #5000;
        bus_read(8'h08, rdata);
        $display("[SIM] Read Timestamp Low 0x08: %0d us", rdata);
        if (rdata < 4 || rdata > 7) begin
            $display("ERROR: Timestamp out of expected range (~5us): %0d", rdata);
            $fatal(1);
        end

        // 3. Test GPIO Edge Capture: Pulse Channel 0 (Pin 0)
        $display("[SIM] Injecting Rising Edge on Channel 0...");
        @(posedge clk);
        gpio_pin_in[0] <= 1'b1;
        #200; // Keep high for 5 cycles

        // Check FIFO Status (Offset 0x10)
        bus_read(8'h10, rdata);
        $display("[SIM] FIFO Status after CH0 rise: 0x%08X (Count=%0d)", rdata, rdata[15:0]);
        if (rdata[15:0] !== 1) begin
            $display("ERROR: Expected FIFO count = 1, got %0d", rdata[15:0]);
            $fatal(1);
        end

        // Pop event word
        bus_read(8'h14, rdata);    // Low 32 bits
        bus_read(8'h18, rdata_hi); // High 32 bits
        $display("[SIM] Event CH0 popped: LO=0x%08X, HI=0x%08X", rdata, rdata_hi);
        // Verify channel = 0, edge_type = 1 (rising)
        if (rdata[27:24] !== 4'h1 || rdata[20:16] !== 5'd0) begin
            $display("ERROR: Expected edge_type=1, channel=0! Got edge_type=%0h, channel=%0d", rdata[27:24], rdata[20:16]);
            $fatal(1);
        end

        // 4. Test Multi-channel Simultaneous Edges: CH1 and CH2 toggle together
        $display("[SIM] Injecting simultaneous edges: CH1 rise, CH2 rise...");
        @(posedge clk);
        gpio_pin_in[1] <= 1'b1;
        gpio_pin_in[2] <= 1'b1;
        #400;

        bus_read(8'h10, rdata);
        $display("[SIM] FIFO Status after simultaneous CH1 & CH2 rise: Count=%0d", rdata[15:0]);
        if (rdata[15:0] !== 2) begin
            $display("ERROR: Expected FIFO count = 2, got %0d", rdata[15:0]);
            $fatal(1);
        end

        // Pop first event (should be CH1)
        bus_read(8'h14, rdata);
        $display("[SIM] Popped 1st event: Channel=%0d, EdgeType=%0d", rdata[20:16], rdata[27:24]);
        if (rdata[20:16] !== 5'd1 || rdata[27:24] !== 4'h1) begin
            $display("ERROR: 1st event mismatch!");
            $fatal(1);
        end

        // Pop second event (should be CH2)
        bus_read(8'h14, rdata);
        $display("[SIM] Popped 2nd event: Channel=%0d, EdgeType=%0d", rdata[20:16], rdata[27:24]);
        if (rdata[20:16] !== 5'd2 || rdata[27:24] !== 4'h1) begin
            $display("ERROR: 2nd event mismatch!");
            $fatal(1);
        end

        // 5. Test FIFO Reset
        $display("[SIM] Testing FIFO Reset via Control register 0x1C...");
        bus_write(8'h1C, 32'h00000001); // Bit 0 = clear
        #100;
        bus_read(8'h10, rdata);
        $display("[SIM] FIFO Status after clear: 0x%08X (empty=%0b)", rdata, rdata[30]);
        if (rdata[30] !== 1'b1 || rdata[15:0] !== 16'd0) begin
            $display("ERROR: FIFO should be empty after clear!");
            $fatal(1);
        end

        $display("=== ALL EVENT_SAMPLER SIMULATION CHECKS PASSED SUCCESSFULLY! ===");
        $finish;
    end

endmodule
