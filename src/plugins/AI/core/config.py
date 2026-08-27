# src/plugins/AI/core/config.py
"""
AI 核心配置

负责：
- 记录存放路径
- API 参数
- 运行状态。
"""

from utils import ROOT_DIR
from utils.config import get_attr

from .utils import build_message

# ==================== 1. 路径配置 ====================
RECORD_DIR = ROOT_DIR / "data/ai_records"
BLACK_DIR = ROOT_DIR / "data/blacklists"

# ==================== 2. API 与模型配置 ====================
MODEL_NAME = get_attr("ai.model_name", str)
API_KEY = get_attr("ai.api_key", str)
TEMPERATURE = get_attr("ai.temperature", float)

# ==================== 3. 运行参数配置 ====================
GROUP_TRIGGERS = get_attr("chore.triggers", list[str])
CLEARUP_TIME = get_attr("data.clearup", float) * 60 * 60
WAITING_TIME = get_attr("data.waiting", float) * 60 * 60

# ==================== 4. 初始化状态 ====================
INIT = [build_message("system", get_attr("chore.personality", str))]
