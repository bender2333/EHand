# EHand Board 硬件事实（正点原子 Zynq-7020）

> Issue #2（wayfinder map #1）。目的：给 Wiring 计划（#7）和首条端到端路径（#4）提供硬件事实。
> 术语见 `CONTEXT.md`。PL = FPGA 逻辑，PS = ARM 侧。

## 0. 来源与可信度

| 缩写 | 文档 | 获取方式 |
|---|---|---|
| **[Z20-PAGE]** | 正点原子官网产品页「正点原子Z20 ZYNQ开发板」`https://www.alientek.com/Product_Details/152.html` | 页面文字只有标题；参数都在页面的长图里，下载后逐张读取（图号见引用） |
| **[Z20-DOC]** | 资料下载中心「ZYNQ 7020开发板Z20」`http://www.openedv.com/docs/boards/fpga/Z20.html` | 网盘链接 + 讨论帖 thread-351965 |
| **[LHZ-DOC]** | 资料下载中心「领航者ZYNQ开发板7010/7020」`http://www.openedv.com/docs/boards/fpga/zdyz_linhanz(V2).html` | 网盘链接 + 讨论帖 thread-329957 |
| **[LHZ-ADDA]** | 《领航者ZYNQ之FPGA开发指南 V2.0》第二十六章 高速AD/DA实验，`http://www.openedv.com/thread-331669-1-1.html` | 厂家论坛连载原文 |
| **[LHZ-IOEXT]** | 同上指南第三十章 IO扩展模块实验，`http://www.openedv.com/thread-332033-1-1.html` | 原文含完整 XDC |
| **[QMX-PAGE]** | 官网「启明星ZYNQ开发板」`https://www.alientek.com/Product_Details/79.html` 首图（7010 版实物，丝印可读） | 下载图片读取丝印 |
| **[XADC-DOC]** | `http://www.openedv.com/docs/modules/other/ATK-XADC.html` + thread-332541 | 只有链接与图片，无参数 |
| **[PKG400]/[PKG484]** | AMD/Xilinx 封装引脚文件 `xc7z020clg400pkg.txt` / `xc7z020clg484pkg.txt`，`https://www.xilinx.com/content/dam/xilinx/support/packagefiles/z7packages/` | 一手；用于引脚 → Bank 映射 |
| **[F-354403]** | 论坛帖 thread-354403（官方回复：最小系统板 VCCO_MIO0_500 接 3.3 V） | 厂家论坛 |

- **openedv.com 在本机 DNS 解析到假 IP，直连超时**；所有 openedv 内容都是 `curl -H "Host: www.openedv.com" http://47.111.11.73/...` 取得（Bing 索引里该 IP 就是同一站点）。
- 官网产品页参数全部是图片，引用写作 `[Z20-PAGE 图N]`（N = 页面图片顺序）。图里的中文由视觉模型转录，数值已在多张图之间交叉核对；只在一张图里出现的值会注明。
- 原理图、用户手册 PDF 都在百度网盘（需登录/客户端），**本次没拿到**。因此 Ethernet PHY 型号、扩展口逐脚表（Z20）、Bank 电压跳线的具体电路**未核实**，见 §8。
- **UNVERIFIED** = 无一手来源；**DERIVED** = 由一手数据推出（可复算）。

---

## 1. 先定是哪块板（需要用户确认）

"正点原子 Zynq-7020 工业级开发板"可指两款，核心芯片都是 **XC7Z020-2I，核心板工作温度 -40~85 ℃**：[Z20-PAGE 图19]

| | **领航者 V2（7020）** | **Z20 ZYNQ** |
|---|---|---|
| 芯片 | XC7Z020**CLG400**-2I | XC7Z020**CLG484**-2I |
| 2×20 扩展口 | **2 个** | **1 个**（36 个可用 IO）|
| FMC LPC | 无 | 1 个（36 对差分）|
| JTAG | 14 针 | 10 针 |
| ATK 模块接口 | 1 个 | 无 |
| USB Host | 4 | 3 |
| HDMI 输入、LVDS LCD、WiFi/BT 天线 | 无 | 有 |
| PS/PL LED | 各 3 | 各 2 |

[Z20-PAGE 图19、图20]。官方总结："Z20 比领航者少一个 20×2 的 IO 扩展口，但多一个 FMC LPC 接口"。[Z20-PAGE 图20]

**两款共同点**：PS DDR3 1 GB（2×512 MB），QSPI Flash 256 Mb，eMMC 8 GB，PS 千兆网口 1、PL 千兆网口 1，HDMI 输出，RGB888 LCD，RS232 / RS485 / CAN 各 1，摄像头口，XADC 口，USB-UART，USB Slave，TF 卡，I²C RTC（CR1220）+ I²C EEPROM 64 Kb，PS/PL 复位键各 1，PS/PL 用户键各 2。[Z20-PAGE 图20]

