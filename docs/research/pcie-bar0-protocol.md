# GW5AT-138 PCIe SGDMA 与 BAR0/BAR2 寄存器协议逆向与映射规格

> 文档定位：针对高云晨熙五代 GW5AT-LV138PG484（OrangePi MSOC）板载 PCIe Gen2 x4 硬核与官方样例（`gowin_demo.ko`、`gowin_pcie_demo_arm64`、`pcie_dma_demo` RTL）的逆向工程规格说明。为 EHand 宿主-FPGA 混合总线与驱动实现提供确切硬件寄存器与协议标准。

---

## 1. 硬件拓扑与 PCIe 硬核配置

### 1.1 器件与硬核参数
* **FPGA 芯片型号**：GW5AST-LV138PG484AC1/I0（高云晨熙五代，`target_device=gw5ast138b-002`）。
* **PCIe 控制器 IP**：Gowin `PCIE_Controller_Top` 配合 SerDes 四通道（X4 模式）。
* **总线速度与带宽**：PCIe 2.0 (Gen2 x4)，理论双向带宽 4.0 GB/s，单向有效吞吐约 2.0 GB/s（5.0 GT/s/lane，8b/10b 编码）。
* **时钟树结构**：
  * SerDes 差分参考时钟：100 MHz（`Q0 REFCLK0`）。
  * TLP 总线工作时钟（`tlp_clk`）：100 MHz（256-bit 数据通路）。
* **PCIe 识别标识**：
  * Vendor ID：`0x22C2`（Gowin Semiconductor Corporation）。
  * Device ID：`0x1100`（或 `0x1102`）。
  * Class Code：Base Class `0x05`，Sub Class `0x80`（Memory Controller / Other）。
  * Max Payload Size (MPS)：硬件硬核支持最大 1024 字节，实际传输由宿主机配置与 `devctrl` 影子寄存器协商决定（常用 256/512 字节）。
  * Max Read Request Size (MRRS)：宿主机配置最高支持 4096 字节。

### 1.2 PCIe BAR 资源分配与路由
根据 `pcie_controller.ipc` 与 `top.v` 中的 `tlp_bar_demux` 译码模块：

| BAR 空间 | 物理宽度 | 配置大小 | 预取类型 | 硬件路由标志（`tl_bardec[5:0]`） | 功能分工 |
|---|---|---|---|---|---|
| **BAR0 / BAR1** | 64-bit Memory | 64 KB | Non-Prefetchable | `tl_bardec[0] == 1`（`rx_ctrl_*`） | Gowin SGDMA 引擎控制器、通道寄存器、中断控制与状态监控 |
| **BAR2 / BAR3** | 64-bit Memory | 64 KB（可扩充至 256MB） | Non-Prefetchable | `tl_bardec[2] == 1`（`rx_mem_*`） | 用户逻辑空间（AXI/Wishbone 寄存器、片上 SRAM/BRAM） |
| **BAR4 / BAR5** | 禁用 | - | - | - | 未使能 |
| **CplD 响应流** | - | - | - | `tl_bardec == 6'b000000`（`rx_dma_*`） | 宿主内存读响应（CplD 数据包），直达 `u_tlp_cpld_dec` |

---

## 2. BAR0 寄存器映射与位域规格

BAR0 空间采用标准 32-bit 对齐访问（DWORD），分为「全局管理区」与「DMA 通道队列区」。

```
BAR0 偏移空间划分：
0x0000 ---------------------------
       全局控制与状态 (0x0000 - 0x00FF)
0x0100 ---------------------------
       RDMA (H2C) 通道 0 寄存器组 (0x0100 - 0x011F)
0x0200 ---------------------------
       WDMA (C2H) 通道 0 寄存器组 (0x0200 - 0x021F)
0x0300 ---------------------------
       RDMA (H2C) 通道 1 寄存器组 (0x0300 - 0x031F)
0x0400 ---------------------------
       WDMA (C2H) 通道 1 寄存器组 (0x0400 - 0x041F)
       ... (通道 i 步进：RDMA @ 0x100+i*0x200, WDMA @ 0x200+i*0x200)
```

