# AgentProbe Firmware

Zynq PS firmware owns USB device behavior, command dispatch, CMSIS-DAP/SWD processing, event aggregation, and Mock management coordination.

V1 firmware is FreeRTOS on Cortex-A9 CPU0. CPU1 AMP and ITM/DWT internal observation are V2 expansion tracks.
