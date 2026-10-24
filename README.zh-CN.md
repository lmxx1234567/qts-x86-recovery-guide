# 通用 x86 上的 QTS 安装与数据恢复

本指南介绍如何用独立 SSD 引导 QTS，校准硬件与盘位映射，并恢复完整的 QNAP Qtier 硬盘组。参考硬件为 ASRock Rack X570D4U-2L2T、Ryzen 5800X 和八盘位机箱；其他硬件需重新验证驱动、映射及固件兼容性。

## 按任务选择路线

[英文任务索引](README.md#read-in-this-order)区分恢复主线与可选配置，章节编号不是全部必读的顺序。

| 当前任务 | 阅读入口 |
|---|---|
| 在新 x86 主机恢复原 QNAP 盘组 | 按下方恢复路线，完成数据与独立启动验收 |
| 升级已正常工作的自组 QTS | 先读[更新与回退](docs/08-updates.md#per-release-sequence)；X77 → X73A / 6.1 使用[已有安装升级分支](docs/11-qts61-upgrade.md#3-upgrade-an-existing-custom-qts-installation)，不要重新执行全新安装 |
| 调整温度、内存、应用或机箱预览 | 完成恢复与数据导出后，按需选择下方可选配置 |

### 新主机恢复路线

1. [适用范围](docs/00-scope.md) → [磁盘清单与备份](docs/01-inventory.md)。先确认存储家族、完整盘组与副本；正常 QTS 启动会写盘。
2. [选择版本](docs/02a-release-tracks.md) → [固件与引导依赖](docs/02-firmware.md)。先定版本，再下载并准备构建输入。
3. 按[命令手册第 1–6 节](docs/10-command-walkthrough.md#1-build-machine-and-directory-layout)构建隔离 VM，并完成[虚拟机验收](docs/03-vm-validation.md#required-sequence)。命令手册是各阶段的配套，不是末尾再做一遍。
4. [收集实体控制器/端口拓扑](docs/05-bay-mapping.md#concrete-linux-topology-collection)，再[构建和安装实体候选](docs/04-build-and-install.md)。
5. 安装后在诊断启动中[验证每个盘位](docs/05-bay-mapping.md#turn-the-inventory-into-a-tested-profile)。失败就修正配置并重测，不进入正常存储启动。
6. [恢复完整盘组](docs/06-migration.md#decide-before-clicking-anything) → [数据与独立启动验收](docs/07-acceptance.md)。不要初始化、建池或格式化原盘；Qtier SSD 层也包含真实数据。

引导 SSD 只存放引导和固件；系统卷、应用和数据使用独立存储池。不要把引导 SSD 剩余空间直接当数据卷。

## 版本与效果

- **5.2 稳定分支**：2026-10-22 下载清单为 5.2.11.3652；运行验证基线为 5.2.10。使用更新版本前需完成相同验收。
- **6.1 Beta**：参考版本 6.1.0.3640、TS-X73A；包含 VM 手动升级和实体机 Qtier 恢复经验。先核对所需应用的兼容性。

[参考结果与验证范围（英文）](docs/case-study.md) · [中文实机效果图](docs/screenshots.zh-CN.md) · [英文效果图](docs/screenshots.md) · [故障排查](docs/09-troubleshooting.md)

## 恢复后的可选配置

按问题选读[硬件读数与内存](docs/07a-hardware-and-apps.md#before-you-start)、[跨架构应用](docs/07a-hardware-and-apps.md#arm64-apps-preserve-data-inventory-before-cleanup)或[缓存候选盘](docs/07a-hardware-and-apps.md#ssd-cache-candidates-a-slot-capability-bitmap)，不需要依次全部配置。监控阈值按实际硬件确定，不照搬示例机器的设置。

[机箱预览指南](docs/12-custom-chassis-display.md)介绍前后 SVG、网口和盘位高亮校准、深浅色验证，以及带兼容性检查的启动恢复。示例端口表不是其他机器的固定编号。更新后如恢复程序报告不兼容，保留厂商资源，重新适配后再启用。

仓库不含官方固件、第三方引导二进制、凭据或原始磁盘数据。主操作文档为英文；中文界面截图单独展示。

## 按需参考

[故障排查](docs/09-troubleshooting.md) · [参考硬件与验证范围](docs/case-study.md) · [依赖来源](docs/sources.md) · [私有验收清单](templates/acceptance.md)
