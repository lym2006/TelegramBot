# src/utils/logger/_filter.py
"""
日志噪音屏蔽模块（内部实现）

负责：
- 批量将指定第三方库的日志级别设为 CRITICAL 并切断冒泡
"""

import logging

# 需要屏蔽噪音的第三方库列表
_NOISY_LIBS = (
    "aiogram",
    "aiohttp",
    "httpx",
    "selenium",
    "urllib3",
    "pydub",
    "cv2",
    "asyncio",
    "PIL",
    "PySide6",
)


def suppress_third_party_logs(lib_names: tuple[str, ...] | None = None) -> None:
    """屏蔽指定第三方库的日志输出（非 CRITICAL 级别全部静默 + 切断冒泡）"""
    targets = lib_names if lib_names is not None else _NOISY_LIBS
    for name in targets:
        lib_logger = logging.getLogger(name)
        lib_logger.setLevel(logging.CRITICAL)
        lib_logger.propagate = False