### 2.1 全局控制寄存器组（Offset: `0x0000` - `0x00FF`）

#### 1. `0x0000` - `CTRL`（DMA 全局控制寄存器，RW）
* **位域定义**：
  * `[0]` - `DMA_EN`：全局 DMA 引擎使能。
    * `1`：使能 DMA 引擎调度。
    * `0`：复位/挂起 DMA 状态机。应用启动时通常先清零再置位以复位调度引擎。
  * `[1]` - `SINGLE_IRQ_MODE`：单中断模式选择。
    * `1`：单 MSI / 共享中断模式（驱动单向量配置时写入 `3` 即 `DMA_EN | SINGLE_IRQ_MODE`）。
    * `0`：多向量 MSI 模式（驱动多向量配置时写入 `1`）。
  * `[31:2]` - `RESERVED`：保留，写入保持 0。

#### 2. `0x0004` - `CHSW`（通道使能开关，RW）
* **位域定义**：
  * `[7:0]` - `RDMA_CH_EN[7:0]`：RDMA（H2C，Host to Card）通道 0~7 使能位。
    * Bit 0 对应 RDMA Channel 0，置 1 使能。
  * `[15:8]` - `RESERVED`：保留。
  * `[23:16]` - `WDMA_CH_EN[7:0]`：WDMA（C2H，Card to Host）通道 0~7 使能位。
    * Bit 16 对应 WDMA Channel 0，置 1 使能。
  * `[31:24]` - `RESERVED`：保留。
* **默认驱动初始化值**：单通道下写入 `0x00010001`（同时开启 RDMA0 与 WDMA0）。

#### 3. `0x0008` - `INTR`（中断屏蔽与使能寄存器，RW）
* **位域定义**：
  * `[7:0]` - `RDMA_IRQ_EN[7:0]`：RDMA 通道 0~7 完成中断使能（1=使能，0=屏蔽）。
  * `[15:8]` - `RESERVED`：保留。
  * `[23:16]` - `WDMA_IRQ_EN[7:0]`：WDMA 通道 0~7 完成中断使能（1=使能，0=屏蔽）。
  * `[31:24]` - `RESERVED`：保留。
* **操作机制**：驱动初始化时清零屏蔽全部中断；通道启动前按位或写入开启特定中断。

#### 4. `0x000C` - `ACLR`（中断自动清除控制，RW）
* **位域定义**：
  * `[7:0]` - `RDMA_ACLR[7:0]`：RDMA 通道 0~7 中断自动清除标志。
  * `[15:8]` - `RESERVED`：保留。
  * `[23:16]` - `WDMA_ACLR[7:0]`：WDMA 通道 0~7 中断自动清除标志。
  * `[31:24]` - `RESERVED`：保留。
* **工作机制**：
  * 当置 1 时，硬件产生 MSI 并收到硬核 `tl_int_ack` 确认后，硬件自动清除中断状态位。多 MSI 向量模式下驱动置位对应位。
  * 当置 0 时，硬件保持中断状态，要求主机软件通过向 `0x0010` 写入 1（W1C）手动清零。单 MSI 模式必须置 0。

#### 5. `0x0010` - `ISTA`（中断状态与清除寄存器，R/W1C）
* **位域定义**：
  * `[7:0]` - `RDMA_IRQ_STA[7:0]`：RDMA 通道 0~7 中断挂起状态。读返回 1 表示产生中断；向其写入 1 清除中断状态。
  * `[15:8]` - `RESERVED`：保留。
  * `[23:16]` - `WDMA_IRQ_STA[7:0]`：WDMA 通道 0~7 中断挂起状态。读返回 1 表示产生中断；向其写入 1 清除中断状态。
  * `[31:24]` - `RESERVED`：保留。
* **操作规范**：中断处理程序中读取该寄存器，识别中断源后，直接写回读取的原始值执行清除（Write-1-to-Clear），随后读取 `0x0004` 冲刷 PCIe 写流水线。

