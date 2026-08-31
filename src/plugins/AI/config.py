# src/plugins/AI/config.py
"""
AI 插件配置模块

- 记录存放路径
- API 参数
- 运行状态
"""

from dataclasses import dataclass
from pathlib import Path

from utils import ROOT_DIR, get_attr

from .utils import build_message


@dataclass(frozen=True)
class AIConfig:
    """AI 插件配置"""

    # ==================== 1. 路径配置 ====================

    record_dir: Path = ROOT_DIR / "data/ai_records"  # 记录存放路径
    black_dir: Path = ROOT_DIR / "data/blacklists"  # 黑名单路径

    # ==================== 2. API 与模型配置 ====================

    model_name: str = get_attr("ai.model_name", str)
    api_key: str = get_attr("ai.api_key", str)
    temperature: float = get_attr("ai.temperature", float)

    # ==================== 3. 运行参数配置 ====================

    group_triggers: tuple[str, ...] = tuple(
        get_attr("chore.triggers", list[str])
    )  # 群聊中触发词
    cleanup_time: float = (
        get_attr("data.clearup", float) * 60 * 60
    )  # 不活跃用户清理时间
    waiting_time: float = (
        get_attr("data.waiting", float) * 60 * 60
    )  # 扫描不活跃用户间隔时间

    # ==================== 4. AI 对话相关 ====================

    init: tuple[dict[str, str], ...] = tuple(
        [build_message("system", get_attr("chore.personality", str))]
    )  # 初始对话
    base_url: str = "https://api.siliconflow.cn/v1"  # AI 对话接口根地址
    request_path: str = "/chat/completions"  # AI 对话接口请求路径

    # ==================== 5. 消息发送 ====================

    msg_chunk_size: int = 4000  # 单条消息最大字符数（Telegram 限制为 4096，留点余量）
    flood_threshold: int = 5  # 触发防频控休眠的总段数阈值
    think_throttle_sec: float = 1.2  # 思考过程 UI 更新节流时间（秒）
    trim_preview_len: int = 2000  # 思考预览文本的最大裁剪长度


# 实例化为全局单例
ai_config = AIConfig()
