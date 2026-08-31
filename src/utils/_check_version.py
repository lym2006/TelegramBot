# src/utils/_check_version.py
"""
版本检查工具（内部实现）

- 读取本地与远程版本号
- 启动前自动校验版本一致性
"""

import tomllib
from typing import cast

from exceptions import NetworkError

from ._base_client import BaseClient
from ._root_dir import ROOT_DIR
from .logger import get_logger

logger = get_logger("Version")

_BASE_URL = "https://lym2006.github.io"
_REQUEST_PATH = "/TelegramBot/pyproject.toml"
_HEADER = {"User-Agent": "Python-Script"}

# ==================== 1. 内部辅助函数 ====================


def _get_local_version() -> str | None:
    """读取本地 pyproject.toml 中的版本号"""
    try:
        pyproject_path = ROOT_DIR / "pyproject.toml"
        if not pyproject_path.exists():
            return
        with open(pyproject_path, "rb") as f:
            content = tomllib.load(f)
        local_version = content["project"]["version"]
        return local_version if local_version else None
    except Exception as e:
        logger.send_error("❌ 读取本地版本失败", e)
        return


async def _get_remote_version() -> str | None:
    """通过 BaseClient 读取远程版本号"""
    try:
        text = await BaseClient.get_content(
            method="text",
            base_url=_BASE_URL,
            request_path=_REQUEST_PATH,
            headers=_HEADER,
        )
        data = tomllib.loads(cast(str, text))
        return data["project"]["version"]
    except NetworkError as e:
        logger.send_error("❌ 读取远程版本过程出现网络异常", e)
        return
    except Exception as e:
        logger.send_error("❌ 读取远程版本过程出现未知异常", e)
        return


# ==================== 2. 核心版本检查逻辑 ====================


async def check_updates() -> None:
    """检查是否为最新版本"""
    local_version = _get_local_version()
    remote_version = await _get_remote_version()

    if local_version is None:
        logger.error("❌ 无法读取本地版本号，跳过版本检查")

    if remote_version is None:
        logger.warning("🚨 远程版本获取失败，无法完成版本检查，继续启动机器人")

    if local_version == remote_version:
        logger.info(f"✅ 当前已是最新版本: {local_version}")
    else:
        logger.warning(
            "🆕 发现新版本\n"
            f"当前版本: {local_version}\n"
            f"最新版本: {remote_version}\n"
            '请点击 "立即更新" 按钮'
        )
