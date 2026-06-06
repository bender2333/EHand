from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FPGA = ROOT / "fpga"
BUILD = FPGA / "build" / "sim"
OUT = BUILD / "ap_top_tb.vvp"


def main() -> None:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if iverilog is None or vvp is None:
        raise SystemExit("Missing FPGA simulator: install iverilog and vvp")

    BUILD.mkdir(parents=True, exist_ok=True)
    compile_cmd = [
        iverilog,
        "-g2012",
        "-o",
        str(OUT),
        str(FPGA / "rtl" / "top" / "ap_top.v"),
        str(FPGA / "sim" / "ap_top_tb.v"),
    ]
    subprocess.run(compile_cmd, check=True)
    result = subprocess.run([vvp, str(OUT)], check=True, text=True, capture_output=True)
    print(result.stdout, end="")
    if "AP_TOP_SMOKE_PASS" not in result.stdout:
        raise SystemExit("FPGA smoke simulation did not report AP_TOP_SMOKE_PASS")


if __name__ == "__main__":
    main()
