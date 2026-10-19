# GW5AT-138 FPGA 构建流水线与工程底座规划 (Issue #13)

## 1. 现状与工具链约束

- **芯片特性**：GW5AT-138 (Gowin Arora-V 138K) 采用 28nm 工艺，内嵌 12.5Gbps SerDes 与 PCIe 2.0 x4 硬核控制器。其 PCIe DMA IP 包包含加密组件（`tlp_dec_encrypt.v`、`arbiter_encryption.v`）。
- **开源工具链现状**：开源综合与 PnR 工具（Yosys / Project Apicula / nextpnr-gowin）目前仅支持 GW1N/GW2A 小规模器件，不支持 GW5A/GW5AT 系列 SerDes 与硬核 PCIe IP，必须使用高云官方 Gowin EDA。
- **板端运行环境**：
  - 本板卡当前为 Ubuntu 22.04 LTS（ARM64 aarch64）。
  - 官方预装 Gowin IDE 的镜像为定制 openEuler 22.03 LTS。Gowin 官方分发包需企业账户/登录权限，且编译运行时需要绑定 MAC 地址的 Node-locked License 或局域网 Floating License。

## 2. 流水线裁决：分层工程模板 + 跨机协同

为确保开发高效与系统稳定，EHand 采取**“分层工程底座 + 跨机协同自动发布”**架构：

### 2.1 底座模板设计（Base Template）
- 底座工程源自 `chapter-2.10.2-pcie_dma_demo`，已预编译生成标准固件 `pcie_dma_demo.fs`。
- **资源划分**：
  - **PCIe 硬核与 SGDMA**：占据 BAR0（64KB），由内核驱动 `gowin_demo.ko` 提供 DMA 传输与中断。
  - **用户逻辑与时间戳/外设寄存器区**：占据 BAR2（64KB/256MB），直通用户态 `mmap`。
  - 这种设计允许我们在 BAR2 地址空间内任意扩展 GPIO 控制、微秒时间戳读取、UART 移位寄存器，而无需频繁重新综合 PCIe 硬核部分。

### 2.2 跨机编译与自动部署流程
1. **RTL 迭代与修改**：Verilog 源代码置于 `fpga/` 目录，统一纳入 Git 仓库版本管理。
2. **比特流编译**：
   - Windows 宿主机（Doctor）或配备 Gowin EDA 的工作站通过 `gw_sh pcie_dma_demo.tcl` 执行批处理编译，生成 `.fs`。
3. **板端烧录与热重置（In-the-loop）**：
   - 固件推送到板端后，执行自动化脚本：
     ```bash
     # 写入 SRAM 调试
     openFPGALoader -m bitstream.fs
     # 或固化至 SPI Flash
     openFPGALoader -f -o 0x000000 bitstream.fs
     # 触发 PCIe 复位与总线重新枚举
     openFPGALoader -r
     echo 1 > /sys/bus/pci/rescan
     ```
4. **板端验证**：Python / C 测试套件直接通过 `/dev/gowin_pcie_bar` 或物理 MMIO 运行断言。
