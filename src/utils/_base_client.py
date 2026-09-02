# src/utils/_base_client.py
"""
异步 HTTP 客户端工具（内部实现）

- 异步 HTTP 客户端生命周期管理
- 通用的 GET/POST 请求封装
- SSE 流式解析
- 自动注入代理
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Literal

import httpx

from exceptions import ConnectionFailedError, HTTPStatusError, RequestTimeoutError

from .config import get_attr


class BaseClient:
    """通用 HTTP 客户端基类"""

    # ==================== 1. 内部辅助方法 ====================

    @classmethod
    @asynccontextmanager
    async def _create_client(
        cls,
        base_url: str = "",
        headers: dict[str, Any] | None = None,
        use_proxy: bool = True,
    ) -> AsyncGenerator[httpx.AsyncClient, None]:
        """创建异步客户端上下文管理器"""
        default_timeout = get_attr("global.network_timeout", float)

        timeout_config = httpx.Timeout(
            connect=10.0,
            read=default_timeout,
            write=default_timeout,
            pool=default_timeout,
        )

        proxy = get_attr("global.proxy", str) if use_proxy else None

        client = httpx.AsyncClient(
            base_url=base_url, headers=headers, timeout=timeout_config, proxy=proxy
        )
        try:
            yield client
        finally:
            await client.aclose()

    @staticmethod
    def _deal_with_exception(
        response: httpx.Response, method: Literal["POST", "GET"]
    ) -> None:
        """统一处理 HTTP 响应异常，翻译为自定义异常"""
        try:
            response.raise_for_status()
        except httpx.TimeoutException as e:
            raise RequestTimeoutError(method) from e
        except httpx.ConnectError as e:
            raise ConnectionFailedError(method) from e
        except httpx.HTTPStatusError as e:
            raise HTTPStatusError(e.response.status_code, e.response.text) from e

    # ==================== 2. 通用请求方法 ====================

    @classmethod
    async def stream_post(
        cls,
        base_url: str = "",
        request_path: str = "",
        headers: dict[str, Any] | None = None,
        payload: Any = None,
        use_proxy: bool = True,
    ) -> AsyncGenerator[str, None]:
        """通用的流式 POST 请求"""
        async with cls._create_client(
            base_url=base_url, headers=headers, use_proxy=use_proxy
        ) as client:
            async with client.stream("POST", request_path, json=payload) as response:
                cls._deal_with_exception(response, "POST")

                async for chunk in response.aiter_lines():
                    if chunk is not None:
                        yield chunk

    @classmethod
    async def get_content(
        cls,
        method: Literal["json", "text"],
        base_url: str = "",
        request_path: str = "",
        headers: dict[str, Any] | None = None,
        use_proxy: bool = True,
        max_retries: int = 3,  # 最多重试次数
        retry_delay: float = 1.0,  # 重试间隔时间（单位：秒）
    ) -> dict[str, Any] | str | None:
        """通用的 GET 请求（返回 JSON 或原始文本）"""
        for attempt in range(1, max_retries + 1):
            try:
                async with cls._create_client(
                    base_url=base_url, headers=headers, use_proxy=use_proxy
                ) as client:
                    response = await client.get(request_path)
                    cls._deal_with_exception(response, "GET")
                    match method:
                        case "json":
                            return response.json()
                        case "text":
                            return response.text

            except (ConnectionFailedError, RequestTimeoutError):
                # 对网络异常（连接失败、超时）进行重试
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * attempt)  # 递增延迟
                    continue  # 重试
                else:
                    raise  # 耗尽次数

            except HTTPStatusError:
                # HTTP 状态码错误不重试
                raise