#### 6. `0x0020` - `DEVCTRL`（PCIe 设备控制影子寄存器，RW）
* **功能说明**：宿主机在枚举建立链路后，从 PCIe 配置空间（Offset `0x88` 或 PCIe Capability + 0x08）读取宿主与根联合体协商后的真实控制字，写入此寄存器。
* **位域定义**：
  * `[7:5]` - `MAX_PAYLOAD_SIZE`：最大有效载荷尺寸。
    * `000b`：128 Bytes
    * `001b`：256 Bytes
    * `010b`：512 Bytes
    * `011b`：1024 Bytes
  * `[14:12]` - `MAX_READ_REQUEST_SIZE`：最大读请求尺寸。
    * `000b`：128 Bytes
    * `001b`：256 Bytes
    * `010b`：512 Bytes
    * `011b`：1024 Bytes
    * `100b`：2048 Bytes
    * `101b`：4096 Bytes
* **硬件映射**：直接连结至 RTL 模块 `u_cmd_if` 的 `tl_cfg_devctrl`，硬件分包器（`tlp_rq_ctrl` / `tlp_rc_ctrl`）依据此参数切割 TLP 数据包长度，防止产生超长包导致 PCIe 协议挂死。

---

### 2.2 DMA 通道寄存器组（Offset: `0x0100` 起，通道步进 `0x0200`）

每组通道占据 `0x0200` 字节空间，其中前半部分（`0x00`~`0xFF`）属于 RDMA，后半部分（`0x100`~`0x1FF`）属于 WDMA。支持最多 8 个独立通道。

#### 通道偏移计算公式：
* **RDMA Channel $i$** 基址 = `0x0100 + i * 0x0200`
* **WDMA Channel $i$** 基址 = `0x0200 + i * 0x0200`

#### 通道寄存器详细定义表：

| 相对偏移 | 寄存器名称 | 读写属性 | 宽度 | 详细功能说明与位域细节 |
|---|---|---|---|---|
| `+0x00` | `SRC_LO / DST_LO` | RW | 32-bit | 主机物理内存地址低 32 位。**必须 4 字节对齐**（Bits [1:0] 必须全为 0）。在 RTL 中只锁存 bits [31:2]。 |
| `+0x04` | `SRC_HI / DST_HI` | RW | 32-bit | 主机物理内存地址高 32 位。用于 64 位 DMA 物理地址寻址。 |
| `+0x08` | `DMA_LEN` | RW | 32-bit | 传输长度计数，**单位为 32-bit DWORD**。例如传输 128 字节填入 `32`（`32 * 4 = 128B`）。硬件支持 bits [23:0]，单次描述符最大传输 16M DWORD（即 64 MB）。 |
| `+0x0C` | `DMA_TAG` | RW | 32-bit | 描述符标签与**硬件触发寄存器**（Trigger Register）。<br>• Bits [7:0] 为用户分配的跟踪 TAG（1~255）。<br>• **核心机制**：向本寄存器写入将原子捕获当前通道的 `(ADDR_LO, ADDR_HI, LEN, TAG)` 寄存器元组，并将其**压入硬件 DMA 请求 FIFO 队列**。 |
| `+0x10` | `DMA_IT_LEVEL` | RW | 32-bit | 中断触发水位阈值（Interrupt Trigger Watermark）。当传输累积完成次数或队列排空达到此阈值时产生通道中断信号（典型设置 `16`）。 |
| `+0x14` | `DMA_STATUS` | RO | 32-bit | 硬件队列与通道运行状态寄存器：<br>• `[7:0]`：当前硬件请求 FIFO 的在途/排队深度（Occupancy Level，范围 0~128）。若读出值为 `0xFF`（255），表示硬件 FIFO 已满，禁止写入新描述符。<br>• `[29:8]`：保留与硬件状态字。<br>• `[31:30]`：通道空闲/完成标志。当读出值满足 `(status & 0xC0000000) == 0xC0000000` 时，表示队列已清空且当前 DMA 事务已全部执行完毕。 |

---

## 3. BAR2 用户空间映射与 MMIO 规格

