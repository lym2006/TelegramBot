# src/utils/ssl.py
"""
代理网络会话工具

- 提供支持代理且自动禁用 SSL 验证的 Aiohttp 会话
- 解决 Bot 启动时 Clash 代理导致的 SSL 握手失败问题
"""

from aiogram.client.session.aiohttp import AiohttpSession


class SSLUnverifiedSession(AiohttpSession):
    """支持代理且自动禁用 SSL 验证的网络会话

    用于解决 Bot 启动时 clash 代理导致的 SSL 握手失败问题
    注意：此会话禁用了 SSL 证书验证，仅建议在开发环境或受信任的代理网络中使用
    """

    def __init__(
        self, proxy: str | None = None, verify: bool = False, **kwargs
    ) -> None:
        super().__init__(proxy=proxy, **kwargs)
        self._connector_init["ssl"] = verify
