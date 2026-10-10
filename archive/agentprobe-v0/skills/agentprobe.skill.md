# AgentProbe Skill

schema_version: 0.1.0

## supported_capabilities

- replay-first scenario execution
- two-board self-hosting topology declaration
- SPI-first Mock/Analyzer workflow
- UART bridge/snoop observation
- 8-channel logic capture
- CMSIS-DAP v2 / SWD DUT control
- Evidence Envelope consumption

## not_supported

- MCP / REST API / Python SDK / IDE plugin as V1 integration surfaces
- Cloud sync or remote execution
- More than 8 capture channels
- GUI or web dashboard
- I2C/SHT30 as a Phase 1 self-hosting gate

## planned_capabilities

- I2C/SHT30 external reference demo
- ITM trace decode and DWT event counters
- ETM trace where target hardware and bandwidth allow
- Shared lab asset management

## safety

Golden firmware/bitstream update mode is disabled by default. Never apply DUT artifacts to Golden unless a human explicitly authorizes the exact Golden serial and artifact hash.