BAR2 是 GW5AT-138 预留给用户自定义逻辑（User Logic）的高速 MMIO 访问窗口。

### 3.1 硬件总线拓扑
* **TLP 译码流**：当宿主机发起地址落在 BAR2 范围内的 Memory Read (MRd) 或 Memory Write (MWr) TLP 包时，`u_tlp_bar_demux` 产生 `tl_bardec[2] = 1`。
* **控制路由**：
  * TLP 被分流至 `rx_mem_*` 总线，由 `u_mem_tlp_dec`（`tlp_dec` 模块）进行指令和地址解析。
  * `u_cc_ctrl`（Completion Controller）负责处理读写请求。如果是读操作，负责生成完成报文（Cpl / CplD），经由 `u_tl_tx` 仲裁发送回 PCIe 链路；如果是写操作，直接对内部总线或双口 SRAM/BRAM 进行写入。
* **访问延迟与粒度**：支持 Byte（8-bit）、Word（16-bit）、DWORD（32-bit）及突发读写，单次读事务平均延迟约 400~800 ns（受 PCIe 链路往返时延影响）。

### 3.2 驱动与用户态内存映射（MMIO mmap 机制）
在 `gowin_demo.c` 内核驱动中，BAR2 不强制在内核态开辟虚拟映射，而是通过字符设备驱动直接向上暴露给用户态程序：

1. **通道与空间切换**：
   用户态调用 `ioctl(fd, GOWIN_SWITCH_BAR_OR_MEM, &param)`，其中设置：
   ```c
   param.dma_select = 0; // 0 表示映射 PCIe BAR 物理空间，1 表示映射 DMA 一致性内存
   param.index = 2;      // 指定目标为 BAR2
   ```
   驱动将私有上下文中的 `data->cur_bar` 置为 `2`，`data->mem_select` 置为 `0`。

2. **用户态直接建立 MMIO 映射**：
   用户态随后调用标准 `mmap`：
   ```c
   void *bar2_ptr = mmap(NULL, BAR2_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
   ```
   内核驱动在 `gowin_bar_mmap()` 中执行：
   * 获取物理基地址：`phys = pci_resource_start(data->pdev, 2) + off;`
   * 设置非缓存属性：`vma->vm_page_prot = pgprot_noncached(vma->vm_page_prot);`
   * 建立页表映射：`io_remap_pfn_range(vma, vma->vm_start, phys >> PAGE_SHIFT, vsize, vma->vm_page_prot);`

3. **零开销用户态访问**：
   用户态可直接将 `bar2_ptr` 强转为硬件寄存器结构体指针，利用标准 C 指针解引用（`volatile uint32_t *`）实现纳秒级低时延寄存器读写，完全避免每次访问陷入内核系统调用。

---

## 4. SGDMA 描述符格式与硬件队列机制

高云 GW5AT-138 PCIe SGDMA 并非传统 x86 网卡中常见的「基于内存环形链表（Memory Ring Buffer Descriptor）」结构，而是采用了**「寄存器压栈式片上硬件 FIFO（Hardware Register-Enqueued FIFO）」**架构。

### 4.1 硬件 FIFO 架构参数
* **读通道队列深度（`RQ_DEP`）**：128 条目（7-bit 计数器，`RQ_BW = 7`）。
* **写通道队列深度（`RC_DEP`）**：128 条目（7-bit 计数器，`RC_BW = 7`）。
* **请求捕获机制**：每当向通道的 `DMA_TAG` 寄存器写入数据时，内部硬件逻辑产生单周期有效脉冲（`req_dma_rd_valid` 或 `req_dma_wr_valid`），将当前通道的地址、长度、TAG 打包压入请求 FIFO。

### 4.2 逻辑描述符格式（128-bit / 4 DWORDs）
当用户依次写入寄存器并由 `DMA_TAG` 触发入队时，硬件在时钟沿采样捕获如下 16 字节逻辑描述符：

