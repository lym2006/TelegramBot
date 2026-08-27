# src/bot/__main__.py
"""
Bot 启动模块

负责：
- 初始化日志器和全局配置
- 检查版本
- 启动 GUI
- 启动 Bot 引擎
"""

import asyncio
import sys
import threading

from PySide6.QtWidgets import QApplication

from gui import create_gui
from utils.exception import ConfigError
from utils.lifecycle import hide_console
from utils.logger import get_logger


class Main:
    """主程序入口，负责初始化环境、配置组件并启动机器人"""

    def __init__(self) -> None:
        self._logger = get_logger("Bot")
        self._proxy: str = ""
        self._token: str = ""
        self._init_event = threading.Event()

    def main(self) -> int:
        """
        主函数

        GUI 秒开，后台静默初始化，最后启动 Bot
        """
        # 1. 隐藏 Windows 原生控制台
        hide_console()

        # 2. 拉起 GUI（保证界面不白屏）
        app = QApplication(sys.argv)
        window = create_gui()
        window.show()
        app.processEvents()
        self._logger.info("🖥️ GUI 主界面已就绪")

        # 3. 初始化扔到后台线程
        init_thread = threading.Thread(target=self._background_init, daemon=True)
        init_thread.start()

        # 4. 启动 Bot 引擎（在另一个后台线程）
        from ._runner import BotRunner

        BotRunner(self._init_event, self._get_config).start()

        # 5. 主线程进入 Qt 事件循环，接管程序
        return app.exec()

    def _background_init(self) -> None:
        """
        后台初始化

        加载配置 + 版本检查
        """
        try:
            self._logger.info("⏳ 正在初始化环境...")
            from utils.init_files import init_project_files

            init_project_files()

            self._logger.info("⏳ 正在加载配置...")
            self._load_config()

            self._logger.info("⏳ 正在检查版本...")
            from utils import check_updates

            if not asyncio.run(check_updates()):
                self._logger.warning("📦 发现新版本，建议更新！")
            else:
                self._logger.info("✅ 当前已是最新版本")

        except ConfigError as e:
            self._logger.error(f"❌ 配置加载失败: {e}")
        except Exception as e:
            self._logger.error(f"❌ 初始化发生未知错误: {e}")
        finally:
            # 指示 bot 线程启动
            self._init_event.set()

    def _load_config(self) -> None:
        """加载全局配置"""
        try:
            from utils.config import (
                ensure_config,
                get_attr,
                load_config,
                set_config,
            )

            ensure_config()
            set_config(load_config())

            self._proxy = get_attr("global.proxy", str)
            self._token = get_attr("global.telegram_token", str)

        except ConfigError as e:
            self._logger.error(e)
            self._logger.info("请在 GUI 中配置")
            # TODO:GUI
            raise

    def _get_config(self) -> tuple[str, str]:
        """供 BotRunner 获取当前配置的接口"""
        return self._proxy, self._token


if __name__ == "__main__":
    Main().main()
