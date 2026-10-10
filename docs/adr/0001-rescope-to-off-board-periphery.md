# EHand plays the Target Board's off-board world; AgentProbe v0 is archived

The v0 docs aimed at a two-board self-hosting rig (Golden AgentProbe verifying DUT AgentProbe), SPI-first Mock, and a custom Zynq SoM baseboard with on-board CMSIS-DAP. None of it ran on hardware. We re-scoped (2026-10-10) to the user's own pain: an Agent can write protocol code but cannot check that it really talks. EHand now plays whatever sits outside an ordinary MCU board (serial peers, Modbus slaves on 485, NTC, switches and pulses) on an off-the-shelf Zynq-7020 dev board, and stays independent of the MCU family.

## Considered Options

- Keep self-hosting as the V1 North Star: rejected; it needs two custom boards before the first real evidence, and proves EHand on itself rather than on users' firmware.
- Off-the-shelf tools only (USB-serial + PC Modbus tool + logic analyser): rejected as the product; they cannot do bit-accurate timing, deliberate timing faults, or several Channels on one clock.

## Consequences

- Out of scope: anything on the Target Board (power, crystal, drive circuits, analogue front-ends), high-speed interfaces, flashing (external J-Link for now), replacing final bring-up on the real board.
- `archive/agentprobe-v0/` and tags `archive/agentprobe-main`, `archive/agentprobe-work-v01a` keep the old work for reference.