```
 31                                       2 1 0
+------------------------------------------+---+
|       Host Physical Base Address Low     | 00| Word 0 (SRC_LO / DST_LO)
+------------------------------------------+---+
|       Host Physical Base Address High        | Word 1 (SRC_HI / DST_HI)
+------------------------------------------+---+
| Rsvd |        Transfer Length in DWORDs      | Word 2 (DMA_LEN, 24-bit)
+------+-----------------------------------+---+
|       Reserved (24-bit)       |  TAG (8-bit) | Word 3 (DMA_TAG, Trigger)
+-------------------------------+--------------+
```

* **Word 0**：`[31:2]` 主机物理内存低 32 位基地址，`[1:0]` 强制为 0（4 字节对齐）。
* **Word 1**：`[31:0]` 主机物理内存高 32 位基地址（支持 64 位寻址）。
* **Word 2**：`[23:0]` 传输 DWORD 长度（最大 $2^{24} - 1$ 个 32-bit 字，即 64MB - 4B）。
* **Word 3**：`[7:0]` 描述符识别标签（TAG），用于标识批次；`[31:8]` 保留。

### 4.3 描述符流式调度流水线（Pipeline & Chaining）
通过利用片上 128 深度的硬件 FIFO，应用程序无需等待前一个 DMA 块传输完毕，可连续流水线下发描述符：

```
Host Userspace                    BAR0 Registers                   FPGA Hardware FIFO
      |                                 |                                  |
      |-- 1. Check STATUS (Level < 128)-|                                  |
      |-- 2. Write SRC_LO ------------->|                                  |
      |-- 3. Write SRC_HI ------------->|                                  |
      |-- 4. Write DMA_LEN ------------>|                                  |
      |-- 5. Write DMA_TAG ------------>| -- Pulse req_dma_rd_valid ------>| [Enqueue Desc 0]
      |                                 |                                  | [Enqueue Desc 1]
      |-- 6. Repeat for Next Blocks ...>| -- Pulse req_dma_rd_valid ------>| [Enqueue Desc 2]
      |                                 |                                  |        |
      |                                 |                                  | (HW Pipeline Execution)
      |                                 |                                  |        V
      |                                 |                                  | Read Host Mem via MRd
      |                                 |                                  | Packetized by MPS/MRRS
      |<-- MSI Interrupt or Poll STA <--|<-- Assert Interrupt / Idle Flag -|
```

1. **防溢出流控**：每次下发前读取 `DMA_STATUS`，检查低 8 位 `level`。若 `level < 128`，可下发 `128 - level` 个块。
2. **硬件自动切片（Packetizer）**：硬件根据 `0x0020` 的 `DEVCTRL` 寄存器配置，自动将每个描述符的大块传输切分成满足 PCIe MPS/MRRS 的微 TLP 包发送。
3. **完成收敛**：
   * 批次完成检测：轮询 `DMA_STATUS` 的 Bit 31:30 是否等于 `2'b11`（`0xC0000000`）。
   * 细粒度中断：累积到达 `DMA_IT_LEVEL` 水位线时触发一次中断通知。

---

## 5. 中断上报与协同流控机制

GW5AT-138 支持 Legacy INTx 与 MSI（Message Signaled Interrupts）。在 Linux 平台官方推荐使用 MSI 模式。

### 5.1 硬件中断信号与协议
在 `top.v` 中，`u_cmd_if` 向上层 PCIe 硬核暴露以下中断接口：
* `tl_int_req`：中断请求触发信号（高电平有效脉冲）。
* `tl_int_msinum[4:0]`：MSI 向量编号（0 对应 RDMA 通道，1 对应 WDMA 通道）。
* `tl_int_status`：当前全局中断状态标志。
* `tl_int_ack`：PCIe 硬核应答确认信号。收到此应答表明 MSI 消息 TLP 已成功加入发送队列。

### 5.2 单 MSI 共享模式处理流程
当系统仅分配到 1 个 MSI 向量时，所有通道共享该中断号，必须执行如下处理时序：