→ **对 EHand 有影响的差别只有一条：扩展口数量（2 个 vs 1 个 + FMC）。** Wiring（#7）要先确认手上是哪块。下文两款分开写。


### 1.1 用户截图清单与这两款都对不上（重要）

用户给的清单（1 GB DDR3、**128 Mbit QSPI**、TF 卡、**UART 与板载 Xilinx JTAG 下载器共用一个 Type-C**、**80 个 GPIO**、独立供电可调 BANK、HDMI 输出、TFT LCD、摄像头、PL 50 MHz）和上面两款的官方参数有出入：

| 清单 | 领航者 V2 / Z20 官方参数 |
|---|---|
| QSPI 128 Mbit | 256 Mb [Z20-PAGE 图17] |
| 无 eMMC | 板载 8 GB eMMC [Z20-PAGE 图17] |
| UART+JTAG 共用 Type-C（板载下载器）| USB-UART 是独立 Type-C（CH340），JTAG 是单独 10/14 针排针 [Z20-PAGE 图03、图13] |
| 80 GPIO | 领航者扩展口 36 脚（×2 口）；Z20 扩展口 36 脚 + FMC [Z20-PAGE 图14] |
| BANK 电压可调（总体）| Z20 仅 BANK33/34 可调；领航者未见 [Z20-PAGE 图15] |

→ 清单很可能是**另一家的板子**（本次检索里同时出现过 Smart ZYNQ SL 的"一侧 Bank 电压可调、Type-C(JTAG) 供电"描述，`http://www.hellofpga.com/index.php/2023/05/10/smart-zynq-sl/`，但那是 7020 以外的小板，也不符合 80 GPIO）。**不要把本文的 Alientek 结论当成用户手上那块板的事实**，先让用户确认品牌型号（#2 未解决项第 1 条）。**UNVERIFIED**：清单对应哪家产品。

## 2. 芯片资源（两款相同）

XC7Z020，Zynq-7000，PL 为 Artix-7 架构，速度等级 -2；双核 Cortex-A9 **最高 766 MHz**；85K LC，53,200 LUT，106,400 FF，4.9 Mb BRAM，220 DSP，4 CMT。[Z20-PAGE 图17、图19]

- 厂家写 766 MHz；-2 速度等级器件本身可到更高频率，厂家为何定 766 MHz 未说明。**UNVERIFIED**（是否可改）。
- PL Bank（DERIVED，[PKG400]/[PKG484] 统计）：
  - CLG400：PL Bank **13（29 脚，仅部分引出）、34（56）、35（56）**；无 Bank 33。
  - CLG484：PL Bank **13（57）、33（56）、34（56）、35（57）**。
  - 全部是 HR（High Range）Bank：支持 3.3 V I/O。Z20 核心板标称 HR I/O 200 个。[Z20-PAGE 图17]

## 3. PL 时钟

- **PL 端单端 50 MHz 晶振；PS 端单端 33.3333 MHz。**[Z20-PAGE 图16、图17、图20]（两款相同）
- 领航者 PL 时钟引脚 **U18**，LVCMOS33；PL 复位键 **N16**。[LHZ-ADDA 表 26.3.1；LHZ-IOEXT XDC]
  - U18 = `IO_L12P_T1_MRCC_34`，Bank 34 的 MRCC 时钟脚；N16 = `IO_L21N_T3_DQS_AD14N_35`，Bank 35。[PKG400]（DERIVED）
- Z20 的 PL 时钟引脚：**未取得**（在网盘的原理图/XDC 里）。
- 板上没有说明独立的可编程时钟芯片；更高/更精确的频率要用 MMCM/PLL 从 50 MHz 合成。**UNVERIFIED**（没看到原理图，只是没见到相关描述）。

## 4. 扩展口引脚与所在 Bank

### 4.1 领航者 V2 —— 一个 2×20 扩展口（含 36 个 IO），已证实

来源：[LHZ-IOEXT] 的 XDC（IO 扩展模块就插在这个扩展口上，用满 36 脚）。Bank 由 [PKG400] 查得（DERIVED）。

| Bank | 引脚 |
|---|---|
| **34**（30 脚）| N18 N20 U20 U19 P19 T20 T14 U17 Y16 T15 W16 T16 Y17 V16 N17 P18 V20 W20 R17 R16 W19 W18 V17 V18 T17 R18 Y18 Y19 P15 P16 |
| **35**（6 脚）| J14 M19 L16 M15 M20 K14 |

