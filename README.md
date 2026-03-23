# 🤖 Fool Telegram Bot

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Aiogram Version](https://img.shields.io/badge/aiogram-3.x-green.svg)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Powered by](https://img.shields.io/badge/powered%20by-aiogram-orange.svg)](https://github.com/aiogram/aiogram)

> 一个基于 Python 和 aiogram 3.x 构建的异步 Telegram 机器人，采用模块化插件设计，支持 AI 功能与自动化操作。

## ✨ 功能特点

- 🚀 **异步架构**: 基于 `asyncio` 和 `aiogram`，高并发处理能力。
- 🔌 **插件化设计**: 位于 `src/plugins` 目录下，支持动态加载功能模块，易于扩展。
- 📝 **完善日志**: 集成 `logging` 模块 ，控制台输出。
- 🛡️ **中间件支持**: 内置日志记录中间件。
- ⚙️ **TOML 配置**: 使用 `config.toml` 进行集中式配置管理，类型安全且易读。
- 🌐 **浏览器自动化**: 内置 Chrome 自动化功能 (Selenium)，解压即可使用。

## 🛠️ 技术栈

| 组件 | 版本/描述 |
| :--- | :--- |
| **语言** | Python 3.11+ |
| **核心框架** | [aiogram 3.x](https://docs.aiogram.dev/) |
| **配置文件** | TOML (`config.toml`) |
| **浏览器驱动** | Google Chrome Portable + WebDriver |
| **日志系统** | logging |

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/lym2006/TelegramBot.git
cd TelegramBot
```

### 2. 创建虚拟环境（推荐）
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置项目

编辑 src/config.toml 文件，填入你的配置：

```toml
# config.toml 示例配置
[network]
proxy="填代理地址和端口"

[api_keys]
siliconflow_key="填siliconflow的api"
telegram_token="填telegram bot的token"
```

Token 可以通过与 [BotFather](https://t.me/BotFather) 对话获取。

### 5. 准备 Chrome 环境 (重要 ⚠️)

本项目依赖 Chrome 进行自动化操作。
请确保 assets/googlechrome/ 下的 googlechrome.rar 解压到该目录。
注意: Chrome 浏览器版本必须与 Driver 版本号严格一致，否则无法启动。

### 6. 运行机器人

```bash
python -m src.bot
```
## 📂 项目结构

TelegramBot/
├── assets/                         # 静态资源
│   └── googlechrome/               # Chrome 浏览器及驱动 (需自行放入)
│       └── ...                     # 解压googlechrome.rar
│
├── src/                            # 源代码目录
│   ├── utils/                      # 🛠️ 工具类
│   │   ├── __init__.py
│   │   ├── config_loader.py        # 配置加载 (读取 config.toml)
│   │   ├── logger_setup.py         # 日志配置
│   │   ├── middleware.py           # 中间件
│   │   └── plugins_register.py     # 插件注册
│   │
│   ├── plugins/                    # 🔌 功能插件
│   │   ├── AI/                     # AI 相关功能
│   │   │   ├── record/             # 记录
│   │   │   │   ├── black.txt       # 黑名单
│   │   │   │   ├── personality.txt # 人设
│   │   │   │   ├── font.ttf        # 自定义字体
│   │   │   │   └── seguiemj.ttf    # emoji字体
│   │   │   │
│   │   │   ├── AI.py
│   │   │   ├── func.py
│   │   │   └── __init__.py
│   │
│   ├── help/                       # ❓ 帮助模块
│   │   ├── __init__.py
│   │   ├── help.py
│   │   └── font.ttf                # 自定义字体
│   │
│   ├── __init__.py
│   ├── bot.py                      # 🚀 程序入口
│   └── config.toml                 # ⚙️ 主配置文件
│
├── .gitignore                      # 🚫 Git 忽略规则
├── pyproject.toml                  # 📦 项目构建与元数据配置
├── requirements.txt                # 📦 依赖列表
├── LICENSE                         # 📜 开源许可证（MIT）
└── README.md                       # 📘 说明文档

## ⚠️ 温馨提示

本项目目前仍处于 **测试阶段**，如遇报错或异常行为属正常现象，请勿惊慌 😊  

如需进行插件开发、查阅 API 或查看源码，请参考以下资源：
- 📖 **官方文档**：[aiogram.dev](https://docs.aiogram.dev/en/latest/)
- 💻 **GitHub 仓库**：[aiogram/aiogram](https://github.com/aiogram/aiogram)

## 📄 许可证 (License)

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---
Made with ❤️ by **lym2006**