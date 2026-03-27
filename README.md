# 🤖 Fool's Telegram Bot

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Aiogram Version](https://img.shields.io/badge/aiogram-3.x-green.svg)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Project Type](https://img.shields.io/badge/project-pyproject.toml-brightgreen.svg)](pyproject.toml)

> 一个基于 Python 和 aiogram 3.x 构建的异步 Telegram 机器人，采用模块化插件设计，支持 AI 功能与自动化操作。

## ✨ 功能特点

- 🚀 **异步架构**: 基于 `asyncio` 和 `aiogram`，提供高并发处理能力。
- 🔌 **插件化设计**: 功能模块位于 `src/plugins` 目录下，支持动态加载，易于扩展和维护。
- 📝 **完善日志**: 集成 `logging` 模块 ，支持控制台输出与文件 Rotating。
- ⚙️ **TOML 配置**: 使用 `config.toml` 进行集中式配置管理，类型安全且易读。
- 🌐 **浏览器自动化**: 内置 Chrome 自动化功能 (Selenium)，解压即可使用。

## 🛠️ 技术栈

| 组件 | 版本/描述 |
| :--- | :--- |
| **语言** | Python 3.11+ |
| **核心框架** | [aiogram 3.x](https://docs.aiogram.dev/) |
| **依赖管理** | `pyproject.toml` (现代 Python 标准) |
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

本项目使用 `pyproject.toml` 管理依赖，推荐使用以下命令安装：

```bash
pip install -e .
# 如果你在中国大陆，网络较慢，可以使用国内镜像源：
# pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 配置项目

编辑 src/config.toml 文件，填入你的配置：

```toml
# config.toml 示例配置
[network]
proxy="http://127.0.0.1:port" # 代理地址和端口

[api_keys]
telegram_token="123456:abcedfgh" # telegram bot token
```

编辑 src/plugins/AI/config.toml 文件，填入你的配置：

```toml
# config.toml 示例配置
[api]
model_name="Pro/deepseek-ai/DeepSeek-R1" # 模型名称
api_key="sk-xxxxxxxxxxxxxxx" # siliconflow的api
temperature=0.7 # 模型温度

[personality]
default="""
默认人设
"""

[triggers]
group_keywords=["fool","你的触发词1","词2..."]
```

Token 获取：在 [BotFather](https://t.me/BotFather) 对话获取。
模型名称获取：在 [硅基流动模型广场](https://cloud.siliconflow.cn/me/models) 获取。

### 5. 准备 Chrome 环境 (重要 ⚠️)

本项目依赖 Chrome 进行自动化操作。
请确保 assets/googlechrome/ 下的 googlechrome.rar 解压到该目录。
注意: Chrome 浏览器版本必须与 Driver 版本号严格一致，请在属性菜单详细信息中查看。

### 6. 运行机器人

```bash
python -m src.bot
```

## 📂 项目结构

```
TelegramBot/
├── README.md                       # 📘 项目说明文档
├── LICENSE                         # 📜 开源许可证
├── pyproject.toml                  # 📦 项目构建配置
│
├── src/                            # 📂 源代码目录
│   ├── bot.py                      # 🚀 机器人主程序
│   ├── config.toml                 # ⚙️ 全局配置文件
│   │
│   ├── utils/                      # 🛠️ 通用工具模块
│   │   ├── config_loader.py        # 配置加载器
│   │   ├── logger_setup.py         # 日志初始化
│   │   ├── middleware.py           # 中间件（场景日志）
│   │   └── plugins_register.py     # 插件自动注册
│   │
│   ├── plugins/                    # 🔌 功能插件
│   │   ├── AI/                     # AI 核心功能
│   │   │   ├── config.toml         # AI 模块配置
│   │   │   ├── config.py           # AI 模块配置加载
│   │   │   ├── glo.py              # 全局变量、函数
│   │   │   ├── handlers/           # 消息处理器
│   │   │   │   ├── AIchat.py       # 聊天逻辑
│   │   │   │   ├── auth.py         # 用户鉴权
│   │   │   │   ├── balance.py      # 余额查询（待修复）
│   │   │   │   ├── history.py      # 历史记录
│   │   │   │   └── identity.py     # 人设更改
│   │   │   │
│   │   │   ├── services/           # 业务服务层
│   │   │   │   ├── client.py       # API 客户端
│   │   │   │   ├── html.py         # HTML 渲染
│   │   │   │   └── message.py      # 消息处理
│   │   │   │
│   │   │   └── record/             # 静态资源/数据记录
│   │   │       ├── black.txt       # 黑名单
│   │   │       ├── personality.txt # 人设提示词
│   │   │       └── *.ttf           # 字体文件
│   │   │
│   │   └── help/                   # ❓ 帮助模块
│   │       └── help.py             # 帮助指令实现
│   │
│   └── __init__.py
│
└── assets/                         # 🖼️ 外部静态资源
    └── googlechrome/               # selenium依赖
        └── ...                     # (分卷压缩包，需解压)
```

## ⚠️ 温馨提示

本项目目前仍处于 **测试阶段**，如遇报错或异常行为属正常现象，请勿惊慌 😊  

如需进行插件开发、查阅 API 或查看源码，请参考以下资源：
- 📖 **官方文档**：[aiogram.dev](https://docs.aiogram.dev/en/latest/)
- 💻 **GitHub 仓库**：[aiogram/aiogram](https://github.com/aiogram/aiogram)

## 📄 许可证 (License)

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---
Made with ❤️ by **lym2006**