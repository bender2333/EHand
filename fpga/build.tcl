# =============================================================================
# Gowin EDA Tcl Script for EHand GW5AT-138 Sampler + PCIe Base
# Run on Windows: gw_sh.exe build.tcl
# =============================================================================

set_device GW5AT-LV138PG484AC1/I0 -device_version B

# Source Files
add_file -type verilog src/arb/arbiter_encryption.v
add_file -type verilog src/gowin_pll/gowin_pll.v
add_file -type verilog src/include/top_define.v
add_file -type verilog src/pcie/tlp_dec_encrypt.v
add_file -type verilog src/serdes/pcie_controller/pcie_controller.v
add_file -type verilog src/serdes/serdes.v
add_file -type verilog src/top.v
add_file -type verilog src/event_sampler.v

# Constraints
add_file -type cst src/ehand_gpio.cst
add_file -type sdc src/pcie_dma_demo.sdc

# Configuration Options
set_option -top_module top
set_option -output_base_name ehand_sampler

# Synthesize
run syn

# Place & Route
run pnr
