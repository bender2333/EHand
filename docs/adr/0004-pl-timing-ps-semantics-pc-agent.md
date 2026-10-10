# Split: PL for timing, PS for protocol semantics, PC for the Agent

On the Zynq-7020, the PL owns everything that touches pins and must be clock-accurate: UART/485 transceive, DE direction timing, PWM and pulse output, switch inputs/outputs, sampling, hardware timestamps, timing Injections. The PS (ARM, Linux) owns protocol meaning: Modbus slave register tables and replies, NTC temperature-to-voltage, applying the Virtual Periphery and Injections, assembling and layering the Timeline, and serving the PC over Ethernet. The PC side is the `ehand` command-line tool the Agent calls (JSON out); MCP can wrap it later.

## Consequences

- Linux on the PS trades hard real-time for development speed; anything needing µs determinism must live in the PL. If a later physical-process model needs a hard real-time loop, run it bare-metal on CPU1 (AMP) rather than moving it to Linux.
