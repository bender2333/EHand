.PHONY: all cli firmware fpga protocol test clean

all: protocol cli firmware fpga

protocol:
	python cli/tools/generate_protocol.py --check

cli:
	python -m compileall -q cli/src

firmware:
	@echo "Firmware build placeholder: implement in firmware/scripts/build.ps1"

fpga:
	@echo "FPGA build placeholder: implement in fpga/scripts/synth.tcl"

test:
	python -m compileall -q cli/src

clean:
	@echo "Clean placeholder"
