# src/utils/plugins_register.py
"""
插件注册与加载工具

- 基于白名单的插件顺序控制
- 插件路由的动态注册与状态监控
"""

import importlib

from aiogram import Dispatcher

from exceptions import PluginsMissingError

from .logger import get_logger

logger = get_logger("Plugins")

# 插件加载白名单（严格按此顺序注册）
# 注意：欢迎与帮助类插件应置于前端，核心 AI 插件必须置于最后
_PLUGIN_ORDER = [
    "welcome",  # 系统级命令
    "help",  # 帮助命令
    # "spider",  #爬虫相关
    # "image_record",  #图像音频相关
    # "emoji",  #emoji合成
    "AI",  # AI部分
]


def register_routers(dispatcher: Dispatcher) -> None:
    """按顺序注册插件"""
    total = len(_PLUGIN_ORDER)
    logger.info(f"开始加载 {total} 个插件...")

    success_count = 0

    for index, plugin_name in enumerate(_PLUGIN_ORDER, start=1):
        pref = f"[{index}/{total}]"
        try:
            # 动态导入插件模块
            module = importlib.import_module(f"plugins.{plugin_name}")

            # 检查插件是否导出了标准的 router 对象
            router = getattr(module, "router", None)
            if router is not None:
                # 清除旧的父路由引用，允许重新附加到新 Dispatcher
                router._parent_router = None
                dispatcher.include_router(router)
                logger.info(f"{pref} 插件 {plugin_name} 注册成功")
                success_count += 1
            else:
                logger.error(
                    f"{pref} 插件 '{plugin_name}' 缺少 'router' 属性"
                    f"(请检查其 __init__.py 是否导出了 router)"
                )

        except ModuleNotFoundError as e:
            if f"plugins.{plugin_name}" in str(e):
                # 插件本身不存在
                msg = f"{pref} 插件 '{plugin_name}' 未找到（请检查目录结构）"
            else:
                # 插件内部缺少依赖
                msg = f"{pref} 插件 '{plugin_name}' 缺少依赖"

            logger.send_error(msg, e)

        except Exception as e:
            # 插件内部的其他错误
            logger.send_error(f"{pref} 插件 '{plugin_name}' 加载异常", e)

    # 输出最终的加载统计摘要
    logger.info(f"插件加载完成 | 成功: {success_count} / 总计: {len(_PLUGIN_ORDER)}")

    # 如果所有插件都加载失败，抛出异常
    if success_count == 0:
        raise PluginsMissingError() from None
