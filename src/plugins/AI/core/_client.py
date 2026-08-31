# src/plugins/AI/core/_client.py
"""
AI 核心网络客户端（内部实现）

- 继承自 BaseClient，封装 AI 专属的鉴权 Headers
"""

import json
from collections.abc import AsyncGenerator
from typing import Any

from utils import BaseClient

from ..config import ai_config


class AIClient(BaseClient):
    """AI 客户端，自动注入鉴权 Headers 并强制禁用代理"""

    # ==================== 1. 动态生成鉴权 Headers ====================

    @classmethod
    def _headers(cls) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {ai_config.api_key}",
            "Content-Type": "application/json",
        }

    # ==================== 2. AI 请求方法 ====================

    @classmethod
    async def stream_chat(
        cls,
        msg: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        AI 流式聊天请求

        复用 BaseClient 的客户端创建 / 超时 / 错误处理，
        注入鉴权 Headers，禁用代理，
        负责 SiliconFlow SSE 协议的 delta 解析，包含 "content" 、"reasoning_content"
        """
        payload = {
            "model": ai_config.model_name,
            "messages": msg,
            "stream": True,
            "temperature": ai_config.temperature,
        }

        async for line in super().stream_post(
            base_url=ai_config.base_url,
            request_path=ai_config.request_path,
            headers=cls._headers(),
            payload=payload,
            use_proxy=False,
        ):
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    delta = data["choices"][0]["delta"]
                    yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
