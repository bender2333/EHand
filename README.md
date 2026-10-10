# EHand

**Real hardware feedback for embedded-coding Agents.**

Wire an MCU board (minimal system or dev board) to EHand once. From then on the Agent declares what sits outside the board (which pins, which protocol, which device on the other end) and EHand plays those devices with real electrical signals, injects faults on request, and returns a time-aligned record of both sides so the Agent can judge whether its firmware really works.

V1 peripherals: serial peer, Modbus RTU slave(s) on RS485, NTC temperature (analogue voltage), switch and pulse sources. Hardware: Alientek (正点原子) Zynq-7020 dev board. Flashing stays on an external J-Link.

- Domain language: [`CONTEXT.md`](CONTEXT.md)
- Decisions: [`docs/adr/`](docs/adr/)
- Previous iteration (AgentProbe v0): [`archive/`](archive/)
