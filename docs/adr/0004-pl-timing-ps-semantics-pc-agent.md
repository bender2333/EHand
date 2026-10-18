# Split: FPGA for timing, Host for protocol semantics, PC/Host for the Agent

On the Kunpeng AI Pro + OrangePi MSOC (GW5AT-138) platform, the FPGA owns everything that touches pins and must be clock-accurate: UART/485 transceive, DE direction timing, PWM and pulse output, switch inputs/outputs, sampling, hardware timestamps, timing Injections. Interconnect between Host and FPGA is PCIe Gen2 x4 (BAR0 MMIO / SGDMA). The Host (Kunpeng ARM64 running Linux) owns protocol meaning: Modbus slave register tables and replies, NTC temperature-to-voltage, applying the Virtual Periphery and Injections, assembling and layering the Timeline, and serving the PC / local Agent over Ethernet or local CLI (`ehand` command-line tool, JSON out; MCP can wrap it later).

## Consequences

- Linux on the Host trades hard real-time for development speed; anything needing µs determinism must live in the FPGA. Communication between Host and FPGA goes over PCIe Gen2 x4 with low latency.
