# 通用 x86 上的 QTS 安装与数据恢复

本指南介绍如何用独立 SSD 引导 QTS，校准硬件与盘位映射，并恢复完整的 QNAP Qtier 硬盘组。参考硬件为 ASRock Rack X570D4U-2L2T、Ryzen 5800X 和八盘位机箱；其他硬件需重新验证驱动、映射及固件兼容性。

## 从哪里开始

1. 阅读英文[适用范围](docs/00-scope.md)，确认源系统是 QTS，而非 QuTS hero 或 QuTScloud。
2. 完成[磁盘清单与备份](docs/01-inventory.md)。正常 QTS 启动会写入磁盘；优先在完整副本和隔离虚拟机中验证。
3. 按[版本选择](docs/02a-release-tracks.md)设置参数，再依次执行[命令流程](docs/10-command-walkthrough.md)。已有自组 QTS 使用[升级分支](docs/11-qts61-upgrade.md#3-upgrade-an-existing-custom-qts-installation)。
4. 核对[每个盘位](docs/05-bay-mapping.md)，再[恢复存储池](docs/06-migration.md)和完成[验收](docs/07-acceptance.md)。不要对原盘初始化、建池或格式化；Qtier 的 SSD 层包含真实数据。

引导 SSD 只存放引导和固件；系统卷、应用和数据使用独立存储池。不要把引导 SSD 剩余空间直接当数据卷。

## 版本与效果

- **5.2 稳定分支**：2026-10-22 下载清单为 5.2.11.3652；运行验证基线为 5.2.10。使用更新版本前需完成相同验收。
- **6.1 Beta**：参考版本 6.1.0.3640、TS-X73A；包含 VM 手动升级和实体机 Qtier 恢复经验。先核对所需应用的兼容性。

[参考结果与验证范围（英文）](docs/case-study.md) · [中文实机效果图](docs/screenshots.zh-CN.md) · [英文效果图](docs/screenshots.md) · [故障排查](docs/09-troubleshooting.md)

## 恢复后的可选配置

[硬件与应用指南](docs/07a-hardware-and-apps.md)涵盖温度、风扇、内存、缓存候选盘和跨架构应用检查。监控阈值按实际硬件确定，不照搬示例机器的设置。

[机箱预览指南](docs/12-custom-chassis-display.md)介绍前后 SVG、网口和盘位高亮校准、深浅色验证，以及带兼容性检查的启动恢复。示例端口表不是其他机器的固定编号。更新后如恢复程序报告不兼容，保留厂商资源，重新适配后再启用。

仓库不含官方固件、第三方引导二进制、凭据或原始磁盘数据。主操作文档为英文；中文界面截图单独展示。
