import os
import time
from typing import Optional

from ehand.hardware.uart import UartPort
from ehand.models.serial_peer import SerialPeer
from ehand.periphery import (
    get_active_injections,
    get_active_periphery,
    save_active_injections,
)
from ehand.timeline import record_transaction


class EHandService:
    def __init__(self, port_override: Optional[str] = None):
        self.port_override = port_override
        self.running = False

    def run_one_turn(self, uart: UartPort, model: SerialPeer) -> bool:
        """Read pending data, process, reply, and record to timeline."""
        rx_data = uart.read(1024)
        if not rx_data:
            return False

        t0_us = int(time.time() * 1_000_000)
        injections = get_active_injections()
        reply, fact_flags, latency_us = model.process_rx(rx_data, injections)

        # Clear non-persistent injections
        remaining_injections = [inj for inj in injections if inj.get("persistent")]
        if len(remaining_injections) != len(injections):
            save_active_injections(remaining_injections)

        if reply is not None:
            # Latency simulation
            if latency_us > 0:
                time.sleep(latency_us / 1_000_000.0)
            uart.write(reply)

        t1_us = int(time.time() * 1_000_000)
        duration_us = t1_us - t0_us

        tx_id = f"tx_{t0_us}"
        record_transaction(
            tx_id=tx_id,
            channel=model.channel_name,
            start_time_us=t0_us,
            duration_us=duration_us,
            req_hex=rx_data.hex(),
            req_ascii=rx_data.decode("latin1", errors="replace"),
            reply_hex=reply.hex() if reply else "",
            reply_ascii=reply.decode("latin1", errors="replace") if reply else "",
            latency_us=latency_us,
            injections=injections,
            fact_flags=fact_flags,
        )
        return True

    def serve_forever(self, poll_interval: float = 0.05) -> None:
        self.running = True
        periph = get_active_periphery()
        if not periph or "channel" not in periph:
            raise RuntimeError("No active periphery applied. Run `ehand apply <file>` first.")

        # For V1 tracer: pick first serial channel
        channel_name, ch_cfg = next(iter(periph["channel"].items()))
        port_path = self.port_override or ch_cfg.get("port", "/dev/ttyUSB1")
        baud = ch_cfg.get("baud", 9600)

        uart = UartPort(port=port_path, baud=baud)
        model = SerialPeer(channel_name=channel_name, config=ch_cfg)

        try:
            while self.running:
                self.run_one_turn(uart, model)
                time.sleep(poll_interval)
        finally:
            uart.close()
