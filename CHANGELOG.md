# Changelog

本项目的所有重要更改都将记录在此文件中。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]
### Added
- 正在开发：AI 生成式对话的流式输出

### Changed
- 正在重构：将原有的草稿消息流式输出方案替换为更优雅的内联键盘交互方式
- 优化 /md 命令判断，避免输出与本次回复不相符的内容

---

## [0.1.8] - 2026-08-16

### Added
- 在 README 中添加了项目运行截图，为用户提供更直观的视觉引导。

### Changed
- 将 `start.bat` 中的所有控制台提示语替换为英文，避免编码错误。

---

## [0.1.7] - 2026-08-16

### Added
- 新增 `start.bat` 一键启动脚本，支持自动激活虚拟环境与启动机器人。

### Changed
- 更新 `install.bat` 与 `update.bat` 自动化脚本，优化安装与更新流程。
- 更新 `README.md` 文档，补充 `start.bat` 使用说明及环境配置指引。

### Fixed
- 修复部分模块中的相对导入路径问题，确保包上下文解析正确。
- 修正相关模块中的变量名拼写错误，解决 `ImportError` 启动异常。

---

## [0.1.6] - 2026-08-16

### Added
- 新增项目文件自动初始化与缺失检测机制 (`init_files`)
- 新增配置文件自动扫描与版本兼容性检查 (自动合并 `config.example.toml` 中的新字段)
- 新增统一的根目录路径读取模块 (`root_dir`)，解决路径引用混乱问题

### Changed
- 重构项目目录结构，优化模块导入逻辑
- 全面接入 Ruff 代码规范检查，提升代码质量
- 安装与更新脚本的提示语改为纯英文，并在 README 中补充中文翻译
- 优化 `config` 加载流程，增强异常处理与错误提示
- 更新 README 操作步骤，替换最新的 `config.example.toml` 模板
- 更新 `.gitignore` 规则，忽略更多不必要的临时文件

---

## [0.1.5] - 2026-08-15

### Added
- 新增 `install.bat` 和 `update.bat` 自动安装/更新脚本
- 新增 Ruff 配置（`pyproject.toml` 中的 ruff 工具配置）

### Changed
- 修改 `README.md` 安装说明，补充手动安装步骤和 Windows 环境准备指南
- 修改 `README.md` 有序列表编号在代码块间被重置的问题

### Fixed
- 修复 `install.bat` 因目录非空导致 `git clone` 失败的问题
- 修复 `update.bat` 未进入 `TelegramBot` 目录导致找不到 `.git` 和 `.venv` 的问题
- 统一 `install.bat` 和 `update.bat` 的启动提示信息

---

## [0.1.4] - 2026-08-14

### Changed
- 优化了项目代码中的 Emoji 使用，提升了代码注释与日志的可读性。
- 调整了 README.md 的排版结构，完善章节描述，确保术语规范。

### Fixed
- 修复了部分 Emoji 在特定环境下无法正确渲染的问题。

---

## [0.1.3] - 2026-08-13
### Changed
- 优化 README 目录结构与排版

---

## [0.1.2] - 2026-08-13
### Added
- 初始化项目更新日志 (`CHANGELOG.md`)

### Changed
- 优化 `README.md` 文档结构，新增目录索引（TOC）与 Changelog 跳转入口
- 修正文档中的格式不规范与拼写错误
- 引入 `.gitmessage` 模板，规范日常代码提交格式

---

## [0.1.1] - 2026-08-12
### Changed
- 更新 `.gitignore` 内容，修复本地配置及日志泄露的问题

---

## [0.1.0] - 2026-08-12
### Added
- 项目架构重置与初始化
- 引入 `aiogram` 框架，实现基础的 Telegram Bot 消息收发
- 引入 `.gitignore` 规范，隔离敏感配置与本地数据文件
- 完成 AI 对话的基础功能