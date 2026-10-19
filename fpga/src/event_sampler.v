// =============================================================================
// Project:       EHand Hardware-in-the-Loop Emulation Platform
// Module:        event_sampler
// Description:   Hardware Microsecond Timestamp & 20-channel GPIO Edge Sampler
// Target Device: Gowin GW5AT-138 (OrangePi MSOC)
// Specification: docs/research/fpga-event-sampler.md (Issue #14)
// =============================================================================

`timescale 1ns / 1ps

module event_sampler #(
    parameter CLK_FREQ_HZ   = 25_000_000, // 25 MHz system clock (40ns period)
    parameter PRESCALE_DIV  = 25,         // 25 cycles = 1.0 us
    parameter NUM_CHANNELS  = 20,         // 20 GPIO lines on MSOC 30PIN FPC
    parameter FIFO_DEPTH    = 2048,       // 2048 entries of 64-bit event frames
    parameter FIFO_AWIDTH   = 11          // 2^11 = 2048
)(
    input  wire                   clk,           // 25MHz system clock
    input  wire                   rst_n,         // Active-low asynchronous reset

    // -------------------------------------------------------------------------
    // Physical Pin Interface (MSOC 30PIN FPC Connector)
    // -------------------------------------------------------------------------
    input  wire [NUM_CHANNELS-1:0] gpio_pin_in,   // Input from target board
    output wire [NUM_CHANNELS-1:0] gpio_pin_out,  // Output to target board
    output wire [NUM_CHANNELS-1:0] gpio_pin_oe,   // Output enable (1=drive, 0=Hi-Z)

    // -------------------------------------------------------------------------
    // Host Register Bus (Synchronous MMIO, BAR2 compatible)
    // -------------------------------------------------------------------------
    input  wire [7:0]             reg_addr,      // Byte offset (0x00 to 0x3F)
    input  wire                   reg_wr_en,     // Write strobe
    input  wire [31:0]            reg_wr_data,   // Write data
    input  wire                   reg_rd_en,     // Read strobe
    output reg  [31:0]            reg_rd_data,   // Read data output

    // -------------------------------------------------------------------------
    // Interrupt / Status Output
    // -------------------------------------------------------------------------
    output wire                   irq_out        // Interrupt line to PCIe controller
);

    // =========================================================================
    // 1. Microsecond Timestamp Engine
    // =========================================================================
    reg [4:0]  prescale_cnt;
    wire       us_tick = (prescale_cnt == (PRESCALE_DIV - 1));
    reg [63:0] timestamp_us;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prescale_cnt <= 5'd0;
            timestamp_us <= 64'd0;
        end else begin
            if (us_tick) begin
                prescale_cnt <= 5'd0;
                timestamp_us <= timestamp_us + 64'd1;
            end else begin
                prescale_cnt <= prescale_cnt + 5'd1;
            end
        end
    end

    // =========================================================================
    // 2. Multi-stage Input Synchronizer & Edge Detection
    // =========================================================================
    reg [NUM_CHANNELS-1:0] gpio_sync_d0;
    reg [NUM_CHANNELS-1:0] gpio_sync_d1;
    reg [NUM_CHANNELS-1:0] gpio_sync_d2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gpio_sync_d0 <= {NUM_CHANNELS{1'b0}};
            gpio_sync_d1 <= {NUM_CHANNELS{1'b0}};
            gpio_sync_d2 <= {NUM_CHANNELS{1'b0}};
        end else begin
            gpio_sync_d0 <= gpio_pin_in;
            gpio_sync_d1 <= gpio_sync_d0;
            gpio_sync_d2 <= gpio_sync_d1;
        end
    end

    wire [NUM_CHANNELS-1:0] raw_rise = (~gpio_sync_d2) & gpio_sync_d1;
    wire [NUM_CHANNELS-1:0] raw_fall = gpio_sync_d2 & (~gpio_sync_d1);

    // =========================================================================
    // 3. Control & Configuration Registers
    // =========================================================================
    reg                     capture_enable;
    reg [NUM_CHANNELS-1:0]  gpio_out_reg;
    reg [NUM_CHANNELS-1:0]  gpio_oe_reg;
    reg                     overflow_flag;

    assign gpio_pin_out = gpio_out_reg;
    assign gpio_pin_oe  = gpio_oe_reg;

    // =========================================================================
    // 4. Multi-channel Edge Arbitration & Event Word Assembly
    // =========================================================================
    reg [NUM_CHANNELS-1:0] pending_rise;
    reg [NUM_CHANNELS-1:0] pending_fall;

    // Priority encoder: find lowest active bit in 20-bit vector
    function [4:0] get_first_set_bit;
        input [NUM_CHANNELS-1:0] vec;
        integer i;
        begin
            get_first_set_bit = 5'd0;
            for (i = NUM_CHANNELS - 1; i >= 0; i = i - 1) begin
                if (vec[i]) get_first_set_bit = i[4:0];
            end
        end
    endfunction

    wire has_pending_rise = (pending_rise != {NUM_CHANNELS{1'b0}});
    wire has_pending_fall = (pending_fall != {NUM_CHANNELS{1'b0}});
    wire has_pending_event = capture_enable && (has_pending_rise || has_pending_fall);

    wire        active_is_rise = has_pending_rise;
    wire [4:0]  active_channel = active_is_rise ? get_first_set_bit(pending_rise) :
                                                  get_first_set_bit(pending_fall);

    // 64-bit Event Frame Encoding (according to Issue #14 spec):
    // [63:32]: timestamp_us[31:0]
    // [31]:    overflow_flag
    // [30:28]: 3'b000 (reserved)
    // [27:24]: edge_type (0x1 = rising, 0x2 = falling)
    // [23:16]: channel_id (0 ~ 19)
    // [15:0]:  pin_snapshot (instantaneous debounced GPIO[15:0])
    wire [63:0] new_event_word = {
        timestamp_us[31:0],
        overflow_flag,
        3'b000,
        active_is_rise ? 4'h1 : 4'h2,
        {3'b000, active_channel},
        gpio_sync_d1[15:0]
    };

    // =========================================================================
    // 5. Hardware Event FIFO (2048 x 64-bit BSRAM)
    // =========================================================================
    reg [63:0] fifo_mem [0:FIFO_DEPTH-1];
    reg [FIFO_AWIDTH-1:0] wr_ptr;
    reg [FIFO_AWIDTH-1:0] rd_ptr;
    reg [FIFO_AWIDTH:0]   fifo_count; // 0 to 2048

    wire fifo_empty = (fifo_count == 0);
    wire fifo_full  = (fifo_count == FIFO_DEPTH);

    // FIFO read port
    wire [63:0] fifo_rdata = fifo_mem[rd_ptr];

    // FIFO pop handshake from host reading FIFO_DATA_LO
    wire fifo_pop_req = reg_rd_en && (reg_addr == 8'h14) && (!fifo_empty);
    wire fifo_push_req = has_pending_event && (!fifo_full);

    // Latched upper 32-bit of event frame for atomic 64-bit reading over 32-bit bus
    reg [31:0] latched_event_hi;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr           <= {FIFO_AWIDTH{1'b0}};
            rd_ptr           <= {FIFO_AWIDTH{1'b0}};
            fifo_count       <= {(FIFO_AWIDTH+1){1'b0}};
            overflow_flag    <= 1'b0;
            pending_rise     <= {NUM_CHANNELS{1'b0}};
            pending_fall     <= {NUM_CHANNELS{1'b0}};
            latched_event_hi <= 32'd0;
        end else begin
            // 1. Accumulate new raw edges
            if (capture_enable) begin
                pending_rise <= (pending_rise | raw_rise);
                pending_fall <= (pending_fall | raw_fall);
            end

            // 2. FIFO Push Handling
            if (has_pending_event) begin
                if (!fifo_full) begin
                    fifo_mem[wr_ptr] <= new_event_word;
                    wr_ptr <= wr_ptr + 1'b1;
                    if (active_is_rise)
                        pending_rise[active_channel] <= 1'b0;
                    else
                        pending_fall[active_channel] <= 1'b0;
                end else begin
                    // FIFO full overflow!
                    overflow_flag <= 1'b1;
                end
            end

            // 3. FIFO Pop Handling (Host reading FIFO_DATA_LO at 0x14)
            if (fifo_pop_req) begin
                latched_event_hi <= fifo_rdata[63:32];
                rd_ptr <= rd_ptr + 1'b1;
            end

            // 4. FIFO Count Tracker
            case ({fifo_push_req, fifo_pop_req})
                2'b10: fifo_count <= fifo_count + 1'b1;
                2'b01: fifo_count <= fifo_count - 1'b1;
                default: fifo_count <= fifo_count; // Both or neither
            endcase

            // 5. Host Register Writes (Clear FIFO / Reset)
            if (reg_wr_en && (reg_addr == 8'h1C)) begin
                if (reg_wr_data[0]) begin // Reset FIFO & clear overflow
                    wr_ptr        <= {FIFO_AWIDTH{1'b0}};
                    rd_ptr        <= {FIFO_AWIDTH{1'b0}};
                    fifo_count    <= {(FIFO_AWIDTH+1){1'b0}};
                    overflow_flag <= 1'b0;
                    pending_rise  <= {NUM_CHANNELS{1'b0}};
                    pending_fall  <= {NUM_CHANNELS{1'b0}};
                end
            end
        end
    end

    // High watermark interrupt (assert when FIFO >= 75% full, i.e. 1536 entries)
    assign irq_out = (fifo_count >= 12'd1536) || overflow_flag;

    // =========================================================================
    // 6. Host Register Bus Read/Write Dispatch (BAR2 MMIO)
    // =========================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            capture_enable <= 1'b1; // Enabled by default
            gpio_out_reg   <= {NUM_CHANNELS{1'b0}};
            gpio_oe_reg    <= {NUM_CHANNELS{1'b0}};
            reg_rd_data    <= 32'd0;
        end else begin
            // Register Writes
            if (reg_wr_en) begin
                case (reg_addr)
                    8'h1C: begin // EVENT_FIFO_CTRL
                        capture_enable <= reg_wr_data[1];
                    end
                    8'h24: begin // GPIO_OUT_DATA
                        gpio_out_reg <= reg_wr_data[NUM_CHANNELS-1:0];
                    end
                    8'h28: begin // GPIO_OUT_OE
                        gpio_oe_reg  <= reg_wr_data[NUM_CHANNELS-1:0];
                    end
                    default: ;
                endcase
            end

            // Register Reads
            if (reg_rd_en) begin
                case (reg_addr)
                    8'h00: reg_rd_data <= 32'h4548414E; // Magic: "EHAN"
                    8'h04: reg_rd_data <= 32'h00010014; // Ver 1.0, 20 channels (0x14)
                    8'h08: reg_rd_data <= timestamp_us[31:0];  // Current Timestamp Low
                    8'h0C: reg_rd_data <= timestamp_us[63:32]; // Current Timestamp High
                    8'h10: reg_rd_data <= {fifo_full | overflow_flag, fifo_empty, 14'd0, 4'd0, fifo_count};
                    8'h14: reg_rd_data <= fifo_rdata[31:0];    // Event Word Low (Pops FIFO)
                    8'h18: reg_rd_data <= latched_event_hi;   // Latched Event Word High
                    8'h1C: reg_rd_data <= {30'd0, capture_enable, 1'b0};
                    8'h20: reg_rd_data <= {12'd0, gpio_sync_d1}; // Live debounced GPIO levels
                    8'h24: reg_rd_data <= {12'd0, gpio_out_reg};
                    8'h28: reg_rd_data <= {12'd0, gpio_oe_reg};
                    default: reg_rd_data <= 32'hDEADBEEF;
                endcase
            end
        end
    end

endmodule
