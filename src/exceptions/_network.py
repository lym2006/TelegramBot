# src/exceptions/_network.py
"""网络与 API 异常（内部实现）"""

from ._base import BotError


class NetworkError(BotError):
    """网络请求异常基类"""


class HTTPStatusError(NetworkError):
    """HTTP 状态码异常"""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__()


class RequestTimeoutError(NetworkError):
    """请求超时异常"""


class ConnectionFailedError(NetworkError):
    """连接失败异常"""
