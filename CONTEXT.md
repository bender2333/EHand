# EHand

EHand gives an embedded-coding Agent real hardware feedback: wired once to an MCU board, it plays the board's off-board world (communication peers and peripherals) with real electrical signals and reports everything it sees back to the Agent.

## Language

### Things on the bench

**Target Board**:
The user's MCU board under development (minimal system or dev board). EHand never models anything on it.
_Avoid_: DUT, external target, MCU (when the board is meant)

**EHand Board**:
The Kunpeng AI Pro + OrangePi MSOC board combination that runs EHand (Kunpeng ARM64 host + Gowin GW5AT-138 FPGA via PCIe).
_Avoid_: AgentProbe, Golden, probe

**Wiring**:
The fixed physical connection between Target Board pins and EHand Board pins, made once by a human.
_Avoid_: topology, routing

**Channel**:
One EHand-side pin group bound to a Target Board interface (a UART, a 485 bus, an ADC input, a GPIO).

### What EHand plays

**Peripheral Model**:
The behaviour EHand plays on a Channel: a Modbus slave, a serial peer, an NTC, a switch or pulse source.
_Avoid_: mock (as a noun for the whole system), simulator

**Virtual Periphery**:
The full declared set of Peripheral Models bound to Channels for one run.
_Avoid_: scenario (for this meaning), virtual board

**Injection**:
A runtime instruction that makes a Peripheral Model misbehave on purpose (wrong CRC, no reply, late reply, frame-gap violation, baud skew).
_Avoid_: fault (alone), error

### What EHand reports

**Timeline**:
The single time-aligned record of everything EHand observed and did on all Channels during a run: Target Board traffic, Peripheral Model replies, Injections, line-level timing.
_Avoid_: log, trace, evidence

**Fact Flag**:
A protocol-rule violation marked on the Timeline (bad CRC, reply timeout). A fact, not a verdict on whose code is wrong.
_Avoid_: diagnosis, verdict

**Summary**:
The top layer of the Timeline: counts plus the list of Fact Flags, what the Agent gets by default before drilling down.

**Mark**:
A named point the Agent puts on the Timeline to slice it, typically one per build-flash-observe iteration.
_Avoid_: run, session (EHand has no run/stop; it plays and records continuously after apply)

## Relationships

- A **Virtual Periphery** binds one **Peripheral Model** to each used **Channel**; **Channels** exist because of the **Wiring**.
- **Injections** target one **Peripheral Model** and are recorded on the **Timeline**.
- The **Agent** reads the **Summary** first and drills into the **Timeline** as needed; judging the **Target Board** firmware is the Agent's job, never EHand's.