```
[FPGA Hardware]                   [Linux Kernel Driver]              [User Space Application]
       |                                    |                                    |
  DMA transfer done                         |                                    |
  Assert tl_int_req                         |                                    |
  Hard IP sends MSI TLP                     |                                    |
       |----------------------------------->|                                    |
       |                             gowin_bar_irq_handler()                     |
       |                                    |                                    |
       |<-- Read 0x0010 (ISTA) -------------|                                    |
       |    Return rval (e.g. 0x00010001)   |                                    |
       |                                    |                                    |
       |<-- Write 0x0010 (W1C Clear rval)---|                                    |
       |<-- Read 0x0004 (CHSW Flush Write)--|                                    |
       |                                    |                                    |
       |                             Bit 0..7 (RDMA):                            |
       |                               atomic64_inc(&irq_count[0])               |
       |                               wake_up_interruptible(&irq_wait[0])       |
       |                             Bit 16..23 (WDMA):                          |
       |                               atomic64_inc(&irq_count[1])               |
       |                               wake_up_interruptible(&irq_wait[1])       |
       |                                    |                                    |
       |                                    |-- Unblock ioctl(GOWIN_WAIT_IRQ) -->|
```

1. **读状态（Read Status）**：读取 `0x0010` 获取当前挂起中断通道掩码。
2. **手动清零（W1C）**：将读出的值原样写回 `0x0010`。
3. **流水线冲刷（Flush Write）**：执行一次对 `0x0004` 的虚读，确保清零写事务穿透 PCIe 桥片。
4. **唤醒等待队列**：驱动维护 `irq_wait[channel_id]` 等待队列，唤醒阻塞在 `GOWIN_WAIT_IRQ` 的用户线程。

### 5.3 多 MSI 独立向量模式（Auto-Clear）
若系统分配到多个 MSI 向量（`msi_number > 1`）：
* 驱动在 probe 阶段向 `0x000C`（`ACLR`）写入使能位。
* 硬件发送对应向量 MSI 收到 ACK 后，内部状态位自动清零，不再需要驱动在中断响应路径中串行读取并写回 `0x0010`，大幅降低中断处理时延与总线开销。

---

## 6. 驱动 UAPI 接口与数据交互协议

`gowin_pcie_bar_drv_uapi.h` 定义了内核驱动与用户态交互的 IOCTL 契约。

### 6.1 IOCTL 宏与编码清单

| 命令宏定义 | 方向与参数 | 编号 | 说明 |
|---|---|---|---|
| `GOWIN_BAR_READ_DWORD` | `_IOWR('G', 0x1, ...)` | `0x01` | 读取指定 BAR、指定偏移的 8/16/32 位寄存器值 |
| `GOWIN_BAR_WRITE_DWORD`| `_IOWR('G', 0x2, ...)` | `0x02` | 写入指定 BAR、指定偏移的 8/16/32 位寄存器值 |
| `GOWIN_CONFIG_READ_DWORD`| `_IOWR('G', 0x3, ...)` | `0x03` | 读取 PCIe 配置空间 DWORD（如获取链路协商速度） |
| `GOWIN_CONFIG_WRITE_DWORD`| `_IOWR('G', 0x4, ...)`| `0x04` | 写入 PCIe 配置空间 DWORD |
| `GOWIN_SWITCH_BAR_OR_MEM`| `_IOW('G', 0x5, ...)` | `0x05` | 切换后续 `mmap` 的目标：BAR 物理空间或 DMA 一致性内存块 |
| `GOWIN_REQUEST_DMA_MEM`| `_IOWR('G', 0x6, ...)` | `0x06` | 请求内核通过 `dma_alloc_coherent` 分配连续物理内存 |
| `GOWIN_RELEASE_DMA_MEM`| `_IOW('G', 0x7, ...)`  | `0x07` | 释放指定编号的 DMA 一致性内存块 |
| `GOWIN_WAIT_IRQ`       | `_IOW('G', 0x8, ...)`  | `0x08` | 阻塞等待指定中断通道事件（带毫秒超时设置） |
| `GOWIN_GET_IRQ_COUNT`  | `_IOWR('G', 0x9, ...)` | `0x09` | 查询指定中断通道的历史触发计数值 |
| `GOWIN_CLEAR_IRQ_COUNT`| `_IOW('G', 0xA, ...)`  | `0x0A` | 清零指定中断通道的历史触发计数值 |
| `GOWIN_IRQ_ENABLE`     | `_IOW('G', 0xB, ...)`  | `0x0B` | 使能特定通道的中断屏蔽位（写入 `0x0008`） |
| `GOWIN_IRQ_DISABLE`    | `_IOW('G', 0xC, ...)`  | `0x0C` | 禁用特定通道的中断屏蔽位（写入 `0x0008`） |

