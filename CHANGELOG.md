# Changelog

本项目的所有重要更改都将记录在此文件中。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]
### Added
- 正在开发：AI 生成式对话的流式输出

### Changed
- 正在重构：将原有的草稿消息流式输出方案替换为更优雅的内联键盘交互方式

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