# src/bot/__main__.py
"""
Bot 启动主模块

- 初始化日志器和全局配置
- 检查版本
- 启动 GUI
- 启动 Bot 引擎
"""

import asyncio
import sys
import threading

from PySide6.QtWidgets import QApplication

from exceptions import (
    ConfigAttrError,
    ConfigError,
    ConfigInputError,
    ConfigMissingError,
    ConfigParseError,
    ConfigTemplateMissingError,
)
from gui import create_gui
from gui.core import gui_bridge
from utils import get_logger
from utils.config import AppConfigData, AppSchema

from ._runner import BotRunner

ERR_MAPS = {
    ConfigTemplateMissingError: "🛑 缺少配置模板，阻止启动",
    ConfigMissingError: "🚨 缺少配置文件",
    ConfigInputError: "❌ 配置写入错误",
    ConfigParseError: "❌ 配置模板解析错误",
    ConfigAttrError: "❌ 配置模板配置项不存在或类型错误\n"
    "配置项：%s\n"
    "期望类型：%s\n"
    "实际值：%s",
}


class Main:
    """主程序入口，负责初始化环境、配置组件并启动机器人"""

    def __init__(self) -> None:
        self._logger = get_logger()
        self._proxy: str = ""
        self._token: str = ""
        self._init_event = threading.Event()
        self._bot_runner: BotRunner | None = None

    def main(self) -> int:
        """
        主函数

        GUI 秒开，后台静默初始化，最后启动 Bot
        """
        # 1. 拉起 GUI
        app = QApplication(sys.argv)
        window = create_gui(schema=AppSchema(), current_config=AppConfigData())
        window.show()
        app.processEvents()
        self._logger.info("🖥️ GUI 主界面已就绪")

        # 2. 启动 Bot 引擎
        self._init_thread = threading.Thread(target=self._background_init, daemon=True)
        self._init_thread.start()

        # 3. 启动 BotRunner（内部等待 init_event 完成后自动创建 BotEngine）
        self._bot_runner = BotRunner(
            init_event=self._init_event,
            get_config_func=self._get_config,
        )
        self._bot_runner.start()


        # 4. 主线程进入 Qt 事件循环，接管程序
        return app.exec()

    def _background_init(self) -> None:
        """
        后台初始化

        文件检查 -> 配置加载 -> 版本检查
        """
        self._logger.info("⏳ 正在初始化环境...")
        from utils.init_files import init_project_files

        init_project_files()

        self._logger.info("⏳ 正在加载配置...")
        self._load_config()

        self._logger.info("⏳ 正在检查版本...")
        from utils import check_updates

        asyncio.run(check_updates())

        # 通知 BotRunner 启动引擎
        self._init_event.set()

    def _load_config(self) -> None:
        """加载全局配置"""
        try:
            from utils.config import (
                ensure_config,
                get_attr,
                get_schema,
                load_config,
                set_config,
            )

            ensure_config()
            config = load_config()
            set_config(config)

            # 注入真实数据
            gui_bridge.real_config_loaded.emit(get_schema(), config)

            self._proxy = get_attr("global.proxy", str)
            self._token = get_attr("global.telegram_token", str)

        except ConfigTemplateMissingError as e:
            self._logger.send_error(ERR_MAPS[type(e)], e)
            # TODO: 启动拦截
            sys.exit(1)  # 暂时先退出

        except ConfigError as e:
            msg = ERR_MAPS[type(e)]
            if isinstance(e, ConfigAttrError):
                msg = msg % (e.key_path, e.expected_type.__name__, e.actual_value)
            self._logger.send_error(msg, e)
            self._logger.info("🛠️ 请在 GUI 中配置")
            # TODO:GUI，这里也要写一个拦截启动，直到填好了才能改掉状态
            sys.exit(1)  # 暂时先退出

        except Exception as e:
            self._logger.send_error("❌ 初始化发生未知错误", e)

    def _get_config(self) -> tuple[str, str]:
        """供 BotRunner 获取当前配置的接口"""
        return self._proxy, self._token


if __name__ == "__main__":
    Main().main()