### 6.2 核心 IOCTL 参数载荷结构体
```c
struct gowin_iotcl_param {
    union {
        uint32_t argv[8];
        // BAR 读写参数
        struct {
            int32_t     bar_idx;      // BAR 索引 (0: BAR0, 2: BAR2)
            uint32_t    bar_type;     // 0: Byte, 1: Word, 2: DWORD
            uint32_t    bar_offset;   // 寄存器相对偏移
            union {
                uint32_t bar_dword;
                uint16_t bar_word;
                uint8_t  bar_byte;
            };
        };
        // DMA 内存申请与查询参数
        struct {
            int32_t     dma_idx;      // 内存槽位索引 (0 ~ 1023)
            uint32_t    dma_size;     // 内存大小 (字节)
            uint32_t    dma_realloc;  // 是否强制重新分配
            uint32_t    nu_2;
            void       *dma_addr;     // 内核虚拟地址 (内核调试用)
            uint64_t    dma_handle;   // 物理总线地址 (DMA 描述符填入此地址)
        };
        // 映射切换参数
        struct {
            int32_t     index;        // BAR 编号或 DMA 槽位号
            uint32_t    dma_select;   // 0: BAR 空间, 1: DMA 内存
        };
        // 中断等待参数
        struct {
            int32_t     irq_idx;      // 通道号 (0: RDMA, 1: WDMA)
            uint32_t    timeout_ms;   // 超时时间 (毫秒, 最大 1000)
        };
    };
};
```

---

## 7. EHand 工程落地与驱动设计规范

基于逆向得出的确切协议规格，EHand 项目在鲲鹏宿主机（Kunpeng AI Pro）与 FPGA 子板间的总线协同策略如下：

### 7.1 BAR 空间功能界限（遵循 ADR-0004）
* **BAR0（专用 DMA 数据总线）**：
  * 仅保留给 Gowin SGDMA 硬件引擎。
  * 承载高速时间戳跟踪流（Timeline Trace Stream）由 FPGA 向 Host 的单向连续传输（C2H / WDMA Channel 0）。
  * 承载主机波形重放或激励注入（H2C / RDMA Channel 0）。
* **BAR2（专用控制与状态总线）**：
  * 映射 EHand 自定义控制寄存器空间（32-bit MMIO）。
  * 寄存器功能划分：
    * `0x0000`：EHand 逻辑版本与 Magic 校验字（只读，如 `0x4548414E` = "EHAN"）。
    * `0x0004`：采样控制（使能、时钟分频、触发模式选择）。
    * `0x0008`：引脚方向与复用配置（20 路 FPC GPIO 动态模式切换）。
    * `0x0010`：硬件故障注入控制（Timing Injection Triggers）。
    * `0x0020`：硬实时 Modbus/UART 波特率配置与状态寄存器。

### 7.2 零拷贝 DMA 环形缓冲设计建议
1. **主机预分配池**：宿主机用户态启动时，通过 `GOWIN_REQUEST_DMA_MEM` 分配 4MB~16MB 一致性物理内存环。
2. **流水线推入**：将这批内存切分成 64KB 的块，初始化时预先向 BAR0 WDMA0 下发 64 个描述符至硬件 FIFO。
3. **完成推进**：每当收到 WDMA 完成中断或轮询发现水位推进时，处理已就绪的 Timeline 块，并立即将该块的物理地址重新推入 WDMA FIFO，维持硬件队列永不饥饿。