- 实验工程全部用 **LVCMOS33** 约束（见 §5）。[LHZ-IOEXT]
- 其中有成对差分脚（如 W18/W19 = L22P/N、P15/P16 = L24P/N、T14/T15 = L5P/N），DERIVED。厂家没说明这个扩展口有没有做差分等长；Z20 页面的"差分等长"指的是 Z20 自己的底板。
- 高速 AD/DA 模块（§7）也接这个口：DA 数据 R17 R16 W19 W18 P16 P15 Y19 Y18，DA 时钟 R18，AD 数据 V16 W16 T14 T15 Y17 …（与上表一致）。[LHZ-ADDA 表 26.3.1]
- **第二个扩展口的引脚：没取得。** 可参考同系列的启明星（同一个 CLG400 封装，丝印可读，[QMX-PAGE]）：
  - 顶部扩展排针 21 脚（G15 E19 G18 M18 H17 B19 D18 K18 C20 D20 F20 L20 G17 M17 H16 A20 E17 K17 B20 D19 F19）全部在 **Bank 35**（DERIVED）。
  - J4 有 35 脚：**Bank 13 占 25 脚、Bank 34 占 10 脚**（DERIVED）。丝印 **"7020 ONLY"**：7010 封装没有引出 Bank 13，所以这些脚只有 7020 有。
  - 这只能**推测**领航者第二扩展口的布局，**UNVERIFIED**：领航者与启明星底板不同。

### 4.2 Z20 —— 一个 2×20 扩展口（36 IO）+ FMC LPC

- 2×20 扩展口，可用 IO **36 个**；FMC LPC 含 **36 对差分 IO**。[Z20-PAGE 图14]
- 底板的 FMC LPC 和扩展口 IO **全部走差分等长线**；核心板同一 Bank 到连接器也是全部等长、差分设计、控阻抗。[Z20-PAGE 图18]
- 核心板 4 个 80 针板对板连接器（核心板侧 SGDBF-05-80P-H35 母座，底板侧 SGDBM-05-080P-H10 公座，最高 1.5 Gbps），引出 **PS IO 42 个、PL IO 199 个**。[Z20-PAGE 图14、图17]
- 实物照片里扩展口丝印可见 `L16 K16 M22 … 3V3 5V`，图片分辨率不够，读不出全表。[Z20-PAGE 图03]
- **逐脚表与 Bank：没取得**（网盘原理图）。结合 §5 推测：扩展口和 FMC 是在电压可调的 Bank 33/34 上，**UNVERIFIED**。

## 5. Bank 电压怎么设、3.3 V 是否可用

- **Z20：BANK33 / BANK34 电压可在 1.8 / 2.5 / 3.3 V 之间切换**，目的是"连接不同电平标准的外设"。[Z20-PAGE 图15、图18]
  - 切换方式是**跳线**：底板丝印 `B34`、`B33` 各有 `3.3V / 2.5V / 1.8V` 三档，丝印编号 `J7`。[Z20-PAGE 图03 实物丝印]
  - 底板线框图另有读法 `B34 / B35 / B13`（图片较糊）。[Z20-PAGE 图10] 与图15（文字规格表，"BANK33/BANK34"）矛盾，**以图15 文字为准**；最终以原理图核实。
  - 跳线背后是一个 LDO 还是可调 DC-DC：**没取得**。
- **领航者：** 厂家资料没有提到 Bank 电压可调。扩展口实验全部约束为 LVCMOS33 并直接驱动 3.3 V 外设（数码管、LED、矩阵键盘 3.3 V 上拉）→ **扩展口所在 Bank 34/35 为 3.3 V**。[LHZ-IOEXT]（由实验工程推出，非原理图）
- PS 侧：同系列 ZYNQ 最小系统板 VCCO_MIO0_500 接 3.3 V（官方回复）。[F-354403]（不是领航者/Z20 本身，仅作参考）
- Zynq-7000 任何 Bank 的 VCCO 都不能超过 3.45 V；**I/O 不耐 5 V**。Target Board 是 5 V 逻辑时需要电平转换。**UNVERIFIED**（行业常识，本次没有从 DS187 摘原文）。
- 结论：**3.3 V 两块板都能用**；Z20 必须确认 B33/B34 跳线插在 3.3 V。

## 6. 以太网

- 两款都是 **PS 端 1 路千兆网口 + PL 端 1 路千兆网口**，10/100/1000 Mbps。[Z20-PAGE 图14、图20]
- PL 端网口要在 PL 里放 MAC（或经 EMIO 连到 PS 的 GEM），会占 PL 引脚。
- **PHY 型号、PS 网口是 MIO 上 RGMII 还是经 EMIO、MDIO 地址：都没取得。** [LHZ-DOC] 有《领航者ZYNQ之嵌入式开发指南》lwIP echo 章节（thread-318052），本次没解析出 PHY 信息。需要原理图。

## 7. 官方 AD/DA 与模拟相关

### 7.1 ATK_HS_AD_DA 高速 AD/DA 模块（领航者扩展口）

[LHZ-ADDA]：

