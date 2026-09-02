# src/plugins/AI/browser/_manager.py
"""
AI 浏览器生命周期管理模块

- 单例模式管理 Playwright 与 Browser 实例
- 提供安全的懒加载与优雅关闭机制
"""

import asyncio

from playwright.async_api import Browser, Playwright, async_playwright

from utils import get_logger, register_shutdown

from ._config import browser_config

logger = get_logger("Plugins.AI.Browser")


class BrowserManager:
    """全局浏览器生命周期管家"""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._lock = asyncio.Lock()  # 防止并发下启动多个浏览器

        # 注册关闭钩子
        register_shutdown(self._shutdown, "Playwright 浏览器")

    async def get_browser(self) -> Browser:
        """
        获取全局浏览器实例（懒加载 + 双重检查锁）

        如果浏览器未启动或已断开连接，则自动初始化
        """
        # 无锁，高性能
        if self._browser and self._browser.is_connected():
            return self._browser

        # 加锁，防并发
        async with self._lock:
            if self._browser and self._browser.is_connected():
                return self._browser

            logger.info("正在初始化全局 Playwright 浏览器...")
            # 1. 启动 Playwright 引擎
            self._playwright = await async_playwright().start()
            # 2. 启动 Chromium 浏览器
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=browser_config.args,
            )
            logger.info("全局浏览器初始化成功")
            return self._browser

    async def _shutdown(self) -> None:
        """优雅关闭浏览器与 Playwright 引擎"""
        async with self._lock:
            if self._browser:
                logger.info("正在关闭全局浏览器...")
                try:
                    await self._browser.close()
                except Exception as e:
                    logger.send_error("关闭浏览器错误", e)
                finally:
                    self._browser = None

            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception as e:
                    logger.warning("停止 Playwright 引擎错误", e)
                finally:
                    self._playwright = None

            logger.info("全局浏览器资源已彻底释放")


# 极其冷酷的全局单例（整个 AI 插件共享这一个管家）
browser_manager = BrowserManager()
