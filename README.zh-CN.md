# 通用 x86 上的 QTS 安装与数据恢复

主文档为英文：[完整流程](README.md)。本仓库记录在非 QNAP x86 硬件上使用独立 SSD 引导 QTS、恢复原 QNAP Qtier 硬盘组的实际过程，并说明适用条件、验证方法和踩坑。

成功方案中，SSD 只存放引导和固件；QTS 的系统卷、应用与数据仍位于原存储池。没有验证“同一 SSD 剩余空间也当数据卷”，也没有验证无人值守自动升级。八盘位 HAL 映射错误是已经修复的历史问题。

请按英文首页的阶段顺序阅读，优先在完整副本和隔离虚拟机中实验。正常 QTS 启动并不是只读操作；不要对原盘点击初始化、创建新池或格式化。Qtier 的 SSD 层包含真实数据，不能当作可丢弃缓存拔掉。

[实际案例](docs/case-study.md) · [截图记录](docs/screenshots.md) · [盘位映射](docs/05-bay-mapping.md) · [存储池迁移](docs/06-migration.md) · [故障排查](docs/09-troubleshooting.md)

仓库不包含官方固件、第三方引导二进制、私人账号或原始磁盘数据。图中敏感内容已用实色遮挡，原图不发布。

## 这台自组 QTS 的配置

**Ryzen 7 5800X（8 核 16 线程）· 64 GiB ECC · 八个 SATA 盘位 · 原 Qtier 池恢复**。主板为 ASRock Rack X570D4U-2L2T，内存为两条 32 GiB、3200 MT/s；独立 Samsung 980 NVMe 负责引导，原两块 4 TB SSD RAID1 + 三块 8 TB HDD RAID5 组成恢复后的 Qtier 池。

![实机英文界面：CPU、64 GB 内存、四个插槽和温度](assets/screenshots/hardware-status-native-en.jpg)

已修正 CPU 温度、内存拓扑、八大盘位预览和全部八个盘位的缓存资格；没有创建缓存，也没有删除 ARM64 旧应用。主板温度尚未接入 QTS。新增修正已在线验证并保存到启动覆盖包，但尚未重启复验。详见[硬件显示与应用迁移](docs/07a-hardware-and-apps.md)。

本次图片直接采集自英文 UI，通过裁剪排除账号、主机名、IP 和序列号，未伪造界面数值。