| | DA | AD |
|---|---|---|
| 芯片 | **AD9708**，8 bit，最高 125 MSPS，差分电流输出 | **AD9280**（或兼容的 3PA9280），8 bit，最高 32 MSPS，流水线延迟 3 个时钟 + 25 ns |
| 模拟范围 | 经滤波 + 运放后输出 **−5 ~ +5 V**（W1 电位器调幅度）；数据 0 → +5 V，255 → −5 V | 输入 **−5 ~ +5 V**，衰减到 0~2 V 进芯片（VO = VI/5 + 1）；−5 V → 0，+5 V → 255 |
| PL 接口 | 8 bit 并行数据 + 时钟，LVCMOS33 | 8 bit 并行数据 + 时钟（+OTR），LVCMOS33 |

- 模块插在 §4.1 那个扩展口上（引脚见 §4.1）。
- 对 NTC 输出（#1 "NTC: PWM+RC vs 外部 DAC"）：8 bit / ±5 V 量程 ≈ 39 mV 每级，模拟 NTC 分压的精度很可能不够，并且输出是电压源、不是电阻。**DERIVED**（只是计算，结论待 NTC 研究确认）。
- 同一份指南里还有"双路高速 DA / 双路高速 AD"章节（thread-331708、thread-332030），说明有双通道模块；**没读取，参数未知。**
- Z20 侧：官方建议用 FMC 口接"FMC 高速 ADDA"模块。[Z20-PAGE 图20] **型号与参数没取得。**

### 7.2 XADC

- Z20 板载 XADC 接口，**测外部 0~1 V 模拟电压**。[Z20-PAGE 图15]
- 另有 ATK-XADC 外接模块（领航者/启明星用）。[XADC-DOC] 资料页没有参数，**规格未知**。

## 8. 板级其它

- 尺寸：Z20 核心板 57×42 mm、12 层；底板 200×130 mm、6 层。[Z20-PAGE 图09、图10、图14]
- 供电：Z20 规格表写 **"底板 DC12V 输入"**[Z20-PAGE 图20]，接口标注图写 **"DC6~16V 电源输入"**[Z20-PAGE 图13]；核心板 DC 5 V。[Z20-PAGE 图17] 另有一组 3.3 V / 5 V 电源输入输出排针。[Z20-PAGE 图13、图15]
- 启动：BOOT 拨码 JTAG / QSPI / SD（Z20 丝印）。[Z20-PAGE 图03]
- 串口：USB-UART 是 CH340，底板有跳线把 CH340 接到 PS_TX/RX 或 PL_TX/RX（丝印 `CH340_RX/TX`、`PS_RX/TX`、`PL_RX/TX`）。[Z20-PAGE 图03] → 调试串口可以给 PS 也可以给 PL。
- RS485、CAN 两款都有板载收发器接口[Z20-PAGE 图20]；收发器型号、DE/RE 由哪个引脚控制：**没取得**。（这关系到 EHand 能否直接用板载 485 当 Channel，见 `modbus-rtu.md` DE/RE 一节。）

## 9. 厂家软件版本

- **Z20：Vivado 2020.2，PetaLinux 2020.2，u-boot Xilinx-v2020.1，内核 5.4.0。**[Z20-PAGE 图21]
- 领航者 V2：资料盘有三套教程（FPGA 设计篇、嵌入式 Vitis 篇、嵌入式 Linux 篇）[LHZ-DOC]，版本号在网盘里，**没取得**。论坛用户提到"V3.6 版本文件"（thread-354782）和自行升级 PetaLinux 2025.2（启明星，thread-354626）——都是用户自述，**UNVERIFIED**。

## 10. 未解决（需要原理图 / 网盘资料）

1. 用户手上是**领航者 V2 7020 还是 Z20**？（决定扩展口数量）
2. 领航者**第二个**扩展口的逐脚表；Z20 扩展口与 FMC 的逐脚表和所在 Bank。
3. Z20 Bank 电压跳线的确切丝印/电路（B33/B34 还是 B34/B35/B13）；领航者 Bank 电压是否固定 3.3 V。
4. 以太网 PHY 型号及 PS 端连接（MIO RGMII / EMIO）。
5. 板载 RS485 / CAN 收发器型号和控制脚。
6. 领航者厂家工具链版本；双路 AD/DA、FMC ADDA、ATK-XADC 模块参数。

取得方式：Z20 资料盘 `https://pan.baidu.com/s/1Fmu4zdUtASiMJgwAQXsOzw`（提取码 n77q）、领航者 A 盘 `https://pan.baidu.com/s/1vXxmhg_mZm_OVg4xQeiCVQ`（提取码 zdyz）[Z20-DOC][LHZ-DOC]。百度网盘需要登录，自动化拿不到，要用户下载"原理图"和"用户手册"放进仓库（或贴路径）。
